"""CONF-01~03 — api_interface_v06.md §19.3 (MD-only 확정, Mock/협의 필드 없음)."""

from fastapi import APIRouter, Header, Response, status

from app.api.dependencies import canonical_hash, check_idempotency, get_current_identity, save_idempotency
from app.schemas.confirmations import ConfirmBody
from app.services import confirmations_service

router = APIRouter(tags=["confirmations"])


@router.post("/requests/{request_id}/requirement-confirmations")
async def confirm_requirement(
    request_id: str,
    body: ConfirmBody,
    response: Response,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    """CONF-01 요구사항 MD 확정 (△ 201/200, backend-design_v01.md §8.2)."""
    identity = await get_current_identity()
    route = f"/api/requests/{request_id}/requirement-confirmations"
    body_hash = canonical_hash(body.model_dump())
    cached = check_idempotency(identity["id"], "POST", route, idempotency_key, body_hash)
    if cached is not None:
        response.status_code = status.HTTP_200_OK
        return cached
    confirmation, is_new = confirmations_service.confirm(request_id, body, identity)
    response.status_code = status.HTTP_201_CREATED if is_new else status.HTTP_200_OK
    save_idempotency(identity["id"], "POST", route, idempotency_key, body_hash, confirmation)
    return confirmation


@router.get("/requests/{request_id}/requirement-confirmations")
async def list_confirmations(request_id: str):
    """CONF-02 확정 이력."""
    return confirmations_service.list_confirmations(request_id)


@router.get("/requests/{request_id}/requirement-confirmations/{confirmation_id}")
async def get_confirmation(request_id: str, confirmation_id: str):
    """CONF-03 확정 MD 상세 (△)."""
    return confirmations_service.get_confirmation(request_id, confirmation_id)
