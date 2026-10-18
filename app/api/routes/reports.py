"""RPT-01~03 — api_interface_v06.md §19.1, §12."""

from fastapi import APIRouter, Header, status

from app.api.dependencies import canonical_hash, check_idempotency, get_current_identity, save_idempotency
from app.schemas.reports import StartReportBody
from app.services import reports_service

router = APIRouter(tags=["reports"])


@router.post("/review-reports", status_code=status.HTTP_202_ACCEPTED)
async def start_report(
    body: StartReportBody,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    """RPT-01 최종 검토 리포트 생성."""
    identity = await get_current_identity()
    route = "/api/review-reports"
    body_hash = canonical_hash(body.model_dump())
    cached = check_idempotency(identity["id"], "POST", route, idempotency_key, body_hash)
    if cached is not None:
        return cached
    result = await reports_service.start_report(body)
    save_idempotency(identity["id"], "POST", route, idempotency_key, body_hash, result)
    return result


@router.get("/report-jobs/{job_id}")
async def get_report_job(job_id: str):
    """RPT-02 리포트 생성 진행 확인."""
    return reports_service.get_report_job(job_id)


@router.get("/review-reports/{report_id}")
async def get_report(report_id: str):
    """RPT-03 최종 검토 리포트 상세."""
    return reports_service.get_report(report_id)
