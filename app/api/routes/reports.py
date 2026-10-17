"""RPT-01~03 — api_interface_v06.md §19.1, §12."""

from fastapi import APIRouter, status

from app.api.errors import not_implemented

router = APIRouter(tags=["reports"])


@router.post("/review-reports", status_code=status.HTTP_202_ACCEPTED)
async def start_report():
    """RPT-01 최종 검토 리포트 생성."""
    raise not_implemented("RPT-01 리포트 생성")


@router.get("/report-jobs/{job_id}")
async def get_report_job(job_id: str):
    """RPT-02 리포트 생성 진행 확인."""
    raise not_implemented("RPT-02 리포트 생성 진행 확인")


@router.get("/review-reports/{report_id}")
async def get_report(report_id: str):
    """RPT-03 최종 검토 리포트 상세."""
    raise not_implemented("RPT-03 리포트 상세")
