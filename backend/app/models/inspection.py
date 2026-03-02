from __future__ import annotations

"""
=============================================================================
BESIKTNINGSAPP BACKEND - INSPECTION MODEL
=============================================================================
Inspection model (Besiktning).

Represents a single inspection event at a property.
"""

from sqlalchemy import Column, String, Integer, Date, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class InspectionStatus(enum.Enum):
    """Inspection status enumeration."""
    DRAFT = "draft"
    FINAL = "final"
    ARCHIVED = "archived"


class OVKResult(enum.Enum):
    """OVK inspection result per ventilation system (B-blankett Resultat)."""
    G = "G"          # Godkänd
    C = "C"          # Kompletteringsbesiktning krävs (anmärkning)
    EG = "EG"        # Egenkontroll (ägaren besiktigar själv)
    EJ = "EJ"        # Ej besiktigad


class SystemType(enum.Enum):
    """Ventilation system type."""
    S = "S"    # Självdrag
    F = "F"    # Frånluft
    FT = "FT"  # Från- och tilluft
    FTX = "FTX"  # Från- och tilluft med värmeåtervinning
    FX = "FX"  # Frånluft med värmeåtervinning
    T = "T"    # Tilluft


class Inspection(BaseModel):
    """
    Inspection model (Besiktning).

    Attributes:
        property_id: Foreign key to Property
        inspector_id: Foreign key to User (besiktningsman)
        date: Inspection date
        active_time_seconds: Time spent actively inspecting (timer)
        status: Status (draft, final, archived)
        notes: General notes / A3 allmänt omdöme about the inspection
        ovk_result: OVK result per system (G/C/EG/EJ)
        next_inspection_date: Nästa ordinarie besiktningsdatum
        reinspection_date: Ombesiktningsdatum (if result C)
        system_number: Ventilationssystemnummer (e.g., "1", "B1")
        system_type: Systemtyp (S/F/FT/FTX/FX/T)
        inspection_category: Besiktningskategori 0–4
        energy_saving_measures: Selected energy saving measure numbers (JSON list of ints)
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
    
    # Notes / A3 Allmänt omdöme
    notes = Column(
        Text,
        nullable=True,
        comment="Allmänt omdöme (A3) and general notes about the inspection",
    )

    # OVK-specific fields
    ovk_result = Column(
        Enum(OVKResult),
        nullable=True,
        comment="OVK besiktningsresultat: G=Godkänd, C=Kompletteringsbesiktning, EG=Egenkontroll, EJ=Ej besiktigad",
    )

    next_inspection_date = Column(
        Date,
        nullable=True,
        comment="Nästa ordinarie besiktningsdatum",
    )

    reinspection_date = Column(
        Date,
        nullable=True,
        comment="Ombesiktningsdatum (fylls i om result == C)",
    )

    system_number = Column(
        String(20),
        nullable=True,
        comment="Ventilationssystemnummer (e.g. '1', 'B1', 'FT-1')",
    )

    system_type = Column(
        Enum(SystemType),
        nullable=True,
        comment="Systemtyp: S/F/FT/FTX/FX/T",
    )

    inspection_category = Column(
        Integer,
        nullable=True,
        comment="Besiktningskategori 0–4 per FunkiS/OVK",
    )

    energy_saving_measures = Column(
        String(200),
        nullable=True,
        comment="Kommaseparerade nr för möjliga energibesparande åtgärder (0–31)",
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
