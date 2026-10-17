"""REG-01~03 — api_interface_v06.md §12, §19.1 (검토 등록·과거 이력)."""

from fastapi import APIRouter, status

from app.api.errors import not_implemented

router = APIRouter(tags=["history"])


@router.post("/review-registrations", status_code=status.HTTP_201_CREATED)
async def register_review():
    """REG-01 최종 검토 등록."""
    raise not_implemented("REG-01 검토 등록")


@router.get("/review-registrations")
async def search_review_registrations():
    """REG-02 등록 이력 검색 (q, legacyReferenceId, registeredFrom/To, cursor, limit)."""
    raise not_implemented("REG-02 등록 이력 검색")


@router.get("/review-registrations/{registration_id}")
async def get_review_registration(registration_id: str):
    """REG-03 등록 당시 상세."""
    raise not_implemented("REG-03 등록 당시 상세")
