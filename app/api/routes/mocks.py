"""MOCK-01/03/05 — api_interface_v06.md §19.1~19.2, §21 (MOCK-02/04/06 제외).

§21 override: MOCK-01의 multipart는 file(선택 MD) + 반복 sourceFiles(ZIP) +
sourceManifest + legacyVersion + requirementDocumentId.
"""

from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile, status

from app.services import mocks_service

router = APIRouter(tags=["system-mock"])


@router.post(
    "/requests/{request_id}/system-mock-generations",
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_system_mock_generation(
    request_id: str,
    file: Annotated[UploadFile, File()],
    requirement_document_id: Annotated[str, Form(alias="requirementDocumentId")],
    legacy_version: Annotated[str, Form(alias="legacyVersion")],
    source_files: Annotated[list[UploadFile] | None, File(alias="sourceFiles")] = None,
    source_manifest: Annotated[str | None, Form(alias="sourceManifest")] = None,
):
    """MOCK-01 예상 화면 생성 (§21 override)."""
    return await mocks_service.start_mock_generation(
        request_id,
        requirement_document_id,
        legacy_version,
        file,
        source_files or [],
        source_manifest,
    )


@router.get("/requests/{request_id}/system-mock-generations/{job_id}")
async def get_system_mock_generation(request_id: str, job_id: str):
    """MOCK-03 생성 진행 확인."""
    return mocks_service.get_mock_generation(request_id, job_id)


@router.get("/requests/{request_id}/system-mock")
async def get_latest_system_mock(request_id: str):
    """MOCK-05 선택 MD의 최신 예상 화면 (△ 단수 조회, backend-design_v01.md §7)."""
    return mocks_service.get_latest_system_mock(request_id)
