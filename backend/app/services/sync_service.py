"""
=============================================================================
BESIKTNINGSAPP BACKEND - SYNC SERVICE
=============================================================================
Offline-first sync orchestration: push (client→server) and pull (server→client).

Design:
- push: accepts a batch of ops (create/update/delete), applies them
  transactionally, detects revision conflicts, returns per-op ack/reject and
  client_id→server_id mappings.
- pull: returns a page of ChangeLog entries since a cursor; client replays
  them to bring its local DB up to date.
- Idempotency: the whole push batch is deduplicated by X-Idempotency-Key;
  individual create ops are deduplicated by client_id.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from flask import current_app
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import (
    Apartment,
    ChangeLog,
    Defect,
    Inspection,
    Measurement,
    Property,
    SyncLog,
)
from app.models.defect import DefectSeverity
from app.models.inspection import InspectionStatus
from app.models.measurement import MeasurementType


# ─── Field allowlists for PATCH (update) operations ───────────────────────────

_UPDATABLE: dict[str, set[str]] = {
    "property": {
        "property_type", "designation", "owner", "owner_name",
        "address", "postal_code", "city", "num_apartments",
        "num_premises", "construction_year", "notes",
    },
    "inspection": {
        "date", "status", "active_time_seconds", "notes",
    },
    "apartment": {
        "apartment_number", "rooms", "notes",
    },
    "defect": {
        "room_index", "code", "title", "description", "remedy", "severity",
    },
    "measurement": {
        "type", "value", "unit", "apartment_number", "sort_key", "notes",
    },
}

_ENTITY_MODEL: dict[str, Any] = {
    "property": Property,
    "inspection": Inspection,
    "apartment": Apartment,
    "defect": Defect,
    "measurement": Measurement,
}


# ─── Public API ───────────────────────────────────────────────────────────────

class SyncService:
    """Sync orchestration service."""

    # ── Push ──────────────────────────────────────────────────────────────────

    @staticmethod
    def process_push(
        user_id: int,
        device_id: str,
        operations: list[dict],
        idempotency_key: str,
    ) -> dict:
        """
        Process a batch of push operations from the client.

        Returns a dict shaped for the /sync/push response:
          acked_op_ids  – op_ids that succeeded (including replays)
          rejected_ops  – op_ids that failed with reason + conflict detail
          id_map        – client_id→server_id mappings (+ revision)
          server_cursor – latest change_log id after this batch
        """
        # ── Batch-level idempotency ────────────────────────────────────────
        existing = SyncLog.query.filter_by(idempotency_key=idempotency_key).first()
        if existing and existing.response_body:
            return existing.response_body

        acked_op_ids: list[str] = []
        rejected_ops: list[dict] = []
        id_map: list[dict] = []
        latest_change_id: int = 0

        for op in operations:
            op_id = op.get("op_id", "")
            try:
                result = SyncService._process_operation(user_id, op)
            except Exception as exc:
                current_app.logger.exception("Unexpected error in op %s: %s", op_id, exc)
                db.session.rollback()
                rejected_ops.append({
                    "op_id": op_id,
                    "reason": "internal_error",
                    "detail": str(exc),
                })
                continue

            if result.get("conflict"):
                rejected_ops.append({
                    "op_id": op_id,
                    "reason": "conflict",
                    "conflict": result["conflict"],
                })
            elif result.get("error"):
                rejected_ops.append({
                    "op_id": op_id,
                    "reason": result["error"],
                })
            else:
                acked_op_ids.append(op_id)
                if result.get("id_mapping"):
                    id_map.append(result["id_mapping"])
                if result.get("change_id", 0) > latest_change_id:
                    latest_change_id = result["change_id"]

        # Commit all successful ops together
        try:
            db.session.commit()
        except IntegrityError as exc:
            db.session.rollback()
            current_app.logger.error("Commit failed during push: %s", exc)

        # Determine server cursor (latest change in DB)
        if latest_change_id == 0:
            last = ChangeLog.query.order_by(ChangeLog.id.desc()).first()
            latest_change_id = last.id if last else 0

        server_cursor = ChangeLog.cursor_from_id(latest_change_id)

        response: dict = {
            "acked_op_ids": acked_op_ids,
            "rejected_ops": rejected_ops,
            "id_map": id_map,
            "server_cursor": server_cursor,
        }

        # Persist batch for idempotency replay
        log = SyncLog.create_log(
            idempotency_key=idempotency_key,
            device_id=device_id,
            user_id=user_id,
            operation_id=f"batch_{idempotency_key}",
            entity_type="batch",
            action="push",
            response_body=response,
            status_code=200,
        )
        db.session.add(log)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

        return response

    # ── Pull ──────────────────────────────────────────────────────────────────

    @staticmethod
    def process_pull(
        user_id: int,
        since_cursor: str | None,
        limit: int = 200,
    ) -> dict:
        """
        Return ChangeLog entries since *since_cursor*.

        Returns a dict shaped for the /sync/pull response:
          changes     – list of change objects
          next_cursor – cursor to use for the next pull
          has_more    – True if there are more changes beyond this page
        """
        since_id = ChangeLog.id_from_cursor(since_cursor)
        limit = min(max(1, limit), 500)  # clamp [1, 500]

        # Fetch one extra to detect has_more
        rows = (
            ChangeLog.query
            .filter(ChangeLog.id > since_id)
            .order_by(ChangeLog.id.asc())
            .limit(limit + 1)
            .all()
        )

        has_more = len(rows) > limit
        page = rows[:limit]

        changes = []
        for row in page:
            changes.append({
                "change_id": ChangeLog.cursor_from_id(row.id),
                "entity_type": row.entity_type,
                "server_id": row.server_id,
                "action": row.action,
                "revision": row.revision,
                "updated_at": row.created_at.isoformat() + "Z",
                "payload": row.payload,
            })

        next_cursor = (
            ChangeLog.cursor_from_id(page[-1].id)
            if page
            else (since_cursor or ChangeLog.cursor_from_id(0))
        )

        return {
            "changes": changes,
            "next_cursor": next_cursor,
            "has_more": has_more,
        }

    # ─── Internal helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _process_operation(user_id: int, op: dict) -> dict:
        """
        Process a single sync operation.

        Returns one of:
          {"change_id": int, "id_mapping": dict}   – success
          {"conflict": dict}                         – revision conflict
          {"error": str}                             – validation / not-found
        """
        entity_type = op.get("entity_type", "")
        action = op.get("action", "")
        client_id = op.get("client_id")
        server_id = op.get("server_id")
        payload = op.get("payload") or {}
        base_revision = op.get("base_revision", 0)

        model = _ENTITY_MODEL.get(entity_type)
        if model is None:
            return {"error": f"unknown_entity_type:{entity_type}"}

        if action == "create":
            return SyncService._handle_create(
                model, entity_type, client_id, payload, user_id
            )
        elif action == "update":
            return SyncService._handle_update(
                model, entity_type, server_id, client_id,
                base_revision, payload, user_id,
            )
        elif action == "delete":
            return SyncService._handle_delete(
                model, entity_type, server_id, client_id,
                base_revision, user_id,
            )

        return {"error": f"unknown_action:{action}"}

    # ── Create ────────────────────────────────────────────────────────────────

    @staticmethod
    def _handle_create(
        model: Any,
        entity_type: str,
        client_id: str | None,
        payload: dict,
        user_id: int,
    ) -> dict:
        # Deduplicate by client_id
        if client_id:
            try:
                cid = uuid.UUID(client_id)
            except ValueError:
                return {"error": "invalid_client_id"}
            existing = model.query.filter_by(client_id=cid).first()
            if existing:
                return {
                    "change_id": 0,
                    "id_mapping": {
                        "entity_type": entity_type,
                        "client_id": client_id,
                        "server_id": existing.id,
                        "revision": existing.revision,
                    },
                }

        try:
            entity = SyncService._build_entity(
                model, entity_type, client_id, payload, user_id
            )
        except (KeyError, ValueError, TypeError) as exc:
            return {"error": f"build_failed:{exc}"}

        db.session.add(entity)
        db.session.flush()  # populate entity.id

        change = SyncService._write_changelog(entity, entity_type, "create", user_id)
        db.session.flush()

        return {
            "change_id": change.id,
            "id_mapping": {
                "entity_type": entity_type,
                "client_id": client_id,
                "server_id": entity.id,
                "revision": entity.revision,
            },
        }

    # ── Update ────────────────────────────────────────────────────────────────

    @staticmethod
    def _handle_update(
        model: Any,
        entity_type: str,
        server_id: int | None,
        client_id: str | None,
        base_revision: int,
        payload: dict,
        user_id: int,
    ) -> dict:
        entity = SyncService._find_entity(model, server_id, client_id)
        if entity is None:
            return {"error": "not_found"}

        if entity.revision != base_revision:
            return {
                "conflict": {
                    "entity_type": entity_type,
                    "server_id": entity.id,
                    "current_revision": entity.revision,
                    "base_revision": base_revision,
                    "server_state": entity.to_dict(),
                    "recommended_action": "fetch_latest_and_merge",
                }
            }

        SyncService._apply_payload(entity, entity_type, payload)
        entity.revision += 1
        entity.updated_at = datetime.utcnow()

        change = SyncService._write_changelog(entity, entity_type, "update", user_id)
        db.session.flush()

        return {"change_id": change.id}

    # ── Delete ────────────────────────────────────────────────────────────────

    @staticmethod
    def _handle_delete(
        model: Any,
        entity_type: str,
        server_id: int | None,
        client_id: str | None,
        base_revision: int,
        user_id: int,
    ) -> dict:
        entity = SyncService._find_entity(model, server_id, client_id)
        if entity is None:
            # Idempotent: already deleted or never existed
            return {"change_id": 0}

        if base_revision and entity.revision != base_revision:
            return {
                "conflict": {
                    "entity_type": entity_type,
                    "server_id": entity.id,
                    "current_revision": entity.revision,
                    "base_revision": base_revision,
                    "recommended_action": "fetch_latest_then_delete",
                }
            }

        entity.deleted_at = datetime.utcnow()
        entity.revision += 1
        entity.updated_at = datetime.utcnow()

        change = SyncService._write_changelog(entity, entity_type, "delete", user_id, payload=None)
        db.session.flush()

        return {"change_id": change.id}

    # ─── Entity builders ──────────────────────────────────────────────────────

    @staticmethod
    def _build_entity(
        model: Any,
        entity_type: str,
        client_id: str | None,
        payload: dict,
        user_id: int,
    ) -> Any:
        """Create (but do not persist) the right model instance from payload."""
        cid = uuid.UUID(client_id) if client_id else None
        builders = {
            "property":    SyncService._build_property,
            "inspection":  SyncService._build_inspection,
            "apartment":   SyncService._build_apartment,
            "defect":      SyncService._build_defect,
            "measurement": SyncService._build_measurement,
        }
        builder = builders.get(entity_type)
        if builder is None:
            raise ValueError(f"No builder for entity_type={entity_type}")
        return builder(cid, payload, user_id)

    @staticmethod
    def _build_property(client_id, payload: dict, user_id: int) -> Property:
        addr = payload.get("address", {})
        if isinstance(addr, str):
            street, postal_code, city = addr, None, None
        else:
            street = addr.get("street", "")
            postal_code = addr.get("postal_code")
            city = addr.get("city", "")

        units = payload.get("units", {})
        return Property(
            client_id=client_id,
            property_type=payload.get("type", payload.get("property_type", "bostadshus")),
            designation=payload["designation"],
            owner=payload.get("owner_name", payload.get("owner")),
            address=street,
            postal_code=postal_code,
            city=city,
            num_apartments=units.get("apartments", payload.get("num_apartments", 0)),
            num_premises=units.get("premises", payload.get("num_premises", 0)),
            construction_year=payload.get("construction_year"),
            notes=payload.get("notes"),
        )

    @staticmethod
    def _build_inspection(client_id, payload: dict, user_id: int) -> Inspection:
        property_id = payload.get("property_id")
        if not property_id and payload.get("property_client_id"):
            prop = Property.query.filter_by(
                client_id=uuid.UUID(payload["property_client_id"])
            ).first()
            if prop:
                property_id = prop.id
        if not property_id:
            raise ValueError("Cannot resolve property for inspection")

        raw_date = payload.get("date")
        insp_date = date.fromisoformat(raw_date) if raw_date else date.today()

        try:
            status = InspectionStatus(payload.get("status", "draft").lower())
        except ValueError:
            status = InspectionStatus.DRAFT

        return Inspection(
            client_id=client_id,
            property_id=property_id,
            inspector_id=payload.get("inspector_id", user_id),
            date=insp_date,
            active_time_seconds=payload.get("active_time_seconds", 0),
            status=status,
            notes=payload.get("notes"),
        )

    @staticmethod
    def _build_apartment(client_id, payload: dict, user_id: int) -> Apartment:
        inspection_id = payload.get("inspection_id")
        if not inspection_id and payload.get("inspection_client_id"):
            insp = Inspection.query.filter_by(
                client_id=uuid.UUID(payload["inspection_client_id"])
            ).first()
            if insp:
                inspection_id = insp.id
        if not inspection_id:
            raise ValueError("Cannot resolve inspection for apartment")

        return Apartment(
            client_id=client_id,
            inspection_id=inspection_id,
            apartment_number=payload["apartment_number"],
            rooms=payload.get("rooms", []),
            notes=payload.get("notes"),
        )

    @staticmethod
    def _build_defect(client_id, payload: dict, user_id: int) -> Defect:
        apartment_id = payload.get("apartment_id")
        if not apartment_id and payload.get("apartment_client_id"):
            apt = Apartment.query.filter_by(
                client_id=uuid.UUID(payload["apartment_client_id"])
            ).first()
            if apt:
                apartment_id = apt.id
        if not apartment_id:
            raise ValueError("Cannot resolve apartment for defect")

        try:
            severity = DefectSeverity[payload.get("severity", "medium").upper()]
        except KeyError:
            severity = DefectSeverity.MEDIUM

        return Defect(
            client_id=client_id,
            apartment_id=apartment_id,
            room_index=payload.get("room_index", 0),
            code=payload.get("code"),
            title=payload.get("title"),
            description=payload["description"],
            remedy=payload.get("remedy"),
            severity=severity,
        )

    @staticmethod
    def _build_measurement(client_id, payload: dict, user_id: int) -> Measurement:
        inspection_id = payload.get("inspection_id")
        if not inspection_id and payload.get("inspection_client_id"):
            insp = Inspection.query.filter_by(
                client_id=uuid.UUID(payload["inspection_client_id"])
            ).first()
            if insp:
                inspection_id = insp.id
        if not inspection_id:
            raise ValueError("Cannot resolve inspection for measurement")

        try:
            mtype = MeasurementType(payload.get("type", "okand"))
        except ValueError:
            mtype = MeasurementType.OKAND

        return Measurement(
            client_id=client_id,
            inspection_id=inspection_id,
            type=mtype,
            value=float(payload["value"]),
            unit=payload["unit"],
            apartment_number=payload.get("apartment_number"),
            sort_key=payload.get("sort_key"),
            notes=payload.get("notes"),
        )

    # ─── Apply payload to existing entity (PATCH semantics) ───────────────────

    @staticmethod
    def _apply_payload(entity: Any, entity_type: str, payload: dict) -> None:
        """Apply whitelisted fields from payload onto entity."""
        allowed = _UPDATABLE.get(entity_type, set())
        for field, value in payload.items():
            if field not in allowed:
                continue
            if entity_type == "inspection" and field == "status":
                try:
                    value = InspectionStatus(str(value).lower())
                except ValueError:
                    continue
            elif entity_type == "inspection" and field == "date":
                if isinstance(value, str):
                    value = date.fromisoformat(value)
            elif entity_type == "defect" and field == "severity":
                try:
                    value = DefectSeverity[str(value).upper()]
                except KeyError:
                    continue
            elif entity_type == "measurement" and field == "type":
                try:
                    value = MeasurementType(value)
                except ValueError:
                    continue
            elif entity_type == "property" and field == "owner_name":
                setattr(entity, "owner", value)
                continue

            setattr(entity, field, value)

    # ─── Utilities ────────────────────────────────────────────────────────────

    @staticmethod
    def _find_entity(model: Any, server_id: int | None, client_id: str | None) -> Any:
        """Look up entity by server_id (preferred) or client_id, excluding soft-deleted."""
        if server_id:
            return model.query.filter_by(id=server_id, deleted_at=None).first()
        if client_id:
            try:
                cid = uuid.UUID(client_id)
            except ValueError:
                return None
            return model.query.filter_by(client_id=cid, deleted_at=None).first()
        return None

    @staticmethod
    def _write_changelog(
        entity: Any,
        entity_type: str,
        action: str,
        user_id: int,
        payload: dict | None = ...,
    ) -> ChangeLog:
        """
        Append a ChangeLog row.

        payload=None  → delete (no snapshot stored)
        payload=...   → auto-call entity.to_dict()
        payload=dict  → use explicitly
        """
        snapshot = entity.to_dict() if payload is ... else payload

        entry = ChangeLog(
            entity_type=entity_type,
            server_id=entity.id,
            action=action,
            revision=entity.revision,
            payload=snapshot,
            changed_by_user_id=user_id,
            created_at=datetime.utcnow(),
        )
        db.session.add(entry)
        return entry
