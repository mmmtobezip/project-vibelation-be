"""FILE-01~03 — api_interface_v06.md §6."""

from fastapi import UploadFile

from app.api import errors
from app.core.settings import settings
from app.repositories.memory import new_id, now_iso, store
from app.services.requests_service import get_request

POLICY_VERSION = "policy-01"
ALLOWED_EXTENSIONS = ["txt", "md", "html", "pdf", "docx", "pptx", "png", "jpg", "jpeg"]


def get_attachment_policy() -> dict:
    return {
        "policyVersion": POLICY_VERSION,
        "allowedExtensions": ALLOWED_EXTENSIONS,
        "maxFileBytes": settings.max_file_bytes,
        "maxFilesPerRequest": settings.max_files_per_request,
        "maxTotalBytesPerRequest": settings.max_file_bytes * settings.max_files_per_request,
    }


async def upload_attachment(request_id: str, file: UploadFile) -> dict:
    get_request(request_id)
    extension = (file.filename or "").rsplit(".", 1)[-1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise errors.ApiError(415, "UNSUPPORTED_FILE_TYPE", f"지원하지 않는 파일 형식입니다: {extension}")
    content = await file.read()
    if len(content) > settings.max_file_bytes:
        raise errors.ApiError(413, "FILE_TOO_LARGE", "파일 크기가 정책 상한을 초과했습니다.")
    attachment_id = new_id("file")
    attachment = {
        "id": attachment_id,
        "requestId": request_id,
        "name": file.filename,
        "contentType": file.content_type or "application/octet-stream",
        "sizeBytes": len(content),
        "uploadStatus": "uploaded",
        "extractionStatus": "notRequired",
        "usableForGeneration": True,
        "policyVersion": POLICY_VERSION,
        "createdAt": now_iso(),
        "error": None,
    }
    store.attachments[attachment_id] = attachment
    return attachment


def get_attachment_status(request_id: str, attachment_id: str) -> dict:
    attachment = store.attachments.get(attachment_id)
    if not attachment or attachment["requestId"] != request_id:
        raise errors.not_found("첨부 자료를 찾을 수 없습니다.")
    return attachment
