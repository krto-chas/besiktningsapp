from __future__ import annotations

"""
=============================================================================
BESIKTNINGSAPP BACKEND - USER MODEL
=============================================================================
User model representing besiktningsmän (inspectors).

Stores authentication credentials and inspector profile information.
"""

from typing import Optional

from sqlalchemy import Column, String, Boolean, Text
from sqlalchemy.orm import relationship
import bcrypt

from app.models.base import BaseModel


class User(BaseModel):
    """
    User model (Besiktningsman/Inspector).
    
    Attributes:
        email: Unique email address for login
        password_hash: Bcrypt hashed password
        name: Full name
        role: User role (admin, inspector, viewer)
        active: Whether the account is active
        company_name: Company/organization name
        certification_org: Certifieringsorgan (SP, SITAC, etc.)
        certification_number: Certifieringsnummer
        certification_valid_until: Giltighetstid för certifiering
        competence: Behörighet/kompetensområde
        phone: Contact phone number
        signature_image_id: ID of signature image (stored separately)
    """
    
    __tablename__ = "users"
    
    # Authentication
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique email address for login",
    )
    
    password_hash = Column(
        String(255),
        nullable=False,
        comment="Bcrypt hashed password",
    )
    
    # Profile
    name = Column(
        String(255),
        nullable=False,
        comment="Full name of the inspector",
    )
    
    role = Column(
        String(50),
        nullable=False,
        default="inspector",
        comment="User role: admin, inspector, viewer",
    )
    
    active = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Whether the account is active",
    )
    
    # Company/Organization
    company_name = Column(
        String(255),
        nullable=True,
        comment="Company or organization name",
    )
    
    # Certification
    certification_org = Column(
        String(100),
        nullable=True,
        comment="Certifieringsorgan (SP, SITAC, etc.)",
    )
    
    certification_number = Column(
        String(100),
        nullable=True,
        comment="Certifieringsnummer",
    )
    
    certification_valid_until = Column(
        String(50),
        nullable=True,
        comment="Giltighetstid för certifiering (YYYY-MM-DD eller text)",
    )
    
    competence = Column(
        Text,
        nullable=True,
        comment="Behörighet/kompetensområde (kan vara längre text)",
    )
    
    # Contact
    phone = Column(
        String(50),
        nullable=True,
        comment="Contact phone number",
    )
    
    # Signature
    signature_image_id = Column(
        String(255),
        nullable=True,
        comment="Reference to signature image (stored in storage service)",
    )
    
    # Relationships
    inspections = relationship(
        "Inspection",
        back_populates="inspector",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    
    def set_password(self, password: str) -> None:
        """
        Hash and set password.
        
        Args:
            password: Plain text password
        """
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            salt
        ).decode("utf-8")
    
    def check_password(self, password: str) -> bool:
        """
        Verify password against stored hash.
        
        Args:
            password: Plain text password to verify
            
        Returns:
            True if password matches, False otherwise
        """
        return bcrypt.checkpw(
            password.encode("utf-8"),
            self.password_hash.encode("utf-8")
        )
    
    def to_dict(self, include_relationships: bool = False) -> dict:
        """
        Convert to dictionary, excluding password_hash.
        
        Args:
            include_relationships: Whether to include relationships
            
        Returns:
            Dictionary representation without sensitive data
        """
        data = super().to_dict(include_relationships=include_relationships)
        # Remove password hash from output
        data.pop("password_hash", None)
        return data
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<User(id={self.id}, email={self.email}, name={self.name})>"
