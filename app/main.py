import structlog
from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.root import router as root_router
from app.api.v1 import router as api_v1_router
from app.config import settings
from app.db.session import init_db
from app.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging()
    init_db()

    app = FastAPI(title="Barghouth Footy Analytics Backend", version="0.1.0")
    app.include_router(root_router)
    app.include_router(health_router)
    app.include_router(api_v1_router)

    return app


app = create_app()


@app.on_event("startup")
async def on_startup() -> None:
    logger = structlog.get_logger()
    logger.info("application.startup", env=settings.app_env)


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger = structlog.get_logger()
    logger.info("application.shutdown")
