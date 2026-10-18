"""MD-01~05 — api_interface_v06.md §8, §19.1."""

from fastapi import APIRouter, status

from app.schemas.requirements import StartGenerationBody
from app.services import requirements_service

router = APIRouter(tags=["requirements"])


@router.post(
    "/requests/{request_id}/requirement-generations",
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_requirement_generation(request_id: str, body: StartGenerationBody):
    """MD-01 요구사항 문서 생성 (△ backend-design_v01.md §8.1)."""
    return await requirements_service.start_generation(request_id, body)


@router.get("/requests/{request_id}/requirement-generations")
async def list_requirement_generations(request_id: str):
    """MD-02 생성 작업 이력."""
    return requirements_service.list_generations(request_id)


@router.get("/requests/{request_id}/requirement-generations/{job_id}")
async def get_requirement_generation(request_id: str, job_id: str):
    """MD-03 생성 진행 확인."""
    return requirements_service.get_generation(request_id, job_id)


@router.get("/requests/{request_id}/requirement-documents")
async def list_requirement_documents(request_id: str):
    """MD-04 MD 목록."""
    return requirements_service.list_documents(request_id)


@router.get("/requests/{request_id}/requirement-documents/{document_id}")
async def get_requirement_document(request_id: str, document_id: str):
    """MD-05 MD 상세."""
    return requirements_service.get_document(request_id, document_id)
