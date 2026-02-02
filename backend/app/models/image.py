"""
=============================================================================
BESIKTNINGSAPP BACKEND - IMAGE MODEL
=============================================================================
Image model (Bildmetadata).

Stores metadata about images uploaded for defects.
Actual image files are stored in storage service (local or S3).
"""
from __future__ import annotations


from sqlalchemy import Column, String, Integer, BigInteger, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Image(BaseModel):
    """
    Image metadata model.
    
    Attributes:
        defect_id: Foreign key to Defect
        filename: Original filename (sanitized)
        storage_key: Key/path in storage service
        content_type: MIME type (e.g., image/jpeg)
        size_bytes: File size in bytes
        checksum: SHA256 checksum for integrity verification
        width: Image width in pixels (optional)
        height: Image height in pixels (optional)
    """
    
    __tablename__ = "images"
    
    # Foreign Key
    defect_id = Column(
        Integer,
        ForeignKey("defects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Defect this image belongs to",
    )
    
    # File Information
    filename = Column(
        String(255),
        nullable=False,
        comment="Sanitized filename",
    )
    
    storage_key = Column(
        String(500),
        nullable=False,
        unique=True,
        index=True,
        comment="Key/path in storage service (local or S3)",
    )
    
    content_type = Column(
        String(100),
        nullable=False,
        comment="MIME type (e.g., image/jpeg, image/png)",
    )
    
    size_bytes = Column(
        BigInteger,
        nullable=False,
        comment="File size in bytes",
    )
    
    checksum = Column(
        String(64),
        nullable=False,
        comment="SHA256 checksum for integrity",
    )
    
    # Image Dimensions (optional)
    width = Column(
        Integer,
        nullable=True,
        comment="Image width in pixels",
    )
    
    height = Column(
        Integer,
        nullable=True,
        comment="Image height in pixels",
    )
    
    # Relationships
    defect = relationship(
        "Defect",
        back_populates="images",
    )
    
    def get_url(self, storage_service) -> str:
        """
        Get URL for accessing the image.
        
        Args:
            storage_service: Storage service instance
            
        Returns:
            URL to access the image
        """
        return storage_service.get_url(self.storage_key)
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<Image(id={self.id}, filename={self.filename}, size={self.size_bytes})>"
