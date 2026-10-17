"""CONF-01~03 — api_interface_v06.md §19.3 (MD-only 확정, Mock/협의 필드 없음)."""

from fastapi import APIRouter, status

from app.api.errors import not_implemented

router = APIRouter(tags=["confirmations"])


@router.post(
    "/requests/{request_id}/requirement-confirmations",
    status_code=status.HTTP_201_CREATED,
)
async def confirm_requirement(request_id: str):
    """CONF-01 요구사항 MD 확정 (△ 201/200, backend-design_v01.md §8.2)."""
    raise not_implemented("CONF-01 요구사항 확정")


@router.get("/requests/{request_id}/requirement-confirmations")
async def list_confirmations(request_id: str):
    """CONF-02 확정 이력."""
    raise not_implemented("CONF-02 확정 이력")


@router.get("/requests/{request_id}/requirement-confirmations/{confirmation_id}")
async def get_confirmation(request_id: str, confirmation_id: str):
    """CONF-03 확정 MD 상세 (△)."""
    raise not_implemented("CONF-03 확정 MD 상세")
