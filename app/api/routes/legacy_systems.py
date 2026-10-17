"""SYS-01~03 — api_interface_v06.md §20.1~20.2 (레거시 소스 ZIP 관리, 미구현 선언 영역)."""

from fastapi import APIRouter, status

from app.api.errors import not_implemented

router = APIRouter(tags=["legacy-systems"])


@router.post("/legacy-systems", status_code=status.HTTP_201_CREATED)
async def create_legacy_system():
    """SYS-01 시스템명·설명 초안 등록."""
    raise not_implemented("SYS-01 시스템 초안 등록")


@router.get("/legacy-systems/{system_id}")
async def get_legacy_system(system_id: str):
    """SYS-02 시스템·초안 패키지·활성 기준 복원."""
    raise not_implemented("SYS-02 시스템 상세 조회")


@router.patch("/legacy-systems/{system_id}")
async def patch_legacy_system(system_id: str):
    """SYS-03 초안 메타 수정 또는 적용(action=apply)."""
    raise not_implemented("SYS-03 시스템 수정/적용")
