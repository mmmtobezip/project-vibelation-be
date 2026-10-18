"""FILE-01~03 — api_interface_v06.md §6."""

from fastapi import APIRouter, File, UploadFile, status

from app.services import files_service

router = APIRouter(tags=["files"])


@router.get("/attachment-policy")
async def get_attachment_policy():
    """FILE-01 첨부 정책."""
    return files_service.get_attachment_policy()


@router.post("/requests/{request_id}/attachments", status_code=status.HTTP_201_CREATED)
async def upload_attachment(request_id: str, file: UploadFile = File(...)):
    """FILE-02 자료 첨부 (multipart, field=file)."""
    return await files_service.upload_attachment(request_id, file)


@router.get("/requests/{request_id}/attachments/{attachment_id}")
async def get_attachment_status(request_id: str, attachment_id: str):
    """FILE-03 첨부 처리 상태."""
    return files_service.get_attachment_status(request_id, attachment_id)
