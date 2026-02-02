"""
=============================================================================
BESIKTNINGSAPP BACKEND - SYNC SCHEMAS
=============================================================================
Pydantic schemas for offline-first sync operations.
"""
from __future__ import annotations


from typing import List, Optional, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field


# =============================================================================
# SYNC HANDSHAKE
# =============================================================================

class SyncHandshakeResponse(BaseModel):
    """Sync handshake response."""
    
    data: Dict[str, Any] = Field(
        description="Server capabilities and configuration",
    )
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "data": {
                    "server_time": "2026-01-29T12:00:00Z",
                    "min_client_version": "1.0.0",
                    "conflict_policy_default": "LWW",
                    "supports_presign_upload": True
                }
            }
        }


# =============================================================================
# SYNC OPERATIONS
# =============================================================================

class SyncOperation(BaseModel):
    """Individual sync operation."""
    
    op_id: str = Field(
        description="Client-generated operation ID (UUID)",
    )
    
    entity_type: str = Field(
        description="Entity type (inspection, apartment, defect, etc.)",
    )
    
    action: str = Field(
        pattern="^(create|update|delete)$",
        description="Action: create, update, or delete",
    )
    
    client_id: Optional[str] = Field(
        default=None,
        description="Client UUID for the entity",
    )
    
    server_id: Optional[int] = Field(
        default=None,
        description="Server ID (if known)",
    )
    
    base_revision: int = Field(
        default=0,
        ge=0,
        description="Base revision for optimistic locking",
    )
    
    payload: Dict[str, Any] = Field(
        description="Operation payload (entity data)",
    )
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "op_id": "op_001_uuid",
                "entity_type": "inspection",
                "action": "create",
                "client_id": "c_ins_001_uuid",
                "server_id": None,
                "base_revision": 0,
                "payload": {
                    "property_client_id": "c_prop_001_uuid",
                    "date": "2026-01-29",
                    "status": "draft"
                }
            }
        }


# =============================================================================
# SYNC PUSH
# =============================================================================

class SyncPushRequest(BaseModel):
    """Sync push request (client → server)."""
    
    device_id: str = Field(
        description="Device identifier",
    )
    
    user_id: int = Field(
        description="User ID",
    )
    
    client_time: datetime = Field(
        description="Client timestamp (ISO 8601)",
    )
    
    ops: List[SyncOperation] = Field(
        max_items=100,
        description="List of operations (max 100)",
    )
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "device_id": "dev_abc",
                "user_id": 1,
                "client_time": "2026-01-29T12:00:00Z",
                "ops": [
                    {
                        "op_id": "op_001",
                        "entity_type": "inspection",
                        "action": "create",
                        "client_id": "c_ins_001",
                        "payload": {"date": "2026-01-29"}
                    }
                ]
            }
        }


class SyncPushResponse(BaseModel):
    """Sync push response (server → client)."""
    
    data: Dict[str, Any] = Field(
        description="Push response data",
    )
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "data": {
                    "processed": 5,
                    "failed": 0,
                    "conflicts": [],
                    "id_mappings": [
                        {
                            "op_id": "op_001",
                            "client_id": "c_ins_001",
                            "server_id": 123
                        }
                    ]
                }
            }
        }


# =============================================================================
# SYNC PULL
# =============================================================================

class SyncPullRequest(BaseModel):
    """Sync pull request (client → server)."""
    
    device_id: str = Field(
        description="Device identifier",
    )
    
    user_id: int = Field(
        description="User ID",
    )
    
    last_sync_time: Optional[datetime] = Field(
        default=None,
        description="Last successful sync timestamp (ISO 8601)",
    )
    
    cursor: Optional[str] = Field(
        default=None,
        description="Cursor for pagination",
    )
    
    limit: int = Field(
        default=100,
        ge=1,
        le=100,
        description="Max entities to return",
    )
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "device_id": "dev_abc",
                "user_id": 1,
                "last_sync_time": "2026-01-28T12:00:00Z",
                "cursor": None,
                "limit": 100
            }
        }


class SyncPullResponse(BaseModel):
    """Sync pull response (server → client)."""
    
    data: Dict[str, Any] = Field(
        description="Pull response data",
    )
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "data": {
                    "entities": [
                        {
                            "entity_type": "inspection",
                            "server_id": 123,
                            "client_id": "c_ins_001",
                            "revision": 1,
                            "action": "update",
                            "data": {"date": "2026-01-29", "status": "draft"}
                        }
                    ],
                    "cursor": "next_cursor_here",
                    "has_more": False,
                    "server_time": "2026-01-29T12:00:00Z"
                }
            }
        }


# =============================================================================
# CONFLICT HANDLING
# =============================================================================

class ConflictInfo(BaseModel):
    """Conflict information."""
    
    op_id: str = Field(
        description="Operation ID that caused conflict",
    )
    
    entity_type: str = Field(
        description="Entity type",
    )
    
    client_id: Optional[str] = Field(
        description="Client UUID",
    )
    
    server_id: Optional[int] = Field(
        description="Server ID",
    )
    
    conflict_type: str = Field(
        description="Conflict type (revision_mismatch, not_found, etc.)",
    )
    
    client_revision: int = Field(
        description="Client's base revision",
    )
    
    server_revision: int = Field(
        description="Current server revision",
    )
    
    server_state: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Current server state",
    )
    
    client_changes: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Client's attempted changes",
    )
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "op_id": "op_005",
                "entity_type": "defect",
                "client_id": "c_def_001",
                "server_id": 777,
                "conflict_type": "revision_mismatch",
                "client_revision": 2,
                "server_revision": 4,
                "server_state": {"description": "Server version"},
                "client_changes": {"description": "Client version"}
            }
        }
