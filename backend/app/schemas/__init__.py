"""
=============================================================================
BESIKTNINGSAPP BACKEND - SCHEMAS PACKAGE
=============================================================================
Pydantic schemas for request/response validation and serialization.

All schemas follow the API contract specification and provide:
- Input validation with proper error messages
- Type safety and conversion
- Documentation for API endpoints
- Request/Response models
"""
from __future__ import annotations

from app.schemas.common import (
    PaginationParams,
    PaginationMeta,
    CursorPaginationParams,
    StandardResponse,
    ErrorResponse,
    FieldError,
)
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    TokenResponse,
    UserProfile,
)
from app.schemas.property import (
    PropertyCreate,
    PropertyUpdate,
    PropertyResponse,
    PropertyList,
)
from app.schemas.inspection import (
    InspectionCreate,
    InspectionUpdate,
    InspectionResponse,
    InspectionList,
)
from app.schemas.apartment import (
    RoomSchema,
    ApartmentCreate,
    ApartmentUpdate,
    ApartmentResponse,
    ApartmentList,
)
from app.schemas.defect import (
    DefectCreate,
    DefectUpdate,
    DefectResponse,
    DefectList,
    DefectPhotoSchema,
)
from app.schemas.image import (
    ImageUploadRequest,
    PresignedUploadRequest,
    PresignedUploadResponse,
    ImageResponse,
    ImageCompleteRequest,
)
from app.schemas.measurement import (
    MeasurementCreate,
    MeasurementUpdate,
    MeasurementResponse,
    MeasurementList,
)
from app.schemas.sync import (
    SyncHandshakeResponse,
    SyncOperation,
    SyncPushRequest,
    SyncPushResponse,
    SyncPullRequest,
    SyncPullResponse,
    ConflictInfo,
)
from app.schemas.pdf import (
    PDFGenerateRequest,
    PDFGenerateResponse,
    PDFVersionResponse,
    PDFVersionList,
)

__all__ = [
    # Common
    "PaginationParams",
    "PaginationMeta",
    "CursorPaginationParams",
    "StandardResponse",
    "ErrorResponse",
    "FieldError",
    # Auth
    "LoginRequest",
    "LoginResponse",
    "TokenResponse",
    "UserProfile",
    # Property
    "PropertyCreate",
    "PropertyUpdate",
    "PropertyResponse",
    "PropertyList",
    # Inspection
    "InspectionCreate",
    "InspectionUpdate",
    "InspectionResponse",
    "InspectionList",
    # Apartment
    "RoomSchema",
    "ApartmentCreate",
    "ApartmentUpdate",
    "ApartmentResponse",
    "ApartmentList",
    # Defect
    "DefectCreate",
    "DefectUpdate",
    "DefectResponse",
    "DefectList",
    "DefectPhotoSchema",
    # Image
    "ImageUploadRequest",
    "PresignedUploadRequest",
    "PresignedUploadResponse",
    "ImageResponse",
    "ImageCompleteRequest",
    # Measurement
    "MeasurementCreate",
    "MeasurementUpdate",
    "MeasurementResponse",
    "MeasurementList",
    # Sync
    "SyncHandshakeResponse",
    "SyncOperation",
    "SyncPushRequest",
    "SyncPushResponse",
    "SyncPullRequest",
    "SyncPullResponse",
    "ConflictInfo",
    # PDF
    "PDFGenerateRequest",
    "PDFGenerateResponse",
    "PDFVersionResponse",
    "PDFVersionList",
]
