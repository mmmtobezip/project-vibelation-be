from app.repositories.memory import now_iso


def build_job(
    job_id: str,
    request_id: str,
    kind: str,
    generation_number: int,
    basis: dict,
) -> dict:
    return {
        "id": job_id,
        "requestId": request_id,
        "kind": kind,
        "status": "queued",
        "generationNumber": generation_number,
        "basis": basis,
        "result": None,
        "error": None,
        "createdAt": now_iso(),
        "startedAt": None,
        "finishedAt": None,
        "pollAfterMs": 500,
    }


def paginate(items: list[dict], cursor: str | None, limit: int) -> tuple[list[dict], str | None]:
    start = 0
    if cursor:
        for i, item in enumerate(items):
            if item["id"] == cursor:
                start = i + 1
                break
    page = items[start : start + limit]
    next_cursor = page[-1]["id"] if start + limit < len(items) else None
    return page, next_cursor
