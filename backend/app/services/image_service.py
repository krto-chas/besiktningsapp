"""
=============================================================================
BESIKTNINGSAPP BACKEND - IMAGE SERVICE
=============================================================================
Image handling and validation service.
"""

from typing import Optional, BinaryIO
from werkzeug.datastructures import FileStorage
from PIL import Image as PILImage
import io

from flask import current_app

from app.models import Image, Defect
from app.extensions import db


class ImageService:
    """Image handling and validation service."""
    
    # Allowed image types
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
    ALLOWED_MIMETYPES = {'image/jpeg', 'image/png', 'image/webp'}
    
    # Max sizes
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_DIMENSION = 4096  # 4096x4096 pixels
    
    @staticmethod
    def validate_image(file: FileStorage) -> tuple[bool, Optional[str]]:
        """
        Validate uploaded image.
        
        Args:
            file: Uploaded file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check if file exists
        if not file or not file.filename:
            return False, "No file provided"
        
        # Check extension
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if ext not in ImageService.ALLOWED_EXTENSIONS:
            return False, f"Invalid file type. Allowed: {', '.join(ImageService.ALLOWED_EXTENSIONS)}"
        
        # Check MIME type
        if file.content_type not in ImageService.ALLOWED_MIMETYPES:
            return False, f"Invalid MIME type: {file.content_type}"
        
        # Check file size
        file.seek(0, 2)  # Seek to end
        size = file.tell()
        file.seek(0)  # Reset
        
        if size > ImageService.MAX_IMAGE_SIZE:
            return False, f"File too large. Max: {ImageService.MAX_IMAGE_SIZE / (1024*1024)}MB"
        
        # Validate image can be opened
        try:
            img = PILImage.open(file.stream)
            
            # Check dimensions
            width, height = img.size
            if width > ImageService.MAX_DIMENSION or height > ImageService.MAX_DIMENSION:
                return False, f"Image dimensions too large. Max: {ImageService.MAX_DIMENSION}x{ImageService.MAX_DIMENSION}"
            
            file.stream.seek(0)  # Reset for later use
            return True, None
            
        except Exception as e:
            return False, f"Invalid image file: {str(e)}"
    
    @staticmethod
    def process_image(
        file: FileStorage,
        defect_id: int,
        storage_service
    ) -> Image:
        """
        Process and store image.
        
        Args:
            file: Uploaded file
            defect_id: Defect ID
            storage_service: Storage service instance
            
        Returns:
            Image model instance
        """
        # Validate
        is_valid, error = ImageService.validate_image(file)
        if not is_valid:
            raise ValueError(error)
        
        # Generate storage key
        storage_key = storage_service.generate_storage_key(
            prefix="images",
            filename=file.filename,
            user_id=None  # Could add user_id from context
        )
        
        # Store file
        metadata = storage_service.store(
            file=file.stream,
            storage_key=storage_key,
            content_type=file.content_type
        )
        
        # Get image dimensions
        file.stream.seek(0)
        img = PILImage.open(file.stream)
        width, height = img.size
        
        # Create image record
        image = Image(
            defect_id=defect_id,
            filename=file.filename,
            storage_key=storage_key,
            content_type=file.content_type,
            size_bytes=metadata.size_bytes,
            checksum=metadata.checksum,
            width=width,
            height=height
        )
        
        db.session.add(image)
        db.session.commit()
        
        return image
    
    @staticmethod
    def resize_image(
        image_data: BinaryIO,
        max_width: int = 1920,
        max_height: int = 1080,
        quality: int = 85
    ) -> io.BytesIO:
        """
        Resize image maintaining aspect ratio.
        
        Args:
            image_data: Image data
            max_width: Maximum width
            max_height: Maximum height
            quality: JPEG quality (1-100)
            
        Returns:
            Resized image as BytesIO
        """
        img = PILImage.open(image_data)
        
        # Calculate new size maintaining aspect ratio
        ratio = min(max_width / img.width, max_height / img.height)
        if ratio < 1:
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, PILImage.Resampling.LANCZOS)
        
        # Save to buffer
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)
        
        return output
