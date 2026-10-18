"""Process-memory repository for the Mock-data stage.

No PostgreSQL yet (backend-design_v01.md §15 phase 1-2 is later). State lives in
plain dicts guarded by one asyncio.Lock; it resets on restart — fine for a Mock
Agent demo backend, not for production. The interface here is intentionally
narrow (get/put/list) so swapping in SQLAlchemy models later doesn't require
touching the services layer much.
"""

import asyncio
import uuid
from datetime import datetime, timezone


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


class InMemoryStore:
    def __init__(self) -> None:
        self.lock = asyncio.Lock()
        self.requests: dict[str, dict] = {}
        self.input_snapshots: dict[str, dict] = {}
        self.attachments: dict[str, dict] = {}
        self.jobs: dict[str, dict] = {}
        self.requirement_documents: dict[str, dict] = {}
        self.system_mock_artifacts: dict[str, dict] = {}
        self.confirmations: dict[str, dict] = {}
        self.analysis_results: dict[str, dict] = {}
        self.review_reports: dict[str, dict] = {}
        self.review_registrations: dict[str, dict] = {}
        self.idempotency_records: dict[tuple, dict] = {}
        self.job_counters: dict[tuple, int] = {}
        self.legacy_references: dict[str, dict] = {
            "legacy-01": {
                "id": "legacy-01",
                "systemName": "Demo Legacy System",
                "version": "DEMO-2026.10",
                "observedAt": now_iso(),
            }
        }

    async def next_generation_number(self, request_id: str, kind: str) -> int:
        async with self.lock:
            key = (request_id, kind)
            self.job_counters[key] = self.job_counters.get(key, 0) + 1
            return self.job_counters[key]

    def jobs_for(self, request_id: str, kind: str | None = None) -> list[dict]:
        rows = [j for j in self.jobs.values() if j["requestId"] == request_id]
        if kind:
            rows = [j for j in rows if j["kind"] == kind]
        return sorted(rows, key=lambda j: j["createdAt"], reverse=True)

    def documents_for(self, request_id: str) -> list[dict]:
        rows = [d for d in self.requirement_documents.values() if d["requestId"] == request_id]
        return sorted(rows, key=lambda d: d["generationNumber"], reverse=True)

    def confirmations_for(self, request_id: str) -> list[dict]:
        rows = [c for c in self.confirmations.values() if c["requestId"] == request_id]
        return sorted(rows, key=lambda c: c["version"], reverse=True)

    def registrations_for_search(
        self,
        q: str | None,
        legacy_reference_id: str | None,
        registered_from: str | None,
        registered_to: str | None,
    ) -> list[dict]:
        rows = list(self.review_registrations.values())
        if q:
            rows = [r for r in rows if q.lower() in r["title"].lower()]
        if legacy_reference_id:
            rows = [r for r in rows if r["legacyReferenceId"] == legacy_reference_id]
        if registered_from:
            rows = [r for r in rows if r["registeredAt"] >= registered_from]
        if registered_to:
            rows = [r for r in rows if r["registeredAt"] < registered_to]
        return sorted(rows, key=lambda r: r["registeredAt"], reverse=True)


store = InMemoryStore()
