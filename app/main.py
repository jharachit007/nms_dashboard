from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.operator_routes import router as operator_router
from app.api.routes import router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.include_router(router, prefix=settings.api_prefix)
    app.include_router(operator_router, prefix=settings.api_prefix)

    frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
    if frontend_dir.exists():
        app.mount("/ui", StaticFiles(directory=str(frontend_dir), html=True), name="ui")

        @app.get("/", include_in_schema=False)
        def redirect_to_ui() -> RedirectResponse:
            return RedirectResponse(url="/ui/index.html")

    return app


app = create_app()
