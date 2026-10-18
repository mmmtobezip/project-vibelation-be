"""MD-01~05 — api_interface_v06.md §8, §19.1."""

from app.api import errors
from app.integrations import agent_client
from app.repositories.memory import new_id, now_iso, store
from app.schemas.requirements import StartGenerationBody
from app.services.common import build_job
from app.services.requests_service import get_request


async def start_generation(request_id: str, body: StartGenerationBody) -> dict:
    request = get_request(request_id)
    if (
        body.input_snapshot_id != request["inputSnapshotId"]
        or body.expected_input_revision != request["inputRevision"]
    ):
        raise errors.stale_input(request["inputRevision"])

    existing = [j for j in store.jobs_for(request_id, "requirement") if j["status"] in ("queued", "running")]
    if existing:
        raise errors.job_already_running(existing[0]["id"])

    generation_number = await store.next_generation_number(request_id, "requirement")
    job = build_job(
        new_id("job"),
        request_id,
        "requirement",
        generation_number,
        basis={"inputSnapshotId": body.input_snapshot_id, "inputRevision": body.expected_input_revision},
    )
    store.jobs[job["id"]] = job
    return job


def list_generations(request_id: str) -> dict:
    get_request(request_id)
    return {"items": store.jobs_for(request_id, "requirement")}


def get_generation(request_id: str, job_id: str) -> dict:
    job = store.jobs.get(job_id)
    if not job or job["requestId"] != request_id or job["kind"] != "requirement":
        raise errors.not_found("생성 작업을 찾을 수 없습니다.")
    if job["status"] in ("succeeded", "failed"):
        return job
    if not agent_client.is_ready(job):
        if job["startedAt"] is None:
            job["startedAt"] = now_iso()
            job["status"] = "running"
        return job

    snapshot = store.input_snapshots[job["basis"]["inputSnapshotId"]]
    rendered = agent_client.render_requirement_document(job, snapshot)
    document_id = new_id("md")
    document = {
        "id": document_id,
        "requestId": request_id,
        "generationId": job["id"],
        "generationNumber": job["generationNumber"],
        "inputRevision": snapshot["inputRevision"],
        "inputSnapshotId": snapshot["id"],
        "title": snapshot["title"],
        "markdown": rendered["markdown"],
        "formatVersion": rendered["formatVersion"],
        "source": "mock",
        "createdAt": now_iso(),
    }
    store.requirement_documents[document_id] = document
    job["status"] = "succeeded"
    job["startedAt"] = job["startedAt"] or job["createdAt"]
    job["finishedAt"] = now_iso()
    job["pollAfterMs"] = 0
    job["result"] = {"type": "requirementDocument", "id": document_id}
    return job


def list_documents(request_id: str) -> dict:
    get_request(request_id)
    items = [
        {k: v for k, v in doc.items() if k not in ("markdown",)}
        for doc in store.documents_for(request_id)
    ]
    return {"items": items}


def get_document(request_id: str, document_id: str) -> dict:
    doc = store.requirement_documents.get(document_id)
    if not doc or doc["requestId"] != request_id:
        raise errors.not_found("요구사항 문서를 찾을 수 없습니다.")
    return doc
