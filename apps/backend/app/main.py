"""
VOXMETRIK_V2 — FastAPI application entry point.

Architecture:
  - V2 modular layer: app/api, app/services, app/db, app/etl
  - Legacy packages: app/packages (streaming, analytics, users) at /api/v1

Run:
    cd backend
    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import JSONResponse

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from app.api.enterprise_router import enterprise_v1_router
from app.api.router import api_router
from app.core import get_settings
from app.core.database import close_read_pool, open_read_pool, using_write_conn
from app.core.indexes import ensure_secondary_indexes
from app.core.logging import get_logger, setup_logging
from app.core.schema_bootstrap import mark_schema_ready
from app.core.search_fold import ensure_search_fold
from app.core.error_handlers import register_error_handlers
from app.core.middleware import RequestTimingMiddleware
from app.core.request_context import RequestContextMiddleware
from app.core.security import configure_security
from app.db.duckdb_client import shutdown_duckdb_client
from app.db.init_db import bootstrap_database, shutdown_database
from app.models.schemas import SystemHealthResponse
from app.pipeline.orchestrator import run_system_boot
from app.services.health_service import HealthService
from app.packages.analytics.routes import analytics_router, smart_router, stats_router
from app.packages.ai.routes.ai import router as ai_router
from app.platform.routes.platform import router as platform_router
from app.packages.catalog.routes import artists_router, genres_router, tracks_router
from app.packages.engagement.routes import (
    dashboard_router,
    favorites_router,
    playlists_router,
)
from app.packages.engagement.services.app_storage import ensure_app_tables
from app.packages.identity.routes import users_router
from app.packages.identity.services.user_storage import ensure_user_tables
from app.packages.organizations.infrastructure.schema import ensure_organization_tables
from app.packages.organizations.routes import organizations_router

setup_logging()
logger = get_logger("voxmetrik.main")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    db_path = settings.db_path_resolved
    logger.info(
        "VOXMETRIK_V2 starting env=%s warehouse=%s",
        settings.environment,
        db_path,
    )

    skip_boot = os.getenv("SKIP_SYSTEM_BOOT", "").strip().lower() in ("1", "true", "yes", "on")
    if not skip_boot:
        try:
            run_system_boot()
        except Exception as exc:
            logger.error("[BOOT] System boot failed: %s", exc, exc_info=True)
    else:
        logger.info("[BOOT] Skipped (SKIP_SYSTEM_BOOT)")

    bootstrap = bootstrap_database()
    shutdown_duckdb_client()

    if bootstrap.get("ready"):
        try:
            with using_write_conn() as conn:
                ensure_user_tables(conn)
                ensure_app_tables(conn)
                # Critical for Spec 016 I1 — must not be swallowed.
                ensure_organization_tables(conn)
                try:
                    ensure_secondary_indexes(conn)
                    ensure_search_fold(conn)
                except Exception as exc:
                    logger.error(
                        "Secondary index/search_fold bootstrap failed: %s",
                        exc,
                        exc_info=True,
                    )
            mark_schema_ready()
            open_read_pool(db_path)
            logger.info("Warehouse OK — %s tables", bootstrap.get("table_count"))
        except Exception as exc:
            logger.error("Legacy bootstrap failed: %s", exc, exc_info=True)
            raise
    else:
        logger.warning("Warehouse not ready: %s", bootstrap.get("message"))

    from app.platform.jobs.scheduler import start_scheduler
    from app.platform.jobs.tasks import (
        task_clean_stale_cache,
        task_record_metrics,
        task_refresh_recommendations_cache,
        task_validate_audio_sources,
    )

    start_scheduler([
        task_record_metrics,
        task_refresh_recommendations_cache,
        task_validate_audio_sources,
        task_clean_stale_cache,
    ])

    yield

    from app.platform.jobs.scheduler import stop_scheduler
    await stop_scheduler()

    shutdown_database()
    close_read_pool()
    shutdown_duckdb_client()
    logger.info("VOXMETRIK_V2 shutdown complete")


def create_app() -> FastAPI:
    application = FastAPI(
        title="VOXMETRIK_V2 API",
        description=(
            "Production-ready streaming analytics platform.\n\n"
            "## Architecture\n"
            "- **Enterprise API** (`/api/v1`): dashboard, analytics, tracks, users\n"
            "- **Modular API** (`/api/v2`): domain services\n"
            "- **Legacy API** (`/api/v1/*`): streaming catalog, auth, playlists\n\n"
            "## Response envelope\n"
            "Success: `{ status, data, meta }` — Error: `{ status, message, details }`\n\n"
            "## Pagination & filters\n"
            "List endpoints support `page`, `page_size`, `sort_by`, `sort_order`, "
            "and optional filters (`genre`, `artist`, `platform`, `device`, `min_popularity`)."
        ),
        version="2.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.docs_enabled else None,
        redoc_url="/redoc" if settings.docs_enabled else None,
        openapi_url="/openapi.json" if settings.docs_enabled else None,
        contact={"name": "VOXMETRIK Engineering"},
        license_info={"name": "Proprietary"},
    )

    configure_security(application)
    application.add_middleware(RequestTimingMiddleware)
    application.add_middleware(RequestContextMiddleware)
    register_error_handlers(application)

    # ── Spec 014 D1: /api/v1 facade ─────────────────────────────────────────
    # Enterprise V1 registers first for overlapping contracts used by Angular
    # (dashboard/overview, analytics/streams, tracks/top, users/{id}/insights).
    # Package routers remain as COMPATIBILITY_ADAPTER surfaces for non-overlapping
    # paths (/dashboard/home, /stats/*, catalog CRUD, etc.). See app.api.route_policy.
    application.include_router(enterprise_v1_router)

    # ── V2 modular router (compatibility adapter; AUTH_REQUIRED on sensitive) ─
    application.include_router(api_router)

    # ── Package routers (backward compatible under /api/v1) ─────────────────
    application.include_router(artists_router, prefix="/api/v1")
    application.include_router(genres_router, prefix="/api/v1")
    application.include_router(tracks_router, prefix="/api/v1")
    application.include_router(playlists_router, prefix="/api/v1")
    application.include_router(favorites_router, prefix="/api/v1")
    application.include_router(dashboard_router, prefix="/api/v1")
    application.include_router(stats_router, prefix="/api/v1")
    application.include_router(analytics_router, prefix="/api/v1")
    application.include_router(smart_router, prefix="/api/v1")
    application.include_router(ai_router, prefix="/api/v1")
    application.include_router(platform_router, prefix="/api/v1")
    application.include_router(users_router, prefix="/api/v1")
    application.include_router(organizations_router, prefix="/api/v1")

    @application.get("/", tags=["Root"], summary="Service metadata")
    def root():
        return {
            "app": "VOXMETRIK_V2",
            "version": "2.0.0",
            "environment": settings.environment,
            "health": "/health",
            "api_v2": "/api/v2",
            "api_v1": "/api/v1",
            "docs": "/docs" if settings.docs_enabled else None,
        }

    @application.get("/health", response_model=SystemHealthResponse, tags=["Health"])
    def health():
        try:
            return HealthService().get_system_health()
        except FileNotFoundError:
            return SystemHealthResponse(
                status="degraded",
                db_connected=False,
                tables_ok=False,
                etl_status="unknown",
                gold_ready=False,
            )
        except Exception as exc:
            logger.error("Health check failed: %s", exc)
            return SystemHealthResponse(
                status="unhealthy",
                db_connected=False,
                tables_ok=False,
                etl_status="error",
                gold_ready=False,
            )

    return application


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload or settings.debug,
        log_level=settings.log_level.lower(),
    )
