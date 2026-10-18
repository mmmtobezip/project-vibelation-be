"""ANA-01~03 — api_interface_v06.md §19.4, §21 (레거시 분석, ZIP 동시 전송 override).

ANA-01 multipart: file(확정 MD) + 반복 sourceFiles(ZIP) + sourceManifest + legacyVersion.
ANA-03 응답은 §21 기준 단순 포맷: impacts/totalDays/durationDays/bufferDays.
"""

from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile, status

from app.services import analyses_service

router = APIRouter(tags=["analysis"])


@router.post(
    "/requests/{request_id}/requirement-confirmations/{confirmation_id}/analysis-jobs",
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_analysis(
    request_id: str,
    confirmation_id: str,
    file: Annotated[UploadFile, File()],
    legacy_version: Annotated[str | None, Form(alias="legacyVersion")] = None,
    source_files: Annotated[list[UploadFile] | None, File(alias="sourceFiles")] = None,
    source_manifest: Annotated[str | None, Form(alias="sourceManifest")] = None,
):
    """ANA-01 레거시 분석 실행 (§21 override)."""
    return await analyses_service.start_analysis(
        request_id,
        confirmation_id,
        legacy_version,
        file,
        source_files or [],
        source_manifest,
    )


@router.get("/analysis-jobs/{job_id}")
async def get_analysis_job(job_id: str):
    """ANA-02 분석 진행 확인."""
    return analyses_service.get_analysis_job(job_id)


@router.get("/analysis-results/{analysis_id}")
async def get_analysis_result(analysis_id: str):
    """ANA-03 영향도 결과 (§21 단순 포맷)."""
    return analyses_service.get_analysis_result(analysis_id)
