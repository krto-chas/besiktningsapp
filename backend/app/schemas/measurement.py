"""
=============================================================================
BESIKTNINGSAPP BACKEND - MEASUREMENT SCHEMAS
=============================================================================
Pydantic schemas for Measurement (Mätning) operations.
"""
from __future__ import annotations


from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.common import BaseSchema, TimestampMixin, RevisionMixin, ClientIdMixin, PaginationMeta


class MeasurementCreate(BaseModel):
    """Measurement creation schema."""
    client_id: Optional[str] = Field(default=None, description="Client UUID")
    inspection_id: Optional[int] = Field(default=None, description="Inspection ID")
    inspection_client_id: Optional[str] = Field(default=None, description="Inspection client ID")
    type: str = Field(pattern="^(flode|tryck|temp|co2|fukt|ljud|okand)$", description="Measurement type")
    value: float = Field(description="Measured value")
    unit: str = Field(min_length=1, max_length=20, description="Unit (e.g., l/s, Pa, °C)")
    apartment_number: Optional[str] = Field(default=None, max_length=20, description="Apartment number")
    sort_key: Optional[str] = Field(default=None, max_length=60, description="Sort key")
    notes: Optional[str] = Field(default=None, max_length=300, description="Notes")


class MeasurementUpdate(BaseModel):
    """Measurement update schema."""
    base_revision: int = Field(ge=1, description="Current revision")
    type: Optional[str] = Field(default=None, pattern="^(flode|tryck|temp|co2|fukt|ljud|okand)$")
    value: Optional[float] = None
    unit: Optional[str] = Field(default=None, max_length=20)
    apartment_number: Optional[str] = Field(default=None, max_length=20)
    sort_key: Optional[str] = Field(default=None, max_length=60)
    notes: Optional[str] = Field(default=None, max_length=300)


class MeasurementResponse(BaseSchema, TimestampMixin, RevisionMixin, ClientIdMixin):
    """Measurement response schema."""
    id: int
    inspection_id: int
    type: str
    value: float
    unit: str
    apartment_number: Optional[str]
    sort_key: Optional[str]
    notes: Optional[str]


class MeasurementList(BaseModel):
    """Measurement list response."""
    data: List[MeasurementResponse]
    meta: Optional[PaginationMeta] = None
