"""Server-side port of the invariants FE currently expresses locally in
src/domain/types.ts (hasConfirmedRequirement, isCurrent, draftFingerprint).
Per backend-design_v01.md §6 and api_interface_v06.md §3/§19.3.
"""


def has_unconfirmed_changes(request: dict, confirmation: dict | None) -> bool:
    if confirmation is None:
        return True
    return (
        confirmation["inputRevision"] != request["inputRevision"]
        or confirmation["requirementDocumentId"] != request.get("workingRequirementDocumentId")
    )


def is_current_confirmation(request: dict, confirmation_id: str | None) -> bool:
    return bool(confirmation_id) and request.get("activeConfirmationId") == confirmation_id


def is_current_analysis(request: dict, analysis: dict) -> bool:
    return (
        analysis["confirmationId"] == request.get("activeConfirmationId")
        and not has_unconfirmed_changes_for(request)
    )


def has_unconfirmed_changes_for(request: dict) -> bool:
    """Convenience for callers that only have the request + its active confirmation id.

    Services look up the confirmation record themselves; this helper exists so
    route handlers can ask the question without re-fetching twice.
    """
    return request.get("hasUnconfirmedChanges", True)


def is_current_report(request: dict, report: dict) -> bool:
    return report["analysisResultId"] == request.get("latestAnalysisResultId")
