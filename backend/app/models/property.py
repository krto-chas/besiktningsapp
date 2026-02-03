from __future__ import annotations

"""
=============================================================================
BESIKTNINGSAPP BACKEND - PROPERTY MODEL
=============================================================================
Property model (Fastighet).

Represents a property/building where inspections are performed.
"""

from sqlalchemy import Column, String, Integer, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Property(BaseModel):
    """
    Property model (Fastighet).
    
    Attributes:
        property_type: Type of property (flerbostadshus, villa, etc.)
        designation: Fastighetsbeteckning
        owner: Property owner name
        address: Street address
        postal_code: Postal code
        city: City
        num_apartments: Number of apartments/lägenhetsr
        num_premises: Number of commercial premises/lokaler
        notes: Additional notes about the property
    """
    
    __tablename__ = "properties"
    
    # Property Type
    property_type = Column(
        String(100),
        nullable=False,
        comment="Type: flerbostadshus, villa, kontor, etc.",
    )
    
    # Identification
    designation = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Fastighetsbeteckning (unique identifier)",
    )
    
    owner = Column(
        String(255),
        nullable=True,
        comment="Property owner name or organization",
    )
    
    # Address
    address = Column(
        String(500),
        nullable=False,
        comment="Street address",
    )
    
    postal_code = Column(
        String(20),
        nullable=True,
        comment="Postal code",
    )
    
    city = Column(
        String(100),
        nullable=True,
        comment="City",
    )
    
    # Property Details
    num_apartments = Column(
        Integer,
        nullable=True,
        comment="Number of apartments/lägenheter",
    )
    
    num_premises = Column(
        Integer,
        nullable=True,
        comment="Number of commercial premises/lokaler",
    )
    
    # Additional Information
    notes = Column(
        Text,
        nullable=True,
        comment="Additional notes about the property",
    )
    
    # Relationships
    inspections = relationship(
        "Inspection",
        back_populates="property",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<Property(id={self.id}, designation={self.designation})>"
