"""REQ-01~04, REF-01 — api_interface_v06.md §4, §5, §19.1."""

from fastapi import APIRouter, status

from app.schemas.requests import CreateRequestBody, PatchRequestBody
from app.services import requests_service

router = APIRouter(tags=["requests"])


@router.post("/requests", status_code=status.HTTP_201_CREATED)
async def create_request(body: CreateRequestBody):
    """REQ-01 요청 생성."""
    return requests_service.create_request(body.title, body.legacy_reference_id)


@router.get("/requests")
async def list_requests():
    """REQ-02 요청 목록."""
    return requests_service.list_requests()


@router.get("/requests/{request_id}")
async def get_request(request_id: str):
    """REQ-03 작업 복원."""
    return requests_service.get_request(request_id)


@router.patch("/requests/{request_id}")
async def patch_request(request_id: str, body: PatchRequestBody):
    """REQ-04 입력·선택 저장 (△ 최신 개정, backend-design_v01.md §6/§8.1)."""
    return requests_service.patch_request(request_id, body)


@router.get("/legacy-references")
async def list_legacy_references():
    """REF-01 레거시 기준 조회."""
    return requests_service.list_legacy_references()
