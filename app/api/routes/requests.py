"""REQ-01~04, REF-01 — api_interface_v06.md §4, §5, §19.1."""

from fastapi import APIRouter, status

from app.api.errors import not_implemented

router = APIRouter(tags=["requests"])


@router.post("/requests", status_code=status.HTTP_201_CREATED)
async def create_request():
    """REQ-01 요청 생성."""
    raise not_implemented("REQ-01 요청 생성")


@router.get("/requests")
async def list_requests():
    """REQ-02 요청 목록."""
    raise not_implemented("REQ-02 요청 목록")


@router.get("/requests/{request_id}")
async def get_request(request_id: str):
    """REQ-03 작업 복원."""
    raise not_implemented("REQ-03 작업 복원")


@router.patch("/requests/{request_id}")
async def patch_request(request_id: str):
    """REQ-04 입력·선택 저장 (△ 최신 개정, backend-design_v01.md §6/§8.1)."""
    raise not_implemented("REQ-04 입력·선택 저장")


@router.get("/legacy-references")
async def list_legacy_references():
    """REF-01 레거시 기준 조회."""
    raise not_implemented("REF-01 레거시 기준 조회")
