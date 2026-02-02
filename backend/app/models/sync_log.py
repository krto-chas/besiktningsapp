"""
=============================================================================
BESIKTNINGSAPP BACKEND - SYNC LOG MODEL
=============================================================================
Sync Log model for tracking sync operations and ensuring idempotency.

Stores processed operations to prevent duplicate processing.
"""
from __future__ import annotations


from datetime import datetime, timedelta

from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from app.models.base import BaseModel


class SyncLog(BaseModel):
    """
    Sync Log model for idempotency tracking.
    
    Attributes:
        idempotency_key: Unique key from X-Idempotency-Key header
        device_id: Client device identifier
        user_id: User who performed the operation
        operation_id: Client-generated operation ID (from sync push)
        entity_type: Type of entity (inspection, apartment, defect, etc.)
        action: Action performed (create, update, delete)
        client_id: Client-generated UUID for the entity
        server_id: Server-assigned ID after processing
        request_body: Original request body (for replay/debugging)
        response_body: Response returned to client
        status_code: HTTP status code
        processed_at: When the operation was processed
        expires_at: When this log entry can be cleaned up
    """
    
    __tablename__ = "sync_logs"
    
    # Idempotency
    idempotency_key = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Idempotency key from X-Idempotency-Key header",
    )
    
    # Client Information
    device_id = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Client device identifier",
    )
    
    user_id = Column(
        Integer,
        nullable=False,
        index=True,
        comment="User who performed the operation",
    )
    
    # Operation Details
    operation_id = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Client-generated operation ID",
    )
    
    entity_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Entity type (inspection, apartment, defect, etc.)",
    )
    
    action = Column(
        String(20),
        nullable=False,
        comment="Action: create, update, delete",
    )
    
    # Entity IDs
    client_id = Column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="Client-generated UUID for the entity",
    )
    
    server_id = Column(
        Integer,
        nullable=True,
        comment="Server-assigned ID after processing",
    )
    
    # Request/Response
    request_body = Column(
        JSON,
        nullable=True,
        comment="Original request body (for replay/debugging)",
    )
    
    response_body = Column(
        JSON,
        nullable=True,
        comment="Response returned to client",
    )
    
    status_code = Column(
        Integer,
        nullable=False,
        comment="HTTP status code",
    )
    
    # Timestamps
    processed_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="When the operation was processed",
    )
    
    expires_at = Column(
        DateTime,
        nullable=False,
        index=True,
        comment="When this log entry can be cleaned up",
    )
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_sync_log_device_user", "device_id", "user_id"),
        Index("idx_sync_log_entity", "entity_type", "client_id"),
        Index("idx_sync_log_expires", "expires_at"),
    )
    
    @classmethod
    def create_log(
        cls,
        idempotency_key: str,
        device_id: str,
        user_id: int,
        operation_id: str,
        entity_type: str,
        action: str,
        client_id: str = None,
        server_id: int = None,
        request_body: dict = None,
        response_body: dict = None,
        status_code: int = 200,
        ttl_hours: int = 24,
    ) -> "SyncLog":
        """
        Create a sync log entry.
        
        Args:
            idempotency_key: Unique idempotency key
            device_id: Client device ID
            user_id: User ID
            operation_id: Operation ID
            entity_type: Entity type
            action: Action (create, update, delete)
            client_id: Client UUID (optional)
            server_id: Server ID (optional)
            request_body: Request body (optional)
            response_body: Response body (optional)
            status_code: HTTP status code (default 200)
            ttl_hours: TTL in hours (default 24)
            
        Returns:
            SyncLog instance
        """
        return cls(
            idempotency_key=idempotency_key,
            device_id=device_id,
            user_id=user_id,
            operation_id=operation_id,
            entity_type=entity_type,
            action=action,
            client_id=client_id,
            server_id=server_id,
            request_body=request_body,
            response_body=response_body,
            status_code=status_code,
            processed_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=ttl_hours),
        )
    
    def __repr__(self) -> str:
        """String representation."""
        return f"<SyncLog(id={self.id}, key={self.idempotency_key}, entity={self.entity_type}, action={self.action})>"
