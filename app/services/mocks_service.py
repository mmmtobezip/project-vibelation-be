"""MOCK-01/03/05 — api_interface_v06.md §19.2, §21 (ZIP 동시 전송 override)."""

import json

from fastapi import UploadFile

from app.api import errors
from app.integrations import agent_client
from app.repositories.memory import new_id, now_iso, store
from app.services.common import build_job
from app.services.requests_service import get_request


async def _validate_manifest(source_files: list[UploadFile], source_manifest: str | None) -> list[dict]:
    if not source_files:
        return []
    if not source_manifest:
        raise errors.invalid_request("sourceFiles가 있으면 sourceManifest가 필요합니다.")
    try:
        manifest = json.loads(source_manifest)
    except ValueError:
        raise errors.invalid_request("sourceManifest가 유효한 JSON이 아닙니다.")
    if len(manifest) != len(source_files):
        raise errors.invalid_request("sourceFiles 개수와 sourceManifest 길이가 다릅니다.")
    return manifest


async def start_mock_generation(
    request_id: str,
    requirement_document_id: str,
    legacy_version: str,
    md_file: UploadFile,
    source_files: list[UploadFile],
    source_manifest: str | None,
) -> dict:
    get_request(request_id)
    doc = store.requirement_documents.get(requirement_document_id)
    if not doc or doc["requestId"] != request_id:
        raise errors.invalid_request("같은 요청의 요구사항 문서가 아닙니다.")
    if not (md_file.filename or "").endswith(".md"):
        raise errors.invalid_request("file은 .md 여야 합니다.")
    await _validate_manifest(source_files, source_manifest)

    existing = [j for j in store.jobs_for(request_id, "systemMock") if j["status"] in ("queued", "running")]
    if existing:
        raise errors.job_already_running(existing[0]["id"])

    generation_number = await store.next_generation_number(request_id, "systemMock")
    job = build_job(
        new_id("job"),
        request_id,
        "systemMock",
        generation_number,
        basis={"requirementDocumentId": requirement_document_id, "legacyVersion": legacy_version},
    )
    store.jobs[job["id"]] = job
    return job


def get_mock_generation(request_id: str, job_id: str) -> dict:
    job = store.jobs.get(job_id)
    if not job or job["requestId"] != request_id or job["kind"] != "systemMock":
        raise errors.not_found("예상 화면 생성 작업을 찾을 수 없습니다.")
    if job["status"] in ("succeeded", "failed"):
        return job
    if not agent_client.is_ready(job):
        if job["startedAt"] is None:
            job["startedAt"] = now_iso()
            job["status"] = "running"
        return job

    rendered = agent_client.render_system_mock()
    artifact_id = new_id("screen")
    artifact = {
        "id": artifact_id,
        "requestId": request_id,
        "requirementDocumentId": job["basis"]["requirementDocumentId"],
        "legacyVersion": job["basis"]["legacyVersion"],
        "html": rendered["html"],
        "formatVersion": rendered["formatVersion"],
        "createdAt": now_iso(),
    }
    store.system_mock_artifacts[artifact_id] = artifact
    job["status"] = "succeeded"
    job["startedAt"] = job["startedAt"] or job["createdAt"]
    job["finishedAt"] = now_iso()
    job["pollAfterMs"] = 0
    job["result"] = {"type": "systemMock", "id": artifact_id}
    return job


def get_latest_system_mock(request_id: str) -> dict:
    request = get_request(request_id)
    doc_id = request.get("workingRequirementDocumentId")
    candidates = [
        a
        for a in store.system_mock_artifacts.values()
        if a["requestId"] == request_id and a["requirementDocumentId"] == doc_id
    ]
    if not candidates:
        raise errors.not_found("선택 MD의 예상 화면이 아직 없습니다.")
    return sorted(candidates, key=lambda a: a["createdAt"], reverse=True)[0]
