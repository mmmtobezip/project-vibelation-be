"""REG-01~03 — api_interface_v06.md §12, §19.1."""

from app.api import errors
from app.repositories.memory import new_id, now_iso, store
from app.schemas.history import RegisterReviewBody
from app.services.common import paginate


def register(body: RegisterReviewBody, identity: dict) -> tuple[dict, bool]:
    request = store.requests.get(body.request_id)
    if not request:
        raise errors.not_found("요청을 찾을 수 없습니다.")
    confirmation = store.confirmations.get(body.confirmation_id)
    if not confirmation or confirmation["requestId"] != body.request_id:
        raise errors.not_found("확정 묶음을 찾을 수 없습니다.")
    analysis = store.analysis_results.get(body.analysis_result_id)
    if not analysis or analysis["confirmationId"] != body.confirmation_id:
        raise errors.invalid_request("확정 기준과 분석 결과가 일치하지 않습니다.")
    report = store.review_reports.get(body.report_id)
    if not report or report["analysisResultId"] != body.analysis_result_id:
        raise errors.invalid_request("분석 결과와 리포트가 일치하지 않습니다.")
    if not (body.review_checks.scope_reviewed and body.review_checks.estimate_reviewed):
        raise errors.review_checks_required()

    for existing in store.review_registrations.values():
        if (
            existing["requestId"] == body.request_id
            and existing["confirmationId"] == body.confirmation_id
            and existing["analysisResultId"] == body.analysis_result_id
            and existing["reportId"] == body.report_id
        ):
            return existing, False

    registration_id = new_id("reg")
    registration = {
        "id": registration_id,
        "requestId": body.request_id,
        "title": request["title"],
        "legacyReferenceId": request["legacyReferenceId"],
        "confirmationId": body.confirmation_id,
        "confirmationVersion": confirmation["version"],
        "analysisResultId": body.analysis_result_id,
        "reportId": body.report_id,
        "registeredAt": now_iso(),
        "registeredBy": identity,
        "estimateSummary": {
            "totalDays": analysis["totalDays"],
            "durationDays": analysis["durationDays"],
            "bufferDays": analysis["bufferDays"],
        },
        "confirmationSnapshot": dict(confirmation),
        "analysisSnapshot": dict(analysis),
        "reportSnapshot": dict(report),
    }
    store.review_registrations[registration_id] = registration
    return registration, True


def search(
    q: str | None,
    legacy_reference_id: str | None,
    registered_from: str | None,
    registered_to: str | None,
    cursor: str | None,
    limit: int,
) -> dict:
    rows = store.registrations_for_search(q, legacy_reference_id, registered_from, registered_to)
    page, next_cursor = paginate(rows, cursor, limit)
    items = [
        {
            "id": r["id"],
            "title": r["title"],
            "confirmationVersion": r["confirmationVersion"],
            "registeredAt": r["registeredAt"],
            "registeredBy": r["registeredBy"],
            "estimateSummary": r["estimateSummary"],
        }
        for r in page
    ]
    return {"items": items, "nextCursor": next_cursor}


def get_registration(registration_id: str) -> dict:
    registration = store.review_registrations.get(registration_id)
    if not registration:
        raise errors.not_found("등록 이력을 찾을 수 없습니다.")
    return registration
