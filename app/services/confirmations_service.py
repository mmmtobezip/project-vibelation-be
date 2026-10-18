"""CONF-01~03 — api_interface_v06.md §19.3 (MD-only 확정)."""

import hashlib

from app.api import errors
from app.repositories.memory import new_id, now_iso, store
from app.schemas.confirmations import ConfirmBody
from app.services.requests_service import get_request


def confirm(request_id: str, body: ConfirmBody, identity: dict) -> tuple[dict, bool]:
    """Returns (confirmation, is_new) so the route can pick 201 vs 200."""
    request = get_request(request_id)
    if body.expected_request_revision != request["requestRevision"]:
        raise errors.version_conflict(request["requestRevision"])
    if body.expected_input_revision != request["inputRevision"]:
        raise errors.stale_input(request["inputRevision"])

    doc = store.requirement_documents.get(body.requirement_document_id)
    if not doc or doc["requestId"] != request_id:
        raise errors.invalid_request("같은 요청의 요구사항 문서가 아닙니다.")

    existing_id = request.get("activeConfirmationId")
    existing = store.confirmations.get(existing_id) if existing_id else None
    if (
        existing
        and existing["requirementDocumentId"] == doc["id"]
        and existing["inputRevision"] == request["inputRevision"]
    ):
        return existing, False

    markdown_bytes = doc["markdown"].encode("utf-8")
    confirmation_id = new_id("conf")
    version = max([c["version"] for c in store.confirmations_for(request_id)] or [0]) + 1
    confirmation = {
        "id": confirmation_id,
        "requestId": request_id,
        "version": version,
        "inputRevision": request["inputRevision"],
        "requirementDocumentId": doc["id"],
        "documentSnapshot": dict(doc),
        "markdownSha256": hashlib.sha256(markdown_bytes).hexdigest(),
        "confirmedAt": now_iso(),
        "confirmedBy": identity,
        "requestRevision": request["requestRevision"] + 1,
    }
    store.confirmations[confirmation_id] = confirmation

    request["activeConfirmationId"] = confirmation_id
    request["workingRequirementDocumentId"] = doc["id"]
    request["hasUnconfirmedChanges"] = False
    request["requestRevision"] += 1
    request["updatedAt"] = now_iso()
    return confirmation, True


def list_confirmations(request_id: str) -> dict:
    get_request(request_id)
    return {"items": store.confirmations_for(request_id)}


def get_confirmation(request_id: str, confirmation_id: str) -> dict:
    confirmation = store.confirmations.get(confirmation_id)
    if not confirmation or confirmation["requestId"] != request_id:
        raise errors.not_found("확정 묶음을 찾을 수 없습니다.")
    return confirmation
