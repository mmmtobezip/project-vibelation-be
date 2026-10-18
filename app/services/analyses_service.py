"""ANA-01~03 — api_interface_v06.md §19.4, §21 (ZIP 동시 전송 override)."""

import json

from fastapi import UploadFile

from app.api import errors
from app.integrations import agent_client
from app.repositories.memory import new_id, now_iso, store
from app.services.common import build_job
from app.services.requests_service import get_request


async def start_analysis(
    request_id: str,
    confirmation_id: str,
    legacy_version: str,
    md_file: UploadFile,
    source_files: list[UploadFile],
    source_manifest: str | None,
) -> dict:
    request = get_request(request_id)
    confirmation = store.confirmations.get(confirmation_id)
    if not confirmation or confirmation["requestId"] != request_id:
        raise errors.not_found("확정 묶음을 찾을 수 없습니다.")

    content = await md_file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise errors.invalid_request("file이 UTF-8 markdown이 아닙니다.")
    if text != confirmation["documentSnapshot"]["markdown"]:
        raise errors.document_mismatch()

    if source_files:
        if not source_manifest:
            raise errors.invalid_request("sourceFiles가 있으면 sourceManifest가 필요합니다.")
        manifest = json.loads(source_manifest)
        if len(manifest) != len(source_files):
            raise errors.invalid_request("sourceFiles 개수와 sourceManifest 길이가 다릅니다.")

    existing = [j for j in store.jobs_for(request_id, "analysis") if j["status"] in ("queued", "running")]
    if existing:
        raise errors.job_already_running(existing[0]["id"])

    generation_number = await store.next_generation_number(request_id, "analysis")
    job = build_job(
        new_id("job"),
        request_id,
        "analysis",
        generation_number,
        basis={
            "confirmationId": confirmation_id,
            "requirementDocumentId": confirmation["requirementDocumentId"],
            "legacyVersion": legacy_version or request["legacyVersion"],
        },
    )
    store.jobs[job["id"]] = job
    return job


def get_analysis_job(job_id: str) -> dict:
    job = store.jobs.get(job_id)
    if not job or job["kind"] != "analysis":
        raise errors.not_found("분석 작업을 찾을 수 없습니다.")
    if job["status"] in ("succeeded", "failed"):
        return job
    if not agent_client.is_ready(job):
        if job["startedAt"] is None:
            job["startedAt"] = now_iso()
            job["status"] = "running"
        return job

    doc = store.requirement_documents.get(job["basis"]["requirementDocumentId"], {})
    rendered = agent_client.render_analysis_result(
        {"title": doc.get("title", ""), "legacyVersion": job["basis"]["legacyVersion"]}
    )
    analysis_id = new_id("analysis")
    analysis = {
        "id": analysis_id,
        "requestId": job["requestId"],
        "confirmationId": job["basis"]["confirmationId"],
        "requirementDocumentId": job["basis"]["requirementDocumentId"],
        "legacyVersion": job["basis"]["legacyVersion"],
        "impacts": rendered["impacts"],
        "totalDays": rendered["totalDays"],
        "durationDays": rendered["durationDays"],
        "bufferDays": rendered["bufferDays"],
        "formatVersion": rendered["formatVersion"],
        "createdAt": now_iso(),
    }
    store.analysis_results[analysis_id] = analysis

    request = store.requests[job["requestId"]]
    request["latestAnalysisJobId"] = job["id"]
    request["latestAnalysisResultId"] = analysis_id

    job["status"] = "succeeded"
    job["startedAt"] = job["startedAt"] or job["createdAt"]
    job["finishedAt"] = now_iso()
    job["pollAfterMs"] = 0
    job["result"] = {"type": "analysisResult", "id": analysis_id}
    return job


def get_analysis_result(analysis_id: str) -> dict:
    analysis = store.analysis_results.get(analysis_id)
    if not analysis:
        raise errors.not_found("분석 결과를 찾을 수 없습니다.")
    return analysis
