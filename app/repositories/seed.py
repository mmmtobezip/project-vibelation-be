"""Pre-populates a handful of sample review registrations at process start so
the History screen (REG-02/03) has something to show before anyone has run
the live workflow through this server. Plays the same role FE's local
src/mocks/history.json plays for its own demo — these are display data only,
not real decisions, and reset whenever the process restarts (in-memory store).
"""

import hashlib
from datetime import datetime, timedelta, timezone

from app.integrations import agent_client
from app.repositories.memory import InMemoryStore, new_id

SCENARIOS = [
    {
        "title": "다운로드 센터 다중 선택 개선",
        "legacyReferenceId": "legacy-01",
        "text": "자료를 최대 10개 선택해 한 번에 내려받고 싶습니다.",
        "daysAgo": 14,
    },
    {
        "title": "로그인 2단계 인증 추가",
        "legacyReferenceId": "legacy-01",
        "text": "로그인 시 OTP 입력 단계를 추가해주세요.",
        "daysAgo": 7,
    },
    {
        "title": "알림 센터 읽음 처리 개선",
        "legacyReferenceId": "legacy-01",
        "text": "알림을 모아서 한 번에 읽음 처리하고 싶습니다.",
        "daysAgo": 2,
    },
]

SEED_IDENTITY = {"id": "user-01", "displayName": "운영 담당자"}


def _past_iso(days_ago: int) -> str:
    dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def seed_history(store: InMemoryStore) -> None:
    """Idempotent: no-ops once anything exists in review_registrations,
    whether from a previous seed call or real REG-01 traffic."""
    if store.review_registrations:
        return

    for scenario in SCENARIOS:
        created_at = _past_iso(scenario["daysAgo"])
        legacy = store.legacy_references[scenario["legacyReferenceId"]]

        request_id = new_id("req")
        snapshot_id = new_id("input")
        snapshot = {
            "id": snapshot_id,
            "requestId": request_id,
            "inputRevision": 1,
            "title": scenario["title"],
            "text": scenario["text"],
            "html": "",
            "desiredDueDate": None,
            "attachmentIds": [],
            "createdAt": created_at,
        }
        store.input_snapshots[snapshot_id] = snapshot

        doc_id = new_id("md")
        md_rendered = agent_client.render_requirement_document({"generationNumber": 1}, snapshot)
        document = {
            "id": doc_id,
            "requestId": request_id,
            "generationId": new_id("job"),
            "generationNumber": 1,
            "inputRevision": 1,
            "inputSnapshotId": snapshot_id,
            "title": scenario["title"],
            "markdown": md_rendered["markdown"],
            "formatVersion": md_rendered["formatVersion"],
            "source": "mock",
            "createdAt": created_at,
        }
        store.requirement_documents[doc_id] = document

        confirmation_id = new_id("conf")
        confirmation = {
            "id": confirmation_id,
            "requestId": request_id,
            "version": 1,
            "inputRevision": 1,
            "requirementDocumentId": doc_id,
            "documentSnapshot": dict(document),
            "markdownSha256": hashlib.sha256(document["markdown"].encode("utf-8")).hexdigest(),
            "confirmedAt": created_at,
            "confirmedBy": SEED_IDENTITY,
            "requestRevision": 3,
        }
        store.confirmations[confirmation_id] = confirmation

        analysis_id = new_id("analysis")
        analysis_rendered = agent_client.render_analysis_result(
            {"title": scenario["title"], "legacyVersion": legacy["version"]}
        )
        analysis = {
            "id": analysis_id,
            "requestId": request_id,
            "confirmationId": confirmation_id,
            "requirementDocumentId": doc_id,
            "legacyVersion": legacy["version"],
            "impacts": analysis_rendered["impacts"],
            "totalDays": analysis_rendered["totalDays"],
            "durationDays": analysis_rendered["durationDays"],
            "bufferDays": analysis_rendered["bufferDays"],
            "formatVersion": analysis_rendered["formatVersion"],
            "createdAt": created_at,
        }
        store.analysis_results[analysis_id] = analysis

        report_rendered = agent_client.render_review_report(
            {
                "title": scenario["title"],
                "version": 1,
                "legacyVersion": legacy["version"],
                "requirements": document["markdown"],
                "impacts": analysis["impacts"],
            }
        )
        report_id = new_id("report")
        report = {
            "id": report_id,
            "requestId": request_id,
            "confirmationId": confirmation_id,
            "analysisResultId": analysis_id,
            "markdown": report_rendered["markdown"],
            "formatVersion": report_rendered["formatVersion"],
            "createdAt": created_at,
        }
        store.review_reports[report_id] = report

        # The request itself is seeded as already-registered/settled so it's
        # internally consistent if something follows these IDs (CONF-03, etc).
        store.requests[request_id] = {
            "id": request_id,
            "requestRevision": 3,
            "inputRevision": 1,
            "inputSnapshotId": snapshot_id,
            "title": scenario["title"],
            "text": scenario["text"],
            "html": "",
            "desiredDueDate": None,
            "attachmentIds": [],
            "legacyReferenceId": scenario["legacyReferenceId"],
            "legacyVersion": legacy["version"],
            "workingRequirementDocumentId": doc_id,
            "activeConfirmationId": confirmation_id,
            "hasUnconfirmedChanges": False,
            "latestAnalysisJobId": None,
            "latestAnalysisResultId": analysis_id,
            "latestReportJobId": None,
            "latestReportId": report_id,
            "createdAt": created_at,
            "updatedAt": created_at,
        }

        registration_id = new_id("reg")
        registration = {
            "id": registration_id,
            "requestId": request_id,
            "title": scenario["title"],
            "legacyReferenceId": scenario["legacyReferenceId"],
            "confirmationId": confirmation_id,
            "confirmationVersion": 1,
            "analysisResultId": analysis_id,
            "reportId": report_id,
            "registeredAt": created_at,
            "registeredBy": SEED_IDENTITY,
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
