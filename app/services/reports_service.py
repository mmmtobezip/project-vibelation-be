"""RPT-01~03 — api_interface_v06.md §12, §19.1."""

from app.api import errors
from app.integrations import agent_client
from app.repositories.memory import new_id, now_iso, store
from app.schemas.reports import StartReportBody
from app.services.common import build_job


async def start_report(body: StartReportBody) -> dict:
    request = store.requests.get(body.request_id)
    if not request:
        raise errors.not_found("요청을 찾을 수 없습니다.")
    confirmation = store.confirmations.get(body.confirmation_id)
    if not confirmation or confirmation["requestId"] != body.request_id:
        raise errors.not_found("확정 묶음을 찾을 수 없습니다.")
    analysis = store.analysis_results.get(body.analysis_result_id)
    if not analysis or analysis["confirmationId"] != body.confirmation_id:
        raise errors.invalid_request("확정 기준과 분석 결과가 일치하지 않습니다.")

    generation_number = await store.next_generation_number(body.request_id, "report")
    job = build_job(
        new_id("job"),
        body.request_id,
        "report",
        generation_number,
        basis={
            "requestId": body.request_id,
            "confirmationId": body.confirmation_id,
            "analysisResultId": body.analysis_result_id,
        },
    )
    store.jobs[job["id"]] = job
    return job


def get_report_job(job_id: str) -> dict:
    job = store.jobs.get(job_id)
    if not job or job["kind"] != "report":
        raise errors.not_found("리포트 생성 작업을 찾을 수 없습니다.")
    if job["status"] in ("succeeded", "failed"):
        return job
    if not agent_client.is_ready(job):
        if job["startedAt"] is None:
            job["startedAt"] = now_iso()
            job["status"] = "running"
        return job

    basis = job["basis"]
    request = store.requests[basis["requestId"]]
    confirmation = store.confirmations[basis["confirmationId"]]
    analysis = store.analysis_results[basis["analysisResultId"]]
    rendered = agent_client.render_review_report(
        {
            "title": request["title"],
            "version": confirmation["version"],
            "legacyVersion": analysis["legacyVersion"],
            "requirements": confirmation["documentSnapshot"]["markdown"],
            "impacts": analysis["impacts"],
        }
    )
    report_id = new_id("report")
    report = {
        "id": report_id,
        "requestId": basis["requestId"],
        "confirmationId": basis["confirmationId"],
        "analysisResultId": basis["analysisResultId"],
        "markdown": rendered["markdown"],
        "formatVersion": rendered["formatVersion"],
        "createdAt": now_iso(),
    }
    store.review_reports[report_id] = report

    request["latestReportJobId"] = job["id"]
    request["latestReportId"] = report_id

    job["status"] = "succeeded"
    job["startedAt"] = job["startedAt"] or job["createdAt"]
    job["finishedAt"] = now_iso()
    job["pollAfterMs"] = 0
    job["result"] = {"type": "reviewReport", "id": report_id}
    return job


def get_report(report_id: str) -> dict:
    report = store.review_reports.get(report_id)
    if not report:
        raise errors.not_found("리포트를 찾을 수 없습니다.")
    return report
