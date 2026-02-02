"""
=============================================================================
BESIKTNINGSAPP BACKEND - DEFECT MODEL
=============================================================================
Defect model (Felrapport).

Represents a defect/issue found during inspection.
"""
from __future__ import annotations


from sqlalchemy import Column, String, Integer, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class DefectSeverity(enum.Enum):
    """Defect severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Defect(BaseModel):
    """
    Defect model (Felrapport).
    
    Attributes:
        apartment_id: Foreign key to Apartment
        room_index: Index of room within apartment (0-based)
        code: Defect code (e.g., "VF01", optional)
        title: Short title/summary (optional, can be auto-filled from code)
        description: Detailed description of the defect (required)
        remedy: Recommended remedy/action (optional)
        severity: Severity level (low, medium, high)
    """
    
    __tablename__ = "defects"
    
    # Foreign Key
    apartment_id = Column(
        Integer,
        ForeignKey("apartments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Apartment where defect was found",
    )
    
    # Room Reference
    room_index = Column(
        Integer,
        nullable=False,
        comment="Room index within apartment (0-based)",
    )
    
    # Defect Details
    code = Column(
        String(30),
        nullable=True,
        comment="Standard defect code (e.g., VF01)",
    )
    
    title = Column(
        String(120),
        nullable=True,
        comment="Short title/summary",
    )
    
    description = Column(
        Text,
        nullable=False,
        comment="Detailed description of the defect",
    )
    
    remedy = Column(
        Text,
        nullable=True,
        comment="Recommended remedy/action",
    )
    
    severity = Column(
        Enum(DefectSeverity),
        nullable=False,
        default=DefectSeverity.MEDIUM,
        comment="Severity: low, medium, high",
    )
    
    # Relationships
    apartment = relationship(
        "Apartment",
        back_populates="defects",
    )
    
    images = relationship(
        "Image",
        back_populates="defect",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="Image.created_at.asc()",
    )
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<Defect(id={self.id}, code={self.code}, severity={self.severity.value})>"
