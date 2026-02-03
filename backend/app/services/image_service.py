"""
=============================================================================
BESIKTNINGSAPP BACKEND - IMAGE SERVICE
=============================================================================
Business logic for image upload, storage, and validation.

Includes:
- Image upload with validation (file type, size, dimensions)
- Storage abstraction (local or S3/MinIO)
- Thumbnail generation
- Metadata tracking
- Presigned URL generation for direct uploads
- Batch operations
"""
from typing import List, Optional, Tuple, BinaryIO
from datetime import datetime, timedelta
import os
import hashlib
import uuid
from io import BytesIO
from PIL import Image as PILImage

from app.models import Image
from app.extensions import db
from app.utils.errors import ValidationError, NotFoundError
from app.config import Config


class ImageService:
    """Business logic for image handling."""

    # Allowed image formats
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
    ALLOWED_MIME_TYPES = {'image/jpeg', 'image/png', 'image/webp'}

    # Size limits
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    MAX_DIMENSION = 4096  # Max width or height
    THUMBNAIL_SIZE = (300, 300)  # Thumbnail dimensions

    # =========================================================================
    # UPLOAD & STORAGE
    # =========================================================================

    @staticmethod
    def upload_image(
        file: BinaryIO,
        filename: str,
        user_id: int,
        client_id: Optional[str] = None
    ) -> Image:
        """
        Upload and store image.

        Args:
            file: File-like object (from Flask request.files)
            filename: Original filename
            user_id: Uploading user ID
            client_id: Optional client UUID for sync

        Returns:
            Created Image instance

        Raises:
            ValidationError: If validation fails
        """
        # Validate file
        ImageService._validate_file(file, filename)

        # Read file content
        file.seek(0)
        file_content = file.read()

        # Validate image with PIL
        image_data = ImageService._validate_image_content(file_content)

        # Generate unique storage key
        storage_key = ImageService._generate_storage_key(filename)

        # Calculate checksum
        checksum = hashlib.sha256(file_content).hexdigest()

        # Check for duplicate (same checksum)
        existing = Image.query.filter_by(
            checksum=checksum,
            deleted_at=None
        ).first()

        if existing:
            # Return existing image instead of uploading duplicate
            return existing

        # Get storage service
        storage = ImageService._get_storage()

        # Upload to storage
        storage_path = storage.save_image(storage_key, file_content)

        # Generate thumbnail
        thumbnail_key = ImageService._generate_storage_key(filename, suffix='_thumb')
        thumbnail_content = ImageService._generate_thumbnail(file_content)
        thumbnail_path = storage.save_image(thumbnail_key, thumbnail_content)

        # Create database record
        image_obj = Image(
            filename=filename,
            storage_key=storage_key,
            storage_path=storage_path,
            thumbnail_key=thumbnail_key,
            thumbnail_path=thumbnail_path,
            mime_type=image_data['mime_type'],
            file_size=len(file_content),
            width=image_data['width'],
            height=image_data['height'],
            checksum=checksum,
            uploaded_by_id=user_id,
            client_id=client_id,
        )

        db.session.add(image_obj)
        db.session.commit()
        db.session.refresh(image_obj)

        return image_obj

    @staticmethod
    def generate_presigned_upload(
        filename: str,
        user_id: int,
        expires_in: int = 3600
    ) -> dict:
        """
        Generate presigned URL for direct upload to storage.

        Args:
            filename: Filename to upload
            user_id: Uploading user ID
            expires_in: URL expiry in seconds (default 1 hour)

        Returns:
            Dictionary with upload URL and metadata

        Raises:
            ValidationError: If filename invalid
        """
        # Validate filename extension
        if not ImageService._is_allowed_filename(filename):
            raise ValidationError(
                f"Invalid file type. Allowed types: {', '.join(ImageService.ALLOWED_EXTENSIONS)}"
            )

        # Generate storage key
        storage_key = ImageService._generate_storage_key(filename)

        # Get storage service
        storage = ImageService._get_storage()

        # Generate presigned URL (only works with S3/MinIO)
        if hasattr(storage, 'generate_presigned_upload'):
            presigned_data = storage.generate_presigned_upload(
                storage_key,
                expires_in=expires_in
            )

            # Create pending image record
            image_obj = Image(
                filename=filename,
                storage_key=storage_key,
                storage_path=None,  # Will be set when upload completes
                mime_type=ImageService._guess_mime_type(filename),
                uploaded_by_id=user_id,
                upload_status='pending',
            )

            db.session.add(image_obj)
            db.session.commit()

            return {
                'image_id': image_obj.id,
                'upload_url': presigned_data['url'],
                'fields': presigned_data.get('fields', {}),
                'storage_key': storage_key,
                'expires_at': (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat(),
            }
        else:
            raise ValidationError("Presigned uploads not supported with local storage")

    @staticmethod
    def complete_upload(
        image_id: int,
        file_size: int,
        width: int,
        height: int,
        checksum: str
    ) -> Image:
        """
        Mark image upload as complete (for presigned uploads).

        Args:
            image_id: Image ID
            file_size: File size in bytes
            width: Image width
            height: Image height
            checksum: SHA256 checksum

        Returns:
            Updated Image instance

        Raises:
            NotFoundError: If image not found
            ValidationError: If image already completed
        """
        image_obj = Image.query.filter_by(id=image_id).first()

        if not image_obj:
            raise NotFoundError(f"Image with id {image_id} not found")

        if image_obj.upload_status == 'completed':
            raise ValidationError("Image upload already completed")

        # Update image metadata
        image_obj.file_size = file_size
        image_obj.width = width
        image_obj.height = height
        image_obj.checksum = checksum
        image_obj.upload_status = 'completed'
        image_obj.storage_path = f"images/{image_obj.storage_key}"

        db.session.commit()
        db.session.refresh(image_obj)

        return image_obj

    # =========================================================================
    # READ
    # =========================================================================

    @staticmethod
    def get_image(image_id: int) -> Image:
        """
        Get image by ID.

        Args:
            image_id: Image ID

        Returns:
            Image instance

        Raises:
            NotFoundError: If image not found
        """
        image_obj = Image.query.filter_by(
            id=image_id,
            deleted_at=None
        ).first()

        if not image_obj:
            raise NotFoundError(f"Image with id {image_id} not found")

        return image_obj

    @staticmethod
    def get_by_client_id(client_id: str) -> Optional[Image]:
        """
        Get image by client_id.

        Args:
            client_id: Client UUID

        Returns:
            Image instance or None
        """
        return Image.query.filter_by(
            client_id=client_id,
            deleted_at=None
        ).first()

    @staticmethod
    def get_images_by_ids(image_ids: List[int]) -> List[Image]:
        """
        Get multiple images by IDs.

        Args:
            image_ids: List of image IDs

        Returns:
            List of Image instances
        """
        return Image.query.filter(
            Image.id.in_(image_ids),
            Image.deleted_at.is_(None)
        ).all()

    @staticmethod
    def get_user_images(
        user_id: int,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Image], int]:
        """
        Get images uploaded by user.

        Args:
            user_id: User ID
            limit: Maximum results
            offset: Number to skip

        Returns:
            Tuple of (images list, total count)
        """
        query = Image.query.filter_by(
            uploaded_by_id=user_id,
            deleted_at=None
        )

        total = query.count()
        images = query.order_by(
            Image.created_at.desc()
        ).limit(limit).offset(offset).all()

        return images, total

    # =========================================================================
    # DOWNLOAD
    # =========================================================================

    @staticmethod
    def get_image_url(image_id: int, thumbnail: bool = False) -> str:
        """
        Get URL to download image.

        Args:
            image_id: Image ID
            thumbnail: If True, get thumbnail URL

        Returns:
            Download URL

        Raises:
            NotFoundError: If image not found
        """
        image_obj = ImageService.get_image(image_id)

        storage = ImageService._get_storage()
        key = image_obj.thumbnail_key if thumbnail else image_obj.storage_key

        if hasattr(storage, 'generate_presigned_url'):
            # S3/MinIO - generate presigned download URL
            return storage.generate_presigned_url(key, expires_in=3600)
        else:
            # Local storage - return API endpoint
            thumb_param = '?thumbnail=true' if thumbnail else ''
            return f"/api/v1/images/{image_id}/download{thumb_param}"

    @staticmethod
    def get_image_content(image_id: int, thumbnail: bool = False) -> Tuple[bytes, str]:
        """
        Get image file content.

        Args:
            image_id: Image ID
            thumbnail: If True, get thumbnail

        Returns:
            Tuple of (file_content, mime_type)

        Raises:
            NotFoundError: If image not found or file missing
        """
        image_obj = ImageService.get_image(image_id)

        storage = ImageService._get_storage()
        key = image_obj.thumbnail_key if thumbnail else image_obj.storage_key

        try:
            content = storage.read_image(key)
            return content, image_obj.mime_type
        except FileNotFoundError:
            raise NotFoundError(f"Image file not found in storage: {key}")

    # =========================================================================
    # DELETE
    # =========================================================================

    @staticmethod
    def delete_image(image_id: int, delete_from_storage: bool = True) -> bool:
        """
        Soft delete image.

        Args:
            image_id: Image ID
            delete_from_storage: If True, also delete from storage

        Returns:
            True if deleted, False if already deleted

        Raises:
            NotFoundError: If image not found
        """
        image_obj = Image.query.filter_by(id=image_id).first()

        if not image_obj:
            raise NotFoundError(f"Image with id {image_id} not found")

        if image_obj.deleted_at:
            return False

        # Soft delete in database
        image_obj.deleted_at = datetime.utcnow()
        db.session.commit()

        # Optionally delete from storage
        if delete_from_storage:
            storage = ImageService._get_storage()
            try:
                storage.delete_image(image_obj.storage_key)
                if image_obj.thumbnail_key:
                    storage.delete_image(image_obj.thumbnail_key)
            except Exception as e:
                # Log error but don't fail the operation
                print(f"Error deleting image from storage: {e}")

        return True

    # =========================================================================
    # VALIDATION
    # =========================================================================

    @staticmethod
    def _validate_file(file: BinaryIO, filename: str) -> None:
        """
        Validate uploaded file.

        Args:
            file: File object
            filename: Filename

        Raises:
            ValidationError: If validation fails
        """
        # Check filename extension
        if not ImageService._is_allowed_filename(filename):
            raise ValidationError(
                f"Invalid file type. Allowed types: {', '.join(ImageService.ALLOWED_EXTENSIONS)}"
            )

        # Check file size
        file.seek(0, 2)  # Seek to end
        size = file.tell()
        file.seek(0)  # Reset

        if size == 0:
            raise ValidationError("File is empty")

        if size > ImageService.MAX_FILE_SIZE:
            max_mb = ImageService.MAX_FILE_SIZE / (1024 * 1024)
            raise ValidationError(f"File too large. Maximum size: {max_mb}MB")

    @staticmethod
    def _validate_image_content(content: bytes) -> dict:
        """
        Validate image content with PIL.

        Args:
            content: Image bytes

        Returns:
            Dictionary with image metadata

        Raises:
            ValidationError: If image invalid
        """
        try:
            img = PILImage.open(BytesIO(content))
            img.verify()  # Verify it's a valid image

            # Re-open for metadata (verify() closes the image)
            img = PILImage.open(BytesIO(content))

            width, height = img.size
            mime_type = PILImage.MIME.get(img.format, 'image/jpeg')

            # Check MIME type
            if mime_type not in ImageService.ALLOWED_MIME_TYPES:
                raise ValidationError(
                    f"Invalid image format. Allowed: {', '.join(ImageService.ALLOWED_MIME_TYPES)}"
                )

            # Check dimensions
            if width > ImageService.MAX_DIMENSION or height > ImageService.MAX_DIMENSION:
                raise ValidationError(
                    f"Image dimensions too large. Maximum: {ImageService.MAX_DIMENSION}px"
                )

            return {
                'width': width,
                'height': height,
                'format': img.format,
                'mime_type': mime_type,
            }

        except PILImage.UnidentifiedImageError:
            raise ValidationError("Invalid image file")
        except Exception as e:
            raise ValidationError(f"Error processing image: {str(e)}")

    @staticmethod
    def _is_allowed_filename(filename: str) -> bool:
        """Check if filename has allowed extension."""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ImageService.ALLOWED_EXTENSIONS

    @staticmethod
    def _guess_mime_type(filename: str) -> str:
        """Guess MIME type from filename."""
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        mime_map = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'webp': 'image/webp',
        }
        return mime_map.get(ext, 'image/jpeg')

    # =========================================================================
    # HELPERS
    # =========================================================================

    @staticmethod
    def _generate_storage_key(filename: str, suffix: str = '') -> str:
        """
        Generate unique storage key.

        Args:
            filename: Original filename
            suffix: Optional suffix (e.g., '_thumb')

        Returns:
            Unique storage key
        """
        ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'jpg'
        unique_id = uuid.uuid4().hex
        timestamp = datetime.utcnow().strftime('%Y%m%d')
        return f"{timestamp}/{unique_id}{suffix}.{ext}"

    @staticmethod
    def _generate_thumbnail(content: bytes) -> bytes:
        """
        Generate thumbnail from image.

        Args:
            content: Original image bytes

        Returns:
            Thumbnail bytes (JPEG)
        """
        img = PILImage.open(BytesIO(content))

        # Convert to RGB if necessary (for PNG with transparency)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = PILImage.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background

        # Generate thumbnail
        img.thumbnail(ImageService.THUMBNAIL_SIZE, PILImage.Resampling.LANCZOS)

        # Save to bytes
        output = BytesIO()
        img.save(output, format='JPEG', quality=85, optimize=True)
        return output.getvalue()

    @staticmethod
    def _get_storage():
        """
        Get storage service instance.

        Returns:
            Storage service (LocalStorage or S3Storage)
        """
        storage_backend = Config.STORAGE_BACKEND

        if storage_backend == 's3':
            from app.services.s3_storage import S3Storage
            return S3Storage()
        else:
            from app.services.local_storage import LocalStorage
            return LocalStorage()

    # =========================================================================
    # STATISTICS
    # =========================================================================

    @staticmethod
    def get_statistics(user_id: Optional[int] = None) -> dict:
        """
        Get image statistics.

        Args:
            user_id: Optional filter by user

        Returns:
            Dictionary with statistics
        """
        query = Image.query.filter_by(deleted_at=None)

        if user_id:
            query = query.filter_by(uploaded_by_id=user_id)

        total = query.count()
        total_size = db.session.query(
            db.func.sum(Image.file_size)
        ).filter_by(deleted_at=None)

        if user_id:
            total_size = total_size.filter_by(uploaded_by_id=user_id)

        total_size = total_size.scalar() or 0

        return {
            'total_images': total,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
        }