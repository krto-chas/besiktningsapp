"""
=============================================================================
BESIKTNINGSAPP BACKEND - STANDARD DEFECT MODEL
=============================================================================
Standard Defect model (Standardfel).

Pre-defined defect templates that users can reference.
Users can create their own or modify standard ones.
"""
from __future__ import annotations


from sqlalchemy import Column, String, Text, Enum, Boolean

from app.models.base import BaseModel
from app.models.defect import DefectSeverity


class StandardDefect(BaseModel):
    """
    Standard Defect model (Standardfel template).
    
    Attributes:
        code: Unique defect code (e.g., "VF01", "VF02")
        title: Short title/summary
        description: Standard description text
        remedy: Standard remedy text
        severity: Default severity level
        active: Whether this template is active/available
        category: Optional category for grouping
    """
    
    __tablename__ = "standard_defects"
    
    # Code
    code = Column(
        String(30),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique defect code (e.g., VF01)",
    )
    
    # Template Content
    title = Column(
        String(120),
        nullable=False,
        comment="Short title/summary",
    )
    
    description = Column(
        Text,
        nullable=False,
        comment="Standard description text",
    )
    
    remedy = Column(
        Text,
        nullable=True,
        comment="Standard remedy text",
    )
    
    severity = Column(
        Enum(DefectSeverity),
        nullable=False,
        default=DefectSeverity.MEDIUM,
        comment="Default severity level",
    )
    
    # Status
    active = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether this template is active/available",
    )
    
    # Organization
    category = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Category for grouping (e.g., 'Ventilation', 'Plumbing')",
    )
    
    def to_defect_dict(self) -> dict:
        """
        Convert to dictionary suitable for creating a Defect.
        
        Returns:
            Dictionary with defect fields
        """
        return {
            "code": self.code,
            "title": self.title,
            "description": self.description,
            "remedy": self.remedy,
            "severity": self.severity,
        }
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<StandardDefect(code={self.code}, title={self.title})>"
