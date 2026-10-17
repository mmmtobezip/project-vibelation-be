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
