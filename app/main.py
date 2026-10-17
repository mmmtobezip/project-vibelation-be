from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api_router
from app.core.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # TODO: init DB engine / httpx AsyncClient here, dispose on shutdown.
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="VIBELATION Backend",
        version="0.1.0",
        lifespan=lifespan,
    )

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(api_router)

    @app.get("/health/live")
    async def health_live():
        return {"status": "ok"}

    @app.get("/health/ready")
    async def health_ready():
        # TODO: check DB/storage reachability once wired.
        return {"status": "ok"}

    return app


app = create_app()
