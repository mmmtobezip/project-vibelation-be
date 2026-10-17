"""MD-01~05 — api_interface_v06.md §8, §19.1 (MOCK-02/04/06 제외 원칙과 동일하게 반복 생성 유지)."""

from fastapi import APIRouter, status

from app.api.errors import not_implemented

router = APIRouter(tags=["requirements"])


@router.post(
    "/requests/{request_id}/requirement-generations",
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_requirement_generation(request_id: str):
    """MD-01 요구사항 문서 생성 (△ backend-design_v01.md §8.1)."""
    raise not_implemented("MD-01 요구사항 문서 생성")


@router.get("/requests/{request_id}/requirement-generations")
async def list_requirement_generations(request_id: str):
    """MD-02 생성 작업 이력."""
    raise not_implemented("MD-02 생성 작업 이력")


@router.get("/requests/{request_id}/requirement-generations/{job_id}")
async def get_requirement_generation(request_id: str, job_id: str):
    """MD-03 생성 진행 확인."""
    raise not_implemented("MD-03 생성 진행 확인")


@router.get("/requests/{request_id}/requirement-documents")
async def list_requirement_documents(request_id: str):
    """MD-04 MD 목록."""
    raise not_implemented("MD-04 MD 목록")


@router.get("/requests/{request_id}/requirement-documents/{document_id}")
async def get_requirement_document(request_id: str, document_id: str):
    """MD-05 MD 상세."""
    raise not_implemented("MD-05 MD 상세")
