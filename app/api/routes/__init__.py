from fastapi import APIRouter

from . import (
    analyses,
    confirmations,
    files,
    history,
    legacy_systems,
    mocks,
    reports,
    requests,
    requirements,
    source_packages,
)

api_router = APIRouter(prefix="/api")
api_router.include_router(requests.router)
api_router.include_router(files.router)
api_router.include_router(requirements.router)
api_router.include_router(mocks.router)
api_router.include_router(confirmations.router)
api_router.include_router(analyses.router)
api_router.include_router(reports.router)
api_router.include_router(history.router)
api_router.include_router(legacy_systems.router)
api_router.include_router(source_packages.router)
