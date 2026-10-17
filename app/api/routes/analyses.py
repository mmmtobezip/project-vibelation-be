"""ANA-01~03 — api_interface_v06.md §19.4, §21 (레거시 분석, ZIP 동시 전송 override).

ANA-01 multipart: file(확정 MD) + 반복 sourceFiles(ZIP) + sourceManifest + legacyVersion.
ANA-03 응답은 §21 기준 단순 포맷: impacts/totalDays/durationDays/bufferDays
(backend-design_v01.md §8.4의 resources/evidence/estimate 포맷보다 §21이 최신 우선).
"""

from fastapi import APIRouter, status

from app.api.errors import not_implemented

router = APIRouter(tags=["analysis"])


@router.post(
    "/requests/{request_id}/requirement-confirmations/{confirmation_id}/analysis-jobs",
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_analysis(request_id: str, confirmation_id: str):
    """ANA-01 레거시 분석 실행 (§21 override: file + sourceFiles[] + sourceManifest)."""
    raise not_implemented("ANA-01 분석 실행")


@router.get("/analysis-jobs/{job_id}")
async def get_analysis_job(job_id: str):
    """ANA-02 분석 진행 확인."""
    raise not_implemented("ANA-02 분석 진행 확인")


@router.get("/analysis-results/{analysis_id}")
async def get_analysis_result(analysis_id: str):
    """ANA-03 영향도 결과 (§21 단순 포맷: impacts/totalDays/durationDays/bufferDays)."""
    raise not_implemented("ANA-03 영향도 결과")
