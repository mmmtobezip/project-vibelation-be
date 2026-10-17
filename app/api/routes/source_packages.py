"""SRC-01~03 — api_interface_v06.md §20.1, §20.3~20.4 (ZIP 업로드·교체·제외)."""

from fastapi import APIRouter, status

from app.api.errors import not_implemented

router = APIRouter(tags=["source-packages"])


@router.post(
    "/legacy-systems/{system_id}/source-packages",
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_source_package(system_id: str):
    """SRC-01 프론트/백 ZIP 업로드 (multipart: file, role, expectedSystemRevision)."""
    raise not_implemented("SRC-01 ZIP 업로드")


@router.get("/legacy-systems/{system_id}/source-packages/{package_id}")
async def get_source_package(system_id: str, package_id: str):
    """SRC-02 검증·인덱싱 상태 조회."""
    raise not_implemented("SRC-02 패키지 상태 조회")


@router.delete(
    "/legacy-systems/{system_id}/source-packages/{package_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_source_package(system_id: str, package_id: str):
    """SRC-03 초안 구성에서 파일 제외 (If-Match: systemRevision 필요)."""
    raise not_implemented("SRC-03 패키지 제외")
