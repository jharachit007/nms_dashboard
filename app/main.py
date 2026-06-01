from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.middleware import RequestLoggingMiddleware
from app.api.operator_routes import router as operator_router
from app.api.ops_routes import router as ops_router
from app.api.routes import router
from app.api.search_routes import router as search_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.services.background_jobs import get_background_job_manager


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await get_background_job_manager(settings).start()
        try:
            yield
        finally:
            await get_background_job_manager(settings).stop()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    if settings.request_log_enabled:
        app.add_middleware(RequestLoggingMiddleware)

    app.include_router(router, prefix=settings.api_prefix)
    app.include_router(operator_router, prefix=settings.api_prefix)
    app.include_router(ops_router, prefix=settings.api_prefix)
    app.include_router(search_router, prefix=settings.api_prefix)

    frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
    if frontend_dir.exists():
        app.mount("/ui", StaticFiles(directory=str(frontend_dir), html=True), name="ui")

        @app.get("/", include_in_schema=False)
        def redirect_to_ui() -> RedirectResponse:
            return RedirectResponse(url="/ui/index.html")

    return app


app = create_app()
