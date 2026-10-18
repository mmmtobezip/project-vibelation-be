"""Demo history seed (app/repositories/seed.py) populates REG-02/03 at boot."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_seeded_registrations_appear_in_search():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api") as client:
        search = (await client.get("/review-registrations")).json()
        titles = {item["title"] for item in search["items"]}
        assert {"다운로드 센터 다중 선택 개선", "로그인 2단계 인증 추가", "알림 센터 읽음 처리 개선"} <= titles


@pytest.mark.asyncio
async def test_seeded_registration_detail_is_internally_consistent():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test/api") as client:
        search = (await client.get("/review-registrations")).json()
        seeded = next(item for item in search["items"] if item["title"] == "알림 센터 읽음 처리 개선")

        detail = (await client.get(f"/review-registrations/{seeded['id']}")).json()
        assert detail["title"] in detail["confirmationSnapshot"]["documentSnapshot"]["markdown"]
        assert detail["title"] in detail["analysisSnapshot"]["impacts"][0]["name"]
        assert detail["title"] in detail["reportSnapshot"]["markdown"]
