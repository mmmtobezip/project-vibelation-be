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


async def generated_document(client: AsyncClient) -> dict:
    """Creates a request, generates a MD, and selects it (no confirmation yet).

    Returns {"requestId", "document", "requestRevision"} (requestRevision is
    the value *after* selection, ready to pass as expectedRequestRevision).
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

    return {"requestId": request_id, "document": document, "requestRevision": selected["requestRevision"]}


async def confirmed_request(client: AsyncClient) -> dict:
    """Builds on generated_document() and confirms the selected MD.

    Returns {"requestId", "confirmation", "document"}.
    """
    ctx = await generated_document(client)
    document = ctx["document"]

    confirmation = (
        await client.post(
            f"/requests/{ctx['requestId']}/requirement-confirmations",
            json={
                "requirementDocumentId": document["id"],
                "expectedInputRevision": document["inputRevision"],
                "expectedRequestRevision": ctx["requestRevision"],
            },
        )
    ).json()

    return {"requestId": ctx["requestId"], "confirmation": confirmation, "document": document}
