"""MOCK-01/03/05 — api_interface_v06.md §19.1~19.2, §21 (MOCK-02/04/06 제외).

주의: MOCK-01의 multipart 필드는 §21이 §19를 덮어쓴다 — file(선택 MD) +
반복 sourceFiles(ZIP) + sourceManifest + legacyVersion + requirementDocumentId.
"""

from fastapi import APIRouter, status

from app.api.errors import not_implemented

router = APIRouter(tags=["system-mock"])


@router.post(
    "/requests/{request_id}/system-mock-generations",
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_system_mock_generation(request_id: str):
    """MOCK-01 예상 화면 생성 (§21 override: file + sourceFiles[] + sourceManifest)."""
    raise not_implemented("MOCK-01 예상 화면 생성")


@router.get("/requests/{request_id}/system-mock-generations/{job_id}")
async def get_system_mock_generation(request_id: str, job_id: str):
    """MOCK-03 생성 진행 확인."""
    raise not_implemented("MOCK-03 생성 진행 확인")


@router.get("/requests/{request_id}/system-mock")
async def get_latest_system_mock(request_id: str):
    """MOCK-05 선택 MD의 최신 예상 화면 (△ 단수 조회, backend-design_v01.md §7)."""
    raise not_implemented("MOCK-05 최신 예상 화면 조회")
