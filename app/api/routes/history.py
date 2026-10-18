"""REG-01~03 — api_interface_v06.md §12, §19.1 (검토 등록·과거 이력)."""

from typing import Annotated

from fastapi import APIRouter, Header, Query, Response, status

from app.api.dependencies import canonical_hash, check_idempotency, get_current_identity, save_idempotency
from app.schemas.history import RegisterReviewBody
from app.services import history_service

router = APIRouter(tags=["history"])


@router.post("/review-registrations")
async def register_review(
    body: RegisterReviewBody,
    response: Response,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    """REG-01 최종 검토 등록."""
    identity = await get_current_identity()
    route = "/api/review-registrations"
    body_hash = canonical_hash(body.model_dump())
    cached = check_idempotency(identity["id"], "POST", route, idempotency_key, body_hash)
    if cached is not None:
        response.status_code = status.HTTP_200_OK
        return cached
    registration, is_new = history_service.register(body, identity)
    response.status_code = status.HTTP_201_CREATED if is_new else status.HTTP_200_OK
    save_idempotency(identity["id"], "POST", route, idempotency_key, body_hash, registration)
    return registration


@router.get("/review-registrations")
async def search_review_registrations(
    q: str | None = None,
    legacy_reference_id: Annotated[str | None, Query(alias="legacyReferenceId")] = None,
    registered_from: Annotated[str | None, Query(alias="registeredFrom")] = None,
    registered_to: Annotated[str | None, Query(alias="registeredTo")] = None,
    cursor: str | None = None,
    limit: int = 20,
):
    """REG-02 등록 이력 검색."""
    return history_service.search(q, legacy_reference_id, registered_from, registered_to, cursor, limit)


@router.get("/review-registrations/{registration_id}")
async def get_review_registration(registration_id: str):
    """REG-03 등록 당시 상세."""
    return history_service.get_registration(registration_id)
