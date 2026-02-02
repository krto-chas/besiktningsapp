"""
=============================================================================
BESIKTNINGSAPP BACKEND - SERVICES PACKAGE
=============================================================================
Business logic services.

Services contain the core business logic and orchestration, keeping
controllers thin and focused on HTTP request/response handling.

Available services:
- auth_service: JWT token generation and validation
- property_service: Property business logic
- inspection_service: Inspection business logic
- sync_service: Offline-first sync orchestration
- storage_service: Abstract storage interface
- local_storage: Local file storage implementation
- s3_storage: S3/MinIO storage implementation
- pdf_service: PDF generation and versioning
- image_service: Image handling and validation
- conflict_resolver: Sync conflict resolution
"""

from app.services.auth_service import AuthService
from app.services.storage_service import StorageService
from app.services.local_storage import LocalStorage
from app.services.s3_storage import S3Storage

__all__ = [
    "AuthService",
    "StorageService",
    "LocalStorage",
    "S3Storage",
]
