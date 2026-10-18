"""Dev-only auth + Idempotency-Key helpers for the Mock-data stage.

Real OIDC verification (backend-design_v01.md §11) is out of scope here;
DEV_AUTH just returns a fixed identity so routes have someone to attribute
confirmedBy/registeredBy to. Idempotency is a plain helper pair rather than a
FastAPI dependency because routes need the canonical-body hash computed from
the already-parsed body, which a generic Depends() can't see.
"""

import hashlib
import json

from fastapi import Header

from app.api.errors import ApiError
from app.core.settings import settings
from app.repositories.memory import now_iso, store


async def get_current_identity() -> dict:
    if not settings.dev_auth:
        raise ApiError(status_code=401, code="UNAUTHENTICATED", message="인증이 필요합니다.")
    return {"id": "user-01", "displayName": "운영 담당자"}


def canonical_hash(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


async def get_idempotency_key(idempotency_key: str | None = Header(default=None)) -> str | None:
    return idempotency_key


def check_idempotency(actor_id: str, method: str, route: str, key: str | None, body_hash: str):
    """Returns the stored response to replay, or None if this is a fresh request."""
    if not key:
        return None
    record = store.idempotency_records.get((actor_id, method, route, key))
    if record is None:
        return None
    if record["bodyHash"] != body_hash:
        raise ApiError(
            status_code=409,
            code="IDEMPOTENCY_CONFLICT",
            message="같은 Idempotency-Key로 다른 요청 본문이 전달되었습니다.",
        )
    return record["response"]


def save_idempotency(actor_id: str, method: str, route: str, key: str | None, body_hash: str, response: dict):
    if not key:
        return
    store.idempotency_records[(actor_id, method, route, key)] = {
        "bodyHash": body_hash,
        "response": response,
        "createdAt": now_iso(),
    }
