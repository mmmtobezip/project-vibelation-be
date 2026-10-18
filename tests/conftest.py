import asyncio

from httpx import AsyncClient


async def poll(client: AsyncClient, url: str) -> dict:
    job = None
    for _ in range(20):
        response = await client.get(url)
        assert response.status_code == 200
        job = response.json()
        if job["status"] in ("succeeded", "failed"):
            return job
        await asyncio.sleep(0.2)
    raise AssertionError(f"job at {url} never finished: {job}")


async def confirmed_request(client: AsyncClient) -> dict:
    """Creates a request, generates+selects a MD, and confirms it.

    Returns {"requestId", "confirmation", "document"}.
    """
    created = (
        await client.post("/requests", json={"title": "에러 케이스 테스트", "legacyReferenceId": "legacy-01"})
    ).json()
    request_id = created["id"]

    patched = (
        await client.patch(
            f"/requests/{request_id}",
            json={
                "expectedRequestRevision": 1,
                "input": {"title": "에러 케이스 테스트", "text": "본문", "html": "", "desiredDueDate": None, "attachmentIds": []},
            },
        )
    ).json()

    gen_job = (
        await client.post(
            f"/requests/{request_id}/requirement-generations",
            json={"inputSnapshotId": patched["inputSnapshotId"], "expectedInputRevision": patched["inputRevision"]},
        )
    ).json()
    gen_job = await poll(client, f"/requests/{request_id}/requirement-generations/{gen_job['id']}")
    document_id = gen_job["result"]["id"]
    document = (await client.get(f"/requests/{request_id}/requirement-documents/{document_id}")).json()

    selected = (
        await client.patch(
            f"/requests/{request_id}",
            json={"expectedRequestRevision": patched["requestRevision"], "workingRequirementDocumentId": document_id},
        )
    ).json()

    confirmation = (
        await client.post(
            f"/requests/{request_id}/requirement-confirmations",
            json={
                "requirementDocumentId": document_id,
                "expectedInputRevision": selected["inputRevision"],
                "expectedRequestRevision": selected["requestRevision"],
            },
        )
    ).json()

    return {"requestId": request_id, "confirmation": confirmation, "document": document}
