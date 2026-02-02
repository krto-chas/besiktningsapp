"""
=============================================================================
BESIKTNINGSAPP BACKEND - LOCAL STORAGE
=============================================================================
Local filesystem storage implementation (for development).
"""

import os
import shutil
from typing import Optional, BinaryIO, Tuple
from pathlib import Path

from flask import current_app

from app.services.storage_service import StorageService, StorageMetadata


class LocalStorage(StorageService):
    """Local filesystem storage implementation."""
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize local storage.
        
        Args:
            base_path: Base directory path (defaults to config)
        """
        self.base_path = base_path or current_app.config.get(
            "LOCAL_STORAGE_PATH",
            "/app/storage"
        )
        
        # Ensure base path exists
        Path(self.base_path).mkdir(parents=True, exist_ok=True)
    
    def store(
        self,
        file: BinaryIO,
        storage_key: str,
        content_type: str,
        metadata: Optional[dict] = None
    ) -> StorageMetadata:
        """Store file to local filesystem."""
        # Build full path
        full_path = os.path.join(self.base_path, storage_key)
        
        # Create directory if needed
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Calculate checksum before writing
        checksum = self.calculate_checksum(file)
        
        # Write file
        file.seek(0)
        with open(full_path, 'wb') as f:
            shutil.copyfileobj(file, f)
        
        # Get file size
        size_bytes = os.path.getsize(full_path)
        
        return StorageMetadata(
            storage_key=storage_key,
            size_bytes=size_bytes,
            content_type=content_type,
            checksum=checksum,
            url=self.get_url(storage_key)
        )
    
    def retrieve(self, storage_key: str) -> Tuple[BinaryIO, StorageMetadata]:
        """Retrieve file from local filesystem."""
        full_path = os.path.join(self.base_path, storage_key)
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {storage_key}")
        
        file = open(full_path, 'rb')
        size_bytes = os.path.getsize(full_path)
        
        # Calculate checksum
        checksum = self.calculate_checksum(file)
        
        metadata = StorageMetadata(
            storage_key=storage_key,
            size_bytes=size_bytes,
            content_type="application/octet-stream",  # Could be stored separately
            checksum=checksum,
            url=self.get_url(storage_key)
        )
        
        return file, metadata
    
    def delete(self, storage_key: str) -> bool:
        """Delete file from local filesystem."""
        full_path = os.path.join(self.base_path, storage_key)
        
        if not os.path.exists(full_path):
            return False
        
        os.remove(full_path)
        return True
    
    def exists(self, storage_key: str) -> bool:
        """Check if file exists."""
        full_path = os.path.join(self.base_path, storage_key)
        return os.path.exists(full_path)
    
    def get_url(self, storage_key: str, expires_in: Optional[int] = None) -> str:
        """Get URL for file (local path or served URL)."""
        # In production, this would be served via web server
        # For now, return a placeholder URL
        return f"/files/{storage_key}"
    
    def generate_presigned_upload_url(
        self,
        storage_key: str,
        content_type: str,
        expires_in: int = 3600
    ) -> dict:
        """Generate presigned upload URL (not applicable for local storage)."""
        # Local storage doesn't support presigned URLs
        # Return info for direct upload instead
        return {
            "upload_url": None,
            "storage_key": storage_key,
            "method": "POST",
            "message": "Use direct upload for local storage"
        }
    
    def health_check(self) -> bool:
        """Check if storage is accessible."""
        try:
            # Check if base path exists and is writable
            return os.path.exists(self.base_path) and os.access(self.base_path, os.W_OK)
        except Exception:
            return False
