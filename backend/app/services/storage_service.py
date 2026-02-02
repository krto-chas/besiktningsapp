"""
=============================================================================
BESIKTNINGSAPP BACKEND - STORAGE SERVICE (Abstract)
=============================================================================
Abstract storage interface for file storage.

Implementations:
- LocalStorage: Local filesystem storage (development)
- S3Storage: S3/MinIO storage (production)
"""

from abc import ABC, abstractmethod
from typing import Optional, BinaryIO, Tuple
from dataclasses import dataclass


@dataclass
class StorageMetadata:
    """Metadata for stored file."""
    
    storage_key: str
    size_bytes: int
    content_type: str
    checksum: str  # SHA256
    url: Optional[str] = None


class StorageService(ABC):
    """Abstract storage service interface."""
    
    @abstractmethod
    def store(
        self,
        file: BinaryIO,
        storage_key: str,
        content_type: str,
        metadata: Optional[dict] = None
    ) -> StorageMetadata:
        """
        Store file.
        
        Args:
            file: File-like object to store
            storage_key: Unique storage key/path
            content_type: MIME type
            metadata: Optional metadata dict
            
        Returns:
            StorageMetadata with file information
        """
        pass
    
    @abstractmethod
    def retrieve(self, storage_key: str) -> Tuple[BinaryIO, StorageMetadata]:
        """
        Retrieve file.
        
        Args:
            storage_key: Storage key
            
        Returns:
            Tuple of (file-like object, metadata)
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        pass
    
    @abstractmethod
    def delete(self, storage_key: str) -> bool:
        """
        Delete file.
        
        Args:
            storage_key: Storage key
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    def exists(self, storage_key: str) -> bool:
        """
        Check if file exists.
        
        Args:
            storage_key: Storage key
            
        Returns:
            True if exists, False otherwise
        """
        pass
    
    @abstractmethod
    def get_url(
        self,
        storage_key: str,
        expires_in: Optional[int] = None
    ) -> str:
        """
        Get URL for accessing file.
        
        Args:
            storage_key: Storage key
            expires_in: Optional expiration time in seconds (for presigned URLs)
            
        Returns:
            URL string
        """
        pass
    
    @abstractmethod
    def generate_presigned_upload_url(
        self,
        storage_key: str,
        content_type: str,
        expires_in: int = 3600
    ) -> dict:
        """
        Generate presigned URL for direct upload.
        
        Args:
            storage_key: Storage key for the file
            content_type: MIME type
            expires_in: URL expiration time in seconds
            
        Returns:
            Dict with 'upload_url', 'storage_key', 'expires_at', etc.
        """
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if storage is accessible.
        
        Returns:
            True if healthy, False otherwise
        """
        pass
    
    def generate_storage_key(
        self,
        prefix: str,
        filename: str,
        user_id: Optional[int] = None
    ) -> str:
        """
        Generate storage key with organized structure.
        
        Args:
            prefix: Prefix (e.g., 'images', 'pdfs')
            filename: Original filename
            user_id: Optional user ID
            
        Returns:
            Storage key string (e.g., 'images/2026/01/user_1/filename.jpg')
        """
        from datetime import datetime
        import os
        from werkzeug.utils import secure_filename
        
        # Sanitize filename
        safe_filename = secure_filename(filename)
        
        # Build path components
        year = datetime.utcnow().strftime("%Y")
        month = datetime.utcnow().strftime("%m")
        
        parts = [prefix, year, month]
        
        if user_id:
            parts.append(f"user_{user_id}")
        
        parts.append(safe_filename)
        
        return "/".join(parts)
    
    def calculate_checksum(self, file: BinaryIO) -> str:
        """
        Calculate SHA256 checksum of file.
        
        Args:
            file: File-like object
            
        Returns:
            SHA256 checksum as hex string
        """
        import hashlib
        
        sha256 = hashlib.sha256()
        
        # Save current position
        current_pos = file.tell()
        file.seek(0)
        
        # Read and hash
        while chunk := file.read(8192):
            sha256.update(chunk)
        
        # Restore position
        file.seek(current_pos)
        
        return f"sha256:{sha256.hexdigest()}"
