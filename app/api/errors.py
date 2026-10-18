"""Common error envelope per api_interface_v06.md §13.

{"error": {"code", "message", "retryable", "fieldErrors", "details"}, "requestId"}
"""

from fastapi import HTTPException


class ApiError(HTTPException):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        retryable: bool = False,
        field_errors: list[dict] | None = None,
        details: dict | None = None,
    ):
        super().__init__(
            status_code=status_code,
            detail={
                "error": {
                    "code": code,
                    "message": message,
                    "retryable": retryable,
                    "fieldErrors": field_errors or [],
                    "details": details or {},
                },
            },
        )


def not_implemented(feature: str) -> ApiError:
    return ApiError(
        status_code=501,
        code="NOT_IMPLEMENTED",
        message=f"{feature}은 스캐폴드 단계로 아직 구현되지 않았습니다.",
    )


def not_found(message: str = "리소스를 찾을 수 없습니다.") -> ApiError:
    return ApiError(status_code=404, code="NOT_FOUND", message=message)


def version_conflict(current_request_revision: int) -> ApiError:
    return ApiError(
        status_code=409,
        code="VERSION_CONFLICT",
        message="다른 변경사항이 저장되었습니다.",
        details={"currentRequestRevision": current_request_revision},
    )


def stale_input(current_input_revision: int) -> ApiError:
    return ApiError(
        status_code=409,
        code="STALE_INPUT",
        message="입력이 변경되었습니다. 다시 확인해주세요.",
        details={"currentInputRevision": current_input_revision},
    )


def stale_confirmation(message: str = "선택 이후 입력이 변경되었습니다.") -> ApiError:
    return ApiError(status_code=409, code="STALE_CONFIRMATION", message=message)


def invalid_request(message: str, field_errors: list[dict] | None = None) -> ApiError:
    return ApiError(status_code=400, code="INVALID_REQUEST", message=message, field_errors=field_errors)


def job_already_running(job_id: str) -> ApiError:
    return ApiError(
        status_code=409,
        code="JOB_ALREADY_RUNNING",
        message="같은 종류의 작업이 이미 진행 중입니다.",
        details={"jobId": job_id},
    )


def document_mismatch() -> ApiError:
    return ApiError(
        status_code=409,
        code="DOCUMENT_MISMATCH",
        message="업로드한 MD 내용이 확정 스냅샷과 일치하지 않습니다.",
    )


def attachment_not_ready() -> ApiError:
    return ApiError(
        status_code=422,
        code="ATTACHMENT_NOT_READY",
        message="첨부 자료가 아직 사용 가능 상태가 아닙니다.",
    )


def review_checks_required() -> ApiError:
    return ApiError(
        status_code=422,
        code="REVIEW_CHECKS_REQUIRED",
        message="scopeReviewed/estimateReviewed 체크가 모두 필요합니다.",
    )
