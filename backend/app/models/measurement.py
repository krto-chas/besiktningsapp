from __future__ import annotations

"""
=============================================================================
BESIKTNINGSAPP BACKEND - MEASUREMENT MODEL
=============================================================================
Measurement model (Mätning).

Stores measurements taken during inspection (flow, pressure, temp, etc.).
"""

from sqlalchemy import Column, String, Integer, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class MeasurementType(enum.Enum):
    """Measurement type enumeration."""
    FLODE = "flode"  # Luftflöde (l/s)
    TRYCK = "tryck"  # Tryck (Pa)
    TEMP = "temp"    # Temperatur (°C)
    CO2 = "co2"      # CO2 (ppm)
    FUKT = "fukt"    # Fuktighet (%)
    LJUD = "ljud"    # Ljudnivå (dB)
    OKAND = "okand"  # Okänd/Other


class Measurement(BaseModel):
    """
    Measurement model (Mätning).
    
    Attributes:
        inspection_id: Foreign key to Inspection
        type: Type of measurement (flode, tryck, temp, etc.)
        value: Measured value (float)
        unit: Unit of measurement (e.g., "l/s", "Pa", "°C")
        apartment_number: Apartment number (optional, if specific to apartment)
        sort_key: Optional key for custom sorting/ordering
        notes: Additional notes about the measurement
    """
    
    __tablename__ = "measurements"
    
    # Foreign Key
    inspection_id = Column(
        Integer,
        ForeignKey("inspections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Inspection this measurement belongs to",
    )
    
    # Measurement Details
    type = Column(
        Enum(MeasurementType),
        nullable=False,
        index=True,
        comment="Type of measurement",
    )
    
    value = Column(
        Float,
        nullable=False,
        comment="Measured value",
    )
    
    unit = Column(
        String(20),
        nullable=False,
        comment="Unit of measurement (e.g., l/s, Pa, °C)",
    )
    
    # Optional Association
    apartment_number = Column(
        String(20),
        nullable=True,
        index=True,
        comment="Apartment number if measurement is specific to apartment",
    )
    
    # Sorting & Organization
    sort_key = Column(
        String(60),
        nullable=True,
        comment="Custom sort key for ordering measurements",
    )
    
    # Notes
    notes = Column(
        String(300),
        nullable=True,
        comment="Additional notes about the measurement",
    )
    
    # Relationships
    inspection = relationship(
        "Inspection",
        back_populates="measurements",
    )
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<Measurement(id={self.id}, type={self.type.value}, value={self.value} {self.unit})>"
