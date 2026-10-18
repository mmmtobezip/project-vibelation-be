"""REQ-01~04, REF-01 — api_interface_v06.md §5, §19.1."""

from app.api import errors
from app.domain.rules import has_unconfirmed_changes
from app.repositories.memory import new_id, now_iso, store
from app.schemas.requests import PatchRequestBody


def _snapshot_from(request_id: str, revision: int, title: str, text: str, html: str, due_date, attachment_ids):
    snapshot = {
        "id": new_id("input"),
        "requestId": request_id,
        "inputRevision": revision,
        "title": title,
        "text": text,
        "html": html,
        "desiredDueDate": due_date,
        "attachmentIds": list(attachment_ids),
        "createdAt": now_iso(),
    }
    store.input_snapshots[snapshot["id"]] = snapshot
    return snapshot


def create_request(title: str, legacy_reference_id: str) -> dict:
    legacy = store.legacy_references.get(legacy_reference_id)
    if not legacy:
        raise errors.invalid_request("존재하지 않는 레거시 기준입니다.")
    request_id = new_id("req")
    snapshot = _snapshot_from(request_id, 1, title, "", "", None, [])
    request = {
        "id": request_id,
        "requestRevision": 1,
        "inputRevision": 1,
        "inputSnapshotId": snapshot["id"],
        "title": title,
        "text": "",
        "html": "",
        "desiredDueDate": None,
        "attachmentIds": [],
        "legacyReferenceId": legacy_reference_id,
        "legacyVersion": legacy["version"],
        "workingRequirementDocumentId": None,
        "activeConfirmationId": None,
        "hasUnconfirmedChanges": True,
        "latestAnalysisJobId": None,
        "latestAnalysisResultId": None,
        "latestReportJobId": None,
        "latestReportId": None,
        "createdAt": now_iso(),
        "updatedAt": now_iso(),
    }
    store.requests[request_id] = request
    return request


def list_requests() -> dict:
    items = sorted(store.requests.values(), key=lambda r: r["createdAt"], reverse=True)
    return {"items": items, "nextCursor": None}


def get_request(request_id: str) -> dict:
    request = store.requests.get(request_id)
    if not request:
        raise errors.not_found("요청을 찾을 수 없습니다.")
    return request


def patch_request(request_id: str, body: PatchRequestBody) -> dict:
    request = get_request(request_id)
    if body.expected_request_revision != request["requestRevision"]:
        raise errors.version_conflict(request["requestRevision"])

    changed = False

    if body.input is not None:
        for attachment_id in body.input.attachment_ids:
            attachment = store.attachments.get(attachment_id)
            if not attachment or attachment["requestId"] != request_id or not attachment["usableForGeneration"]:
                raise errors.attachment_not_ready()
        next_revision = request["inputRevision"] + 1
        snapshot = _snapshot_from(
            request_id,
            next_revision,
            body.input.title,
            body.input.text,
            body.input.html,
            body.input.desired_due_date,
            body.input.attachment_ids,
        )
        request["inputRevision"] = next_revision
        request["inputSnapshotId"] = snapshot["id"]
        request["title"] = body.input.title
        request["text"] = body.input.text
        request["html"] = body.input.html
        request["desiredDueDate"] = body.input.desired_due_date
        request["attachmentIds"] = list(body.input.attachment_ids)
        changed = True

    if "working_requirement_document_id" in body.model_fields_set:
        doc_id = body.working_requirement_document_id
        if doc_id is not None:
            doc = store.requirement_documents.get(doc_id)
            if not doc or doc["requestId"] != request_id:
                raise errors.invalid_request("같은 요청의 요구사항 문서가 아닙니다.")
        request["workingRequirementDocumentId"] = doc_id
        changed = True

    if changed:
        confirmation = store.confirmations.get(request.get("activeConfirmationId"))
        request["hasUnconfirmedChanges"] = has_unconfirmed_changes(request, confirmation)
        request["requestRevision"] += 1
        request["updatedAt"] = now_iso()

    return request


def list_legacy_references() -> dict:
    return {"items": list(store.legacy_references.values())}
