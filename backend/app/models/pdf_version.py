from __future__ import annotations

"""
=============================================================================
BESIKTNINGSAPP BACKEND - PDF VERSION MODEL
=============================================================================
PDF Version model for tracking all generated PDF versions.

Each PDF generation creates a NEW immutable version.
Old versions are NEVER deleted automatically.
"""

from sqlalchemy import Column, String, Integer, BigInteger, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class PDFStatus(enum.Enum):
    """PDF status enumeration."""
    DRAFT = "draft"
    FINAL = "final"


class PDFVersion(BaseModel):
    """
    PDF Version model.
    
    Attributes:
        inspection_id: Foreign key to Inspection
        version_number: Sequential version number (1, 2, 3, ...)
        status: Status (draft or final)
        storage_key: Key/path in storage service
        filename: Generated filename
        size_bytes: File size in bytes
        checksum: SHA256 checksum for integrity
        created_by_user_id: User who generated this version
    """
    
    __tablename__ = "pdf_versions"
    
    # Foreign Keys
    inspection_id = Column(
        Integer,
        ForeignKey("inspections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Inspection this PDF belongs to",
    )
    
    created_by_user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who created this PDF version",
    )
    
    # Version Information
    version_number = Column(
        Integer,
        nullable=False,
        comment="Sequential version number (1, 2, 3, ...)",
    )
    
    status = Column(
        Enum(PDFStatus),
        nullable=False,
        default=PDFStatus.DRAFT,
        comment="Status: draft or final",
    )
    
    # File Information
    storage_key = Column(
        String(500),
        nullable=False,
        unique=True,
        index=True,
        comment="Key/path in storage service",
    )
    
    filename = Column(
        String(255),
        nullable=False,
        comment="Generated filename",
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
    
    # Relationships
    inspection = relationship(
        "Inspection",
        back_populates="pdf_versions",
    )
    
    created_by = relationship(
        "User",
        foreign_keys=[created_by_user_id],
    )
    
    def get_url(self, storage_service) -> str:
        """
        Get URL for accessing the PDF.
        
        Args:
            storage_service: Storage service instance
            
        Returns:
            URL to access the PDF
        """
        return storage_service.get_url(self.storage_key)
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<PDFVersion(id={self.id}, inspection_id={self.inspection_id}, version={self.version_number}, status={self.status.value})>"
