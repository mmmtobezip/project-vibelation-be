"""Error-contract tests per api_interface_v06.md §13 / backend-design_v01.md §11."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from tests.conftest import confirmed_request, generated_document, poll


@pytest.mark.asyncio
async def test_job_already_running_blocks_concurrent_mock_generation():
    """Regression test for a gap found while writing the MOCK API test report:
    mocks_service.start_mock_generation was missing the same queued/running
    guard requirements_service/analyses_service already had."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api") as client:
        ctx = await generated_document(client)
        files = {"file": ("requirements.md", ctx["document"]["markdown"].encode("utf-8"), "text/markdown")}
        data = {"requirementDocumentId": ctx["document"]["id"], "legacyVersion": "DEMO-2026.10"}

        first = await client.post(f"/requests/{ctx['requestId']}/system-mock-generations", data=data, files=files)
        second = await client.post(f"/requests/{ctx['requestId']}/system-mock-generations", data=data, files=files)

        assert first.status_code == 202
        assert second.status_code == 409
        error = second.json()["detail"]["error"]
        assert error["code"] == "JOB_ALREADY_RUNNING"
        assert error["details"]["jobId"] == first.json()["id"]


@pytest.mark.asyncio
async def test_version_conflict_on_stale_patch():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api") as client:
        created = (await client.post("/requests", json={"title": "A", "legacyReferenceId": "legacy-01"})).json()

        response = await client.patch(
            f"/requests/{created['id']}",
            json={"expectedRequestRevision": 999, "input": {"title": "A", "text": "x", "html": "", "desiredDueDate": None, "attachmentIds": []}},
        )
        assert response.status_code == 409
        body = response.json()["detail"]["error"]
        assert body["code"] == "VERSION_CONFLICT"
        assert body["details"]["currentRequestRevision"] == created["requestRevision"]


@pytest.mark.asyncio
async def test_stale_input_on_generation_with_wrong_revision():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api") as client:
        created = (await client.post("/requests", json={"title": "B", "legacyReferenceId": "legacy-01"})).json()

        response = await client.post(
            f"/requests/{created['id']}/requirement-generations",
            json={"inputSnapshotId": created["inputSnapshotId"], "expectedInputRevision": 999},
        )
        assert response.status_code == 409
        assert response.json()["detail"]["error"]["code"] == "STALE_INPUT"


@pytest.mark.asyncio
async def test_job_already_running_blocks_concurrent_generation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api") as client:
        created = (await client.post("/requests", json={"title": "C", "legacyReferenceId": "legacy-01"})).json()
        body = {"inputSnapshotId": created["inputSnapshotId"], "expectedInputRevision": created["inputRevision"]}

        first = await client.post(f"/requests/{created['id']}/requirement-generations", json=body)
        second = await client.post(f"/requests/{created['id']}/requirement-generations", json=body)

        assert first.status_code == 202
        assert second.status_code == 409
        error = second.json()["detail"]["error"]
        assert error["code"] == "JOB_ALREADY_RUNNING"
        assert error["details"]["jobId"] == first.json()["id"]


@pytest.mark.asyncio
async def test_attachment_not_ready_rejects_unknown_attachment_id():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api") as client:
        created = (await client.post("/requests", json={"title": "D", "legacyReferenceId": "legacy-01"})).json()

        response = await client.patch(
            f"/requests/{created['id']}",
            json={
                "expectedRequestRevision": 1,
                "input": {"title": "D", "text": "x", "html": "", "desiredDueDate": None, "attachmentIds": ["file-does-not-exist"]},
            },
        )
        assert response.status_code == 422
        assert response.json()["detail"]["error"]["code"] == "ATTACHMENT_NOT_READY"


@pytest.mark.asyncio
async def test_document_mismatch_on_tampered_markdown():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api") as client:
        ctx = await confirmed_request(client)

        response = await client.post(
            f"/requests/{ctx['requestId']}/requirement-confirmations/{ctx['confirmation']['id']}/analysis-jobs",
            files={"file": ("requirements.md", b"# tampered content", "text/markdown")},
        )
        assert response.status_code == 409
        assert response.json()["detail"]["error"]["code"] == "DOCUMENT_MISMATCH"


@pytest.mark.asyncio
async def test_review_checks_required_when_not_both_true():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api") as client:
        ctx = await confirmed_request(client)

        files = {"file": ("requirements.md", ctx["confirmation"]["documentSnapshot"]["markdown"].encode("utf-8"), "text/markdown")}
        analysis_job = (
            await client.post(
                f"/requests/{ctx['requestId']}/requirement-confirmations/{ctx['confirmation']['id']}/analysis-jobs",
                files=files,
            )
        ).json()
        analysis_job = await poll(client, f"/analysis-jobs/{analysis_job['id']}")
        analysis_id = analysis_job["result"]["id"]

        report_job = (
            await client.post(
                "/review-reports",
                json={
                    "requestId": ctx["requestId"],
                    "confirmationId": ctx["confirmation"]["id"],
                    "analysisResultId": analysis_id,
                },
            )
        ).json()
        report_job = await poll(client, f"/report-jobs/{report_job['id']}")
        report_id = report_job["result"]["id"]

        response = await client.post(
            "/review-registrations",
            json={
                "requestId": ctx["requestId"],
                "confirmationId": ctx["confirmation"]["id"],
                "analysisResultId": analysis_id,
                "reportId": report_id,
                "reviewChecks": {"scopeReviewed": True, "estimateReviewed": False},
            },
        )
        assert response.status_code == 422
        assert response.json()["detail"]["error"]["code"] == "REVIEW_CHECKS_REQUIRED"


@pytest.mark.asyncio
async def test_not_found_for_unknown_request():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api") as client:
        response = await client.get("/requests/does-not-exist")
        assert response.status_code == 404
        assert response.json()["detail"]["error"]["code"] == "NOT_FOUND"
