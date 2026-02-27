"""
=============================================================================
BESIKTNINGSAPP BACKEND - SYNC ENDPOINTS
=============================================================================
Offline-first sync: handshake / push / pull.

Contract (see besiktnings-app-DB.txt §D):
  GET  /api/v1/sync/handshake
  POST /api/v1/sync/push          (X-Idempotency-Key required)
  GET  /api/v1/sync/pull?since=chg_..&limit=200
"""
from __future__ import annotations

from datetime import datetime

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.services.sync_service import SyncService

bp = Blueprint("sync", __name__)

_MAX_OPS_PER_PUSH = 500


# ─── Handshake ────────────────────────────────────────────────────────────────

@bp.route("/handshake", methods=["GET"])
@jwt_required()
def handshake():
    """Return server capabilities and current server time."""
    return jsonify({
        "data": {
            "server_time": datetime.utcnow().isoformat() + "Z",
            "min_client_version": "1.0.0",
            "conflict_policy_default": "LWW",
            "supports_presign_upload": True,
            "max_ops_per_push": _MAX_OPS_PER_PUSH,
        }
    }), 200


# ─── Push (client → server) ───────────────────────────────────────────────────

@bp.route("/push", methods=["POST"])
@jwt_required()
def push():
    """
    Push a batch of outbox operations from client to server.

    Required header:
        X-Idempotency-Key: <uuid>

    Request body:
        { "device_id": "dev_abc", "ops": [ { "op_id": "...", ... }, ... ] }

    Response 200:
        {
          "data": {
            "acked_op_ids": [...], "rejected_ops": [...],
            "id_map": [...], "server_cursor": "chg_000000000042"
          },
          "meta": { "server_time": "..." }
        }
    """
    idempotency_key = request.headers.get("X-Idempotency-Key", "")
    if not idempotency_key:
        return jsonify({
            "error": {
                "code": "missing_header",
                "message": "X-Idempotency-Key header is required for /sync/push",
            }
        }), 400

    data = request.get_json(silent=True) or {}
    ops = data.get("ops", [])
    device_id = data.get("device_id", "unknown")
    user_id = get_jwt_identity()

    if not isinstance(ops, list):
        return jsonify({
            "error": {"code": "validation_error", "message": "'ops' must be a list"}
        }), 400

    if len(ops) > _MAX_OPS_PER_PUSH:
        return jsonify({
            "error": {
                "code": "payload_too_large",
                "message": f"Maximum {_MAX_OPS_PER_PUSH} ops per push",
            }
        }), 413

    try:
        result = SyncService.process_push(
            user_id=int(user_id),
            device_id=str(device_id),
            operations=ops,
            idempotency_key=idempotency_key,
        )
    except Exception as exc:
        current_app.logger.exception("Sync push failed: %s", exc)
        return jsonify({
            "error": {"code": "internal_error", "message": "Sync push failed"}
        }), 500

    return jsonify({
        "data": result,
        "meta": {"server_time": datetime.utcnow().isoformat() + "Z"},
    }), 200


# ─── Pull (server → client) ───────────────────────────────────────────────────

@bp.route("/pull", methods=["GET"])
@jwt_required()
def pull():
    """
    Return server-side changes since a cursor.

    Query params:
        since  – cursor from previous pull, e.g. "chg_000000000042"
        limit  – max entries per page (default 200, max 500)

    Response 200:
        {
          "data": {
            "changes": [ { "change_id": "...", "entity_type": "...", ... } ],
            "next_cursor": "chg_000000000043",
            "has_more": false
          },
          "meta": { "server_time": "..." }
        }
    """
    since_cursor = request.args.get("since")
    try:
        limit = int(request.args.get("limit", 200))
    except ValueError:
        limit = 200

    user_id = get_jwt_identity()

    try:
        result = SyncService.process_pull(
            user_id=int(user_id),
            since_cursor=since_cursor,
            limit=limit,
        )
    except Exception as exc:
        current_app.logger.exception("Sync pull failed: %s", exc)
        return jsonify({
            "error": {"code": "internal_error", "message": "Sync pull failed"}
        }), 500

    return jsonify({
        "data": result,
        "meta": {"server_time": datetime.utcnow().isoformat() + "Z"},
    }), 200
