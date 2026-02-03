from __future__ import annotations

"""
=============================================================================
BESIKTNINGSAPP BACKEND - MODELS PACKAGE
=============================================================================
Domain models for the application.

All models inherit from BaseModel which provides:
- id (primary key)
- client_id (UUID from mobile client)
- revision (for optimistic locking)
- created_at, updated_at (timestamps)
"""
from app.models.base import BaseModel
from app.models.user import User
from app.models.property import Property
from app.models.inspection import Inspection
from app.models.apartment import Apartment
from app.models.defect import Defect
from app.models.image import Image
from app.models.measurement import Measurement
from app.models.pdf_version import PDFVersion
from app.models.sync_log import SyncLog
from app.models.standard_defect import StandardDefect

__all__ = [
    "BaseModel",
    "User",
    "Property",
    "Inspection",
    "Apartment",
    "Defect",
    "Image",
    "Measurement",
    "PDFVersion",
    "SyncLog",
    "StandardDefect",
]
