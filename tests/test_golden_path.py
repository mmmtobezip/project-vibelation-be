"""Happy-path contract test: REQ -> MD -> CONF -> ANA -> RPT -> REG.

Exercises the Mock Agent end to end (backend-design_v01.md §15 "필수 테스트" 1번
항목) without a database — the in-memory store resets per test process.
"""

import asyncio
import json

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


async def _poll(client: AsyncClient, url: str) -> dict:
    for _ in range(20):
        response = await client.get(url)
        assert response.status_code == 200
        job = response.json()
        if job["status"] in ("succeeded", "failed"):
            return job
        await asyncio.sleep(0.2)
    raise AssertionError(f"job at {url} never finished: {job}")


@pytest.mark.asyncio
async def test_golden_path():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api") as client:
        created = (
            await client.post("/requests", json={"title": "다운로드 센터 개선", "legacyReferenceId": "legacy-01"})
        ).json()
        assert created["requestRevision"] == 1
        request_id = created["id"]

        patched = (
            await client.patch(
                f"/requests/{request_id}",
                json={
                    "expectedRequestRevision": 1,
                    "input": {
                        "title": "다운로드 센터 개선",
                        "text": "최대 10개 파일을 선택하고 싶습니다.",
                        "html": "",
                        "desiredDueDate": None,
                        "attachmentIds": [],
                    },
                },
            )
        ).json()
        assert patched["inputRevision"] == 2
        assert patched["requestRevision"] == 2

        gen_job = (
            await client.post(
                f"/requests/{request_id}/requirement-generations",
                json={"inputSnapshotId": patched["inputSnapshotId"], "expectedInputRevision": 2},
            )
        ).json()
        assert gen_job["status"] == "queued"

        gen_job = await _poll(client, f"/requests/{request_id}/requirement-generations/{gen_job['id']}")
        assert gen_job["status"] == "succeeded"
        document_id = gen_job["result"]["id"]

        doc = (await client.get(f"/requests/{request_id}/requirement-documents/{document_id}")).json()
        assert "다운로드 센터 개선" in doc["markdown"]

        selected = (
            await client.patch(
                f"/requests/{request_id}",
                json={
                    "expectedRequestRevision": patched["requestRevision"],
                    "workingRequirementDocumentId": document_id,
                },
            )
        ).json()
        assert selected["workingRequirementDocumentId"] == document_id

        confirm_response = await client.post(
            f"/requests/{request_id}/requirement-confirmations",
            json={
                "requirementDocumentId": document_id,
                "expectedInputRevision": selected["inputRevision"],
                "expectedRequestRevision": selected["requestRevision"],
            },
        )
        assert confirm_response.status_code == 201
        confirmation = confirm_response.json()

        files = {"file": ("requirements.md", doc["markdown"].encode("utf-8"), "text/markdown")}
        analysis_job = (
            await client.post(
                f"/requests/{request_id}/requirement-confirmations/{confirmation['id']}/analysis-jobs",
                files=files,
            )
        ).json()
        assert analysis_job["status"] == "queued"

        analysis_job = await _poll(client, f"/analysis-jobs/{analysis_job['id']}")
        analysis_id = analysis_job["result"]["id"]

        analysis = (await client.get(f"/analysis-results/{analysis_id}")).json()
        assert analysis["totalDays"] > 0
        assert analysis["impacts"][0]["type"] in ("UI", "Logic", "API", "DB", "Permission")

        report_job = (
            await client.post(
                "/review-reports",
                json={
                    "requestId": request_id,
                    "confirmationId": confirmation["id"],
                    "analysisResultId": analysis_id,
                },
            )
        ).json()
        report_job = await _poll(client, f"/report-jobs/{report_job['id']}")
        report_id = report_job["result"]["id"]

        report = (await client.get(f"/review-reports/{report_id}")).json()
        assert "검토결과 리포트" in report["markdown"]

        registration_response = await client.post(
            "/review-registrations",
            json={
                "requestId": request_id,
                "confirmationId": confirmation["id"],
                "analysisResultId": analysis_id,
                "reportId": report_id,
                "reviewChecks": {"scopeReviewed": True, "estimateReviewed": True},
            },
        )
        assert registration_response.status_code == 201
        registration = registration_response.json()

        search = (await client.get("/review-registrations")).json()
        assert any(item["id"] == registration["id"] for item in search["items"])

        detail = (await client.get(f"/review-registrations/{registration['id']}")).json()
        assert detail["reportSnapshot"]["id"] == report_id

        mock_job = (
            await client.post(
                f"/requests/{request_id}/system-mock-generations",
                data={"requirementDocumentId": document_id, "legacyVersion": "DEMO-2026.10"},
                files={"file": ("requirements.md", doc["markdown"].encode("utf-8"), "text/markdown")},
            )
        ).json()
        assert mock_job["status"] == "queued"
        mock_job = await _poll(client, f"/requests/{request_id}/system-mock-generations/{mock_job['id']}")
        assert mock_job["status"] == "succeeded"

        latest_mock = (await client.get(f"/requests/{request_id}/system-mock")).json()
        assert "<!doctype html>" in latest_mock["html"]
