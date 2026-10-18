"""Mock Agent response rendering.

For this Mock-data stage there is no real Agent HTTP service, so "dispatch" is
simulated the same way FE's local mocks already do it
(src/services/requirements.ts / systemMocks.ts): a Job becomes ready once
RUNNING_THRESHOLD_MS has elapsed since its createdAt, and the result is
rendered deterministically from the repo-root mocks/*.json fixtures by
substituting {{placeholder}} tokens.

When a real Agent server exists (backend-design_v01.md §9 internal
operationId/taskId contract), this module's render_* functions become the
MockAgentClient implementation behind the same AgentClient Protocol an
HttpAgentClient would also implement.
"""

import json
from datetime import datetime
from pathlib import Path

MOCKS_DIR = Path(__file__).resolve().parents[2] / "mocks"
RUNNING_THRESHOLD_MS = 900


def _load(name: str) -> dict:
    with open(MOCKS_DIR / f"{name}.json", encoding="utf-8") as f:
        return json.load(f)


def render_template(template: str, values: dict) -> str:
    out = template
    for key, value in values.items():
        out = out.replace("{{" + key + "}}", str(value))
    return out


def elapsed_ms(created_at_iso: str) -> float:
    created = datetime.fromisoformat(created_at_iso.replace("Z", "+00:00"))
    now = datetime.now(created.tzinfo)
    return (now - created).total_seconds() * 1000


def is_ready(job: dict) -> bool:
    return elapsed_ms(job["createdAt"]) >= RUNNING_THRESHOLD_MS


def render_requirement_document(job: dict, input_snapshot: dict) -> dict:
    fixture = _load("requirement-document")
    markdown = render_template(
        fixture["markdownTemplate"],
        {
            "generationNumber": job["generationNumber"],
            "title": input_snapshot["title"],
            "inputRevision": input_snapshot["inputRevision"],
            "text": input_snapshot.get("text") or "(미입력)",
            "html": input_snapshot.get("html") or "<!-- 미입력 -->",
            "attachments": "\n".join(
                f"- {name}" for name in input_snapshot.get("attachmentNames", [])
            )
            or "(없음)",
        },
    )
    return {"markdown": markdown, "formatVersion": fixture["formatVersion"]}


def render_system_mock() -> dict:
    fixture = _load("system-mock")
    return {"html": fixture["html"], "formatVersion": fixture["formatVersion"]}


def render_analysis_result() -> dict:
    """api_interface_v06.md §21 shape: impacts/totalDays/durationDays/bufferDays."""
    fixture = _load("analysis-result")
    return {
        "impacts": fixture["impacts"],
        "totalDays": fixture["totalDays"],
        "durationDays": fixture["durationDays"],
        "bufferDays": fixture["bufferDays"],
        "formatVersion": fixture["formatVersion"],
    }


def render_review_report(context: dict) -> dict:
    fixture = _load("review-report")
    impacts_md = "\n".join(
        render_template(fixture["impactTemplate"], impact) for impact in context["impacts"]
    )
    markdown = render_template(
        fixture["markdownTemplate"],
        {
            "title": context["title"],
            "version": context["version"],
            "legacyVersion": context["legacyVersion"],
            "requirements": context["requirements"],
            "impacts": impacts_md,
        },
    )
    return {"markdown": markdown, "formatVersion": fixture["formatVersion"]}
