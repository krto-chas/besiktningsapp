from __future__ import annotations

"""
=============================================================================
BESIKTNINGSAPP BACKEND - CHANGE LOG MODEL
=============================================================================
Append-only log of every entity mutation.

Used as the cursor source for /sync/pull – clients request all changes
after a given cursor (change_log.id) and receive exactly the diff they need.

Design decisions:
- Does NOT inherit from BaseModel (it is infrastructure, not a domain entity).
- Immutable: rows are never updated or soft-deleted; old rows are purged by a
  scheduled job after a configurable retention window (default 90 days).
- Sequential integer PK is used as the cursor value.
- Cursor wire format: "chg_000000000001" (4-char prefix + 12-digit zero-padded id).
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Index, Integer, JSON, String

from app.extensions import db


class ChangeLog(db.Model):
    """
    Append-only change log for offline-first sync.

    Attributes:
        id:                  Auto-increment PK, used as sync cursor.
        entity_type:         Domain type ("property", "inspection", etc.)
        server_id:           PK of the changed entity in its own table.
        action:              "create" | "update" | "delete"
        revision:            Entity revision at time of change.
        payload:             Full entity dict snapshot (null for deletes).
        changed_by_user_id:  User who caused the mutation.
        created_at:          Wall-clock time of the mutation (UTC).
    """

    __tablename__ = "change_log"

    id = Column(Integer, primary_key=True, autoincrement=True)

    entity_type = Column(
        String(50),
        nullable=False,
        comment="Domain entity type: property, inspection, apartment, defect, measurement",
    )

    server_id = Column(
        Integer,
        nullable=False,
        comment="PK of the changed entity in its own table",
    )

    action = Column(
        String(20),
        nullable=False,
        comment="Mutation action: create | update | delete",
    )

    revision = Column(
        Integer,
        nullable=False,
        comment="Entity revision at time of this change",
    )

    payload = Column(
        JSON,
        nullable=True,
        comment="Full entity snapshot at time of change; null for deletes",
    )

    changed_by_user_id = Column(
        Integer,
        nullable=True,
        comment="User ID who performed the mutation",
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment="UTC timestamp of mutation",
    )

    __table_args__ = (
        Index("idx_change_log_entity", "entity_type", "server_id"),
        Index("idx_change_log_cursor", "id"),  # explicit for cursor queries
    )

    # ─── Cursor helpers ────────────────────────────────────────────────────

    @staticmethod
    def cursor_from_id(change_id: int) -> str:
        """Encode a numeric ID as a wire cursor string: 'chg_000000000001'."""
        return f"chg_{change_id:012d}"

    @staticmethod
    def id_from_cursor(cursor: str | None) -> int:
        """
        Decode a wire cursor string to a numeric ID.

        Returns 0 (meaning "from the beginning") if cursor is absent or invalid.
        """
        if not cursor:
            return 0
        try:
            if cursor.startswith("chg_"):
                return int(cursor[4:])
            # Accept plain integers too (convenient for testing)
            return int(cursor)
        except (ValueError, IndexError):
            return 0

    def __repr__(self) -> str:
        return (
            f"<ChangeLog(id={self.id}, {self.entity_type} #{self.server_id}"
            f" {self.action} rev={self.revision})>"
        )
