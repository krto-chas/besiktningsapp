"""
=============================================================================
BESIKTNINGSAPP BACKEND - INSPECTION MODEL
=============================================================================
Inspection model (Besiktning).

Represents a single inspection event at a property.
"""
from __future__ import annotations


from sqlalchemy import Column, String, Integer, Date, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class InspectionStatus(enum.Enum):
    """Inspection status enumeration."""
    DRAFT = "draft"
    FINAL = "final"
    ARCHIVED = "archived"


class Inspection(BaseModel):
    """
    Inspection model (Besiktning).
    
    Attributes:
        property_id: Foreign key to Property
        inspector_id: Foreign key to User (besiktningsman)
        date: Inspection date
        active_time_seconds: Time spent actively inspecting (timer)
        status: Status (draft, final, archived)
        notes: General notes about the inspection
    """
    
    __tablename__ = "inspections"
    
    # Foreign Keys
    property_id = Column(
        Integer,
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Property being inspected",
    )
    
    inspector_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Inspector performing the inspection",
    )
    
    # Inspection Details
    date = Column(
        Date,
        nullable=False,
        index=True,
        comment="Inspection date",
    )
    
    active_time_seconds = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Active inspection time in seconds (from timer)",
    )
    
    status = Column(
        Enum(InspectionStatus),
        nullable=False,
        default=InspectionStatus.DRAFT,
        index=True,
        comment="Inspection status: draft, final, archived",
    )
    
    # Notes
    notes = Column(
        String(2000),
        nullable=True,
        comment="General notes about the inspection",
    )
    
    # Relationships
    property = relationship(
        "Property",
        back_populates="inspections",
    )
    
    inspector = relationship(
        "User",
        back_populates="inspections",
    )
    
    apartments = relationship(
        "Apartment",
        back_populates="inspection",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    
    measurements = relationship(
        "Measurement",
        back_populates="inspection",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    
    pdf_versions = relationship(
        "PDFVersion",
        back_populates="inspection",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="PDFVersion.version_number.desc()",
    )
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<Inspection(id={self.id}, property_id={self.property_id}, date={self.date})>"
