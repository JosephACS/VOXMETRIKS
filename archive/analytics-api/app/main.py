from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import duckdb
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import artists, audit, genres, recommendations, streams, system, users
from app.core.config import get_settings
from app.core.db import close_db, get_db, open_db
from app.core.exceptions import register_exception_handlers
from app.core.logging_config import get_logger, setup_logging
from app.middleware.request_context import RequestContextMiddleware
from app.utils.response_wrapper import success_response

setup_logging()
logger = get_logger("voxmetrik.analytics")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    logger.info(
        "Starting %s env=%s DuckDB=%s cache=%s",
        settings.app_name,
        settings.environment,
        settings.db_path_resolved,
        settings.cache_enabled,
    )
    try:
        open_db()
    except FileNotFoundError as exc:
        logger.error("Database unavailable at startup: %s", exc)
    yield
    close_db()
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        description="Enterprise music analytics API backed by DuckDB warehouse.",
        version="1.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url="/redoc" if settings.docs_enabled else None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
    )

    application.add_middleware(RequestContextMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["GET", "OPTIONS"],
        allow_headers=["*"],
    )

    register_exception_handlers(application)

    application.include_router(system.router)
    application.include_router(artists.router)
    application.include_router(streams.router)
    application.include_router(genres.router)
    application.include_router(recommendations.router)
    application.include_router(users.router)
    application.include_router(audit.router)

    @application.get("/", tags=["Root"])
    def root():
        return success_response(
            {
                "app": settings.app_name,
                "version": "1.1.0",
                "environment": settings.environment,
                "health": "/health",
                "health_full": "/system/health/full",
                "docs": "/docs" if settings.docs_enabled else None,
            },
            "VOXMETRIK Analytics API",
        )

    @application.get("/health", tags=["Health"])
    def health(conn: duckdb.DuckDBPyConnection = Depends(get_db)):
        db_path = settings.db_path_resolved
        try:
            tables = [r[0] for r in conn.execute("SHOW TABLES").fetchall()]
            duckdb_version = conn.execute("SELECT version()").fetchone()[0]
            status = "ok"
            message = "Service healthy"
        except Exception as exc:
            logger.error("Health check failed: %s", exc)
            tables = []
            duckdb_version = None
            status = "degraded"
            message = str(exc)

        return success_response(
            {
                "app": settings.app_name,
                "version": "1.1.0",
                "environment": settings.environment,
                "database": str(db_path),
                "table_count": len(tables),
                "duckdb_version": duckdb_version,
                "status": status,
            },
            message,
        )

    return application


app = create_app()


if __name__ == "__main__":
    import uvicorn

    cfg = get_settings()
    uvicorn.run(
        "app.main:app",
        host=cfg.host,
        port=cfg.port,
        reload=cfg.debug,
        log_level=cfg.log_level.lower(),
    )
