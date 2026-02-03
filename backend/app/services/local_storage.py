"""
=============================================================================
BESIKTNINGSAPP BACKEND - LOCAL STORAGE SERVICE
=============================================================================
Local file system storage implementation.

Used for:
- Development environment
- Testing
- Small deployments without S3/MinIO

Directory structure:
/storage/
  ├── images/
  │   ├── YYYYMMDD/
  │   │   ├── uuid1.jpg
  │   │   ├── uuid1_thumb.jpg
  │   │   └── ...
  └── pdfs/
      ├── YYYYMMDD/
      │   ├── inspection_1_v1.pdf
      │   └── ...
"""
import os
from pathlib import Path
from typing import BinaryIO
import shutil

from app.config import Config
from app.utils.errors import StorageError


class LocalStorage:
    """Local file system storage service."""
    
    def __init__(self):
        """Initialize local storage."""
        self.base_path = Path(Config.STORAGE_PATH or '/app/storage')
        self.images_path = self.base_path / 'images'
        self.pdfs_path = self.base_path / 'pdfs'
        
        # Create directories if they don't exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure storage directories exist."""
        self.images_path.mkdir(parents=True, exist_ok=True)
        self.pdfs_path.mkdir(parents=True, exist_ok=True)
    
    # =========================================================================
    # IMAGES
    # =========================================================================
    
    def save_image(self, storage_key: str, content: bytes) -> str:
        """
        Save image to local storage.
        
        Args:
            storage_key: Storage key (e.g., "20260203/uuid.jpg")
            content: Image bytes
        
        Returns:
            Storage path (relative to base_path)
        
        Raises:
            StorageError: If save fails
        """
        try:
            # Build full path
            file_path = self.images_path / storage_key
            
            # Create parent directories
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            file_path.write_bytes(content)
            
            # Return relative path
            return f"images/{storage_key}"
            
        except Exception as e:
            raise StorageError(
                f"Failed to save image: {str(e)}",
                operation='save_image'
            )
    
    def read_image(self, storage_key: str) -> bytes:
        """
        Read image from local storage.
        
        Args:
            storage_key: Storage key
        
        Returns:
            Image bytes
        
        Raises:
            FileNotFoundError: If file not found
            StorageError: If read fails
        """
        try:
            file_path = self.images_path / storage_key
            
            if not file_path.exists():
                raise FileNotFoundError(f"Image not found: {storage_key}")
            
            return file_path.read_bytes()
            
        except FileNotFoundError:
            raise
        except Exception as e:
            raise StorageError(
                f"Failed to read image: {str(e)}",
                operation='read_image'
            )
    
    def delete_image(self, storage_key: str) -> bool:
        """
        Delete image from local storage.
        
        Args:
            storage_key: Storage key
        
        Returns:
            True if deleted, False if not found
        
        Raises:
            StorageError: If delete fails
        """
        try:
            file_path = self.images_path / storage_key
            
            if not file_path.exists():
                return False
            
            file_path.unlink()
            return True
            
        except Exception as e:
            raise StorageError(
                f"Failed to delete image: {str(e)}",
                operation='delete_image'
            )
    
    def image_exists(self, storage_key: str) -> bool:
        """
        Check if image exists.
        
        Args:
            storage_key: Storage key
        
        Returns:
            True if exists
        """
        file_path = self.images_path / storage_key
        return file_path.exists()
    
    # =========================================================================
    # PDFs
    # =========================================================================
    
    def save_pdf(self, storage_key: str, content: bytes) -> str:
        """
        Save PDF to local storage.
        
        Args:
            storage_key: Storage key (e.g., "pdfs/20260203/inspection_1_v1.pdf")
            content: PDF bytes
        
        Returns:
            Storage path (relative to base_path)
        
        Raises:
            StorageError: If save fails
        """
        try:
            # Remove 'pdfs/' prefix if present
            if storage_key.startswith('pdfs/'):
                storage_key = storage_key[5:]
            
            # Build full path
            file_path = self.pdfs_path / storage_key
            
            # Create parent directories
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            file_path.write_bytes(content)
            
            # Return relative path
            return f"pdfs/{storage_key}"
            
        except Exception as e:
            raise StorageError(
                f"Failed to save PDF: {str(e)}",
                operation='save_pdf'
            )
    
    def read_pdf(self, storage_key: str) -> bytes:
        """
        Read PDF from local storage.
        
        Args:
            storage_key: Storage key
        
        Returns:
            PDF bytes
        
        Raises:
            FileNotFoundError: If file not found
            StorageError: If read fails
        """
        try:
            # Remove 'pdfs/' prefix if present
            if storage_key.startswith('pdfs/'):
                storage_key = storage_key[5:]
            
            file_path = self.pdfs_path / storage_key
            
            if not file_path.exists():
                raise FileNotFoundError(f"PDF not found: {storage_key}")
            
            return file_path.read_bytes()
            
        except FileNotFoundError:
            raise
        except Exception as e:
            raise StorageError(
                f"Failed to read PDF: {str(e)}",
                operation='read_pdf'
            )
    
    def delete_pdf(self, storage_key: str) -> bool:
        """
        Delete PDF from local storage.
        
        Args:
            storage_key: Storage key
        
        Returns:
            True if deleted, False if not found
        
        Raises:
            StorageError: If delete fails
        """
        try:
            # Remove 'pdfs/' prefix if present
            if storage_key.startswith('pdfs/'):
                storage_key = storage_key[5:]
            
            file_path = self.pdfs_path / storage_key
            
            if not file_path.exists():
                return False
            
            file_path.unlink()
            return True
            
        except Exception as e:
            raise StorageError(
                f"Failed to delete PDF: {str(e)}",
                operation='delete_pdf'
            )
    
    def pdf_exists(self, storage_key: str) -> bool:
        """
        Check if PDF exists.
        
        Args:
            storage_key: Storage key
        
        Returns:
            True if exists
        """
        # Remove 'pdfs/' prefix if present
        if storage_key.startswith('pdfs/'):
            storage_key = storage_key[5:]
        
        file_path = self.pdfs_path / storage_key
        return file_path.exists()
    
    # =========================================================================
    # UTILITIES
    # =========================================================================
    
    def get_storage_info(self) -> dict:
        """
        Get storage usage information.
        
        Returns:
            Dictionary with storage stats
        """
        def get_dir_size(path: Path) -> int:
            """Get total size of directory."""
            total = 0
            for item in path.rglob('*'):
                if item.is_file():
                    total += item.stat().st_size
            return total
        
        images_size = get_dir_size(self.images_path) if self.images_path.exists() else 0
        pdfs_size = get_dir_size(self.pdfs_path) if self.pdfs_path.exists() else 0
        
        return {
            'backend': 'local',
            'base_path': str(self.base_path),
            'images_size_bytes': images_size,
            'images_size_mb': round(images_size / (1024 * 1024), 2),
            'pdfs_size_bytes': pdfs_size,
            'pdfs_size_mb': round(pdfs_size / (1024 * 1024), 2),
            'total_size_bytes': images_size + pdfs_size,
            'total_size_mb': round((images_size + pdfs_size) / (1024 * 1024), 2),
        }
    
    def cleanup_empty_dirs(self):
        """Remove empty directories."""
        for base in [self.images_path, self.pdfs_path]:
            for dirpath, dirnames, filenames in os.walk(base, topdown=False):
                dir_path = Path(dirpath)
                if not any(dir_path.iterdir()):
                    dir_path.rmdir()
    
    def backup(self, backup_path: str):
        """
        Create backup of storage directory.
        
        Args:
            backup_path: Path to backup directory
        
        Raises:
            StorageError: If backup fails
        """
        try:
            backup_dest = Path(backup_path)
            backup_dest.mkdir(parents=True, exist_ok=True)
            
            # Copy entire storage directory
            shutil.copytree(
                self.base_path,
                backup_dest / self.base_path.name,
                dirs_exist_ok=True
            )
            
        except Exception as e:
            raise StorageError(
                f"Failed to create backup: {str(e)}",
                operation='backup'
            )