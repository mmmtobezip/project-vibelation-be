"""Idempotency-Key behavior per api_interface_v06.md §2 "멱등성과 재시도"."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_same_key_same_body_returns_same_resource():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api") as client:
        body = {"title": "멱등성 테스트", "legacyReferenceId": "legacy-01"}
        headers = {"Idempotency-Key": "key-abc"}

        first = await client.post("/requests", json=body, headers=headers)
        second = await client.post("/requests", json=body, headers=headers)

        assert first.status_code == 201
        assert second.status_code == 201
        assert first.json()["id"] == second.json()["id"]


@pytest.mark.asyncio
async def test_same_key_different_body_conflicts():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api") as client:
        headers = {"Idempotency-Key": "key-xyz"}

        first = await client.post(
            "/requests", json={"title": "요청 A", "legacyReferenceId": "legacy-01"}, headers=headers
        )
        second = await client.post(
            "/requests", json={"title": "요청 B", "legacyReferenceId": "legacy-01"}, headers=headers
        )

        assert first.status_code == 201
        assert second.status_code == 409
        assert second.json()["detail"]["error"]["code"] == "IDEMPOTENCY_CONFLICT"
