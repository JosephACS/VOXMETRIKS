"""
backend/main.py
===============
VOXMETRIK_V2 — FastAPI application entry point.

Run:
    cd backend
    uvicorn main:app --reload

Or from project root:
    uvicorn backend.main:app --reload
"""

from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

import duckdb
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# ── Ensure backend package is importable when run from project root ───────────
_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from app.core import get_settings, list_tables
from app.core.database import close_read_pool, open_read_pool
from app.core.indexes import ensure_secondary_indexes
from app.core.schema_bootstrap import mark_schema_ready
from app.core.search_fold import ensure_search_fold
from app.packages.analytics.routes import analytics_router, stats_router
from app.packages.streaming.routes import (
    artists_router,
    dashboard_router,
    favorites_router,
    genres_router,
    playlists_router,
    tracks_router,
)
from app.packages.streaming.services.app_storage import ensure_app_tables
from app.packages.users.routes import users_router
from app.packages.users.services.user_storage import ensure_user_tables
from app.shared.schemas.models import HealthResponse

# ── Logging ───────────────────────────────────────────────────────────────────
settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="[%(asctime)s] [%(levelname)-8s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("voxmetrik.api")


# ── Lifespan: validate DB on startup ─────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    db_path = settings.db_path_resolved
    logger.info(
        "VOXMETRIK_V2 API starting up — environment=%s, docs=%s, DuckDB: %s",
        settings.environment,
        "enabled" if settings.docs_enabled else "disabled",
        db_path,
    )

    if not db_path.exists():
        logger.error(
            f"Database not found: {db_path}\n"
            "  → Run:  python elt_pipeline.py  first"
        )
    else:
        try:
            conn = duckdb.connect(str(db_path))
            tables = list_tables(conn)
            ensure_user_tables(conn)
            ensure_app_tables(conn)
            ensure_secondary_indexes(conn)
            ensure_search_fold(conn)
            mark_schema_ready()
            conn.close()
            open_read_pool(db_path)
            logger.info(f"Database OK — {len(tables)} tables")
        except Exception as exc:
            logger.error(f"Database check failed: {exc}")

    yield
    close_read_pool()
    logger.info("VOXMETRIK_V2 API shutting down")


# ── App ───────────────────────────────────────────────────────────────────────
# Interactive docs (/docs, /redoc, /openapi.json) are served in development and
# disabled in production to avoid exposing the API surface publicly.
_docs_enabled = settings.docs_enabled

app = FastAPI(
    title="VOXMETRIK_V2 API",
    description=(
        "Spotify dataset analytics API backed by DuckDB.\n\n"
        "Run `python elt_pipeline.py` from the project root to populate the database."
    ),
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs" if _docs_enabled else None,
    redoc_url="/redoc" if _docs_enabled else None,
    openapi_url="/openapi.json" if _docs_enabled else None,
)

# CORS — restrict origins via CORS_ORIGINS (comma-separated; "*" allowed only
# outside production). In production an empty allow-list means no cross-origin
# is granted until real origins are configured.
_cors_origins = settings.cors_origin_list
if settings.is_production and ("*" in _cors_origins or not _cors_origins):
    logger.warning(
        "CORS: production requires an explicit origin allow-list. "
        "Set CORS_ORIGINS to your frontend domain(s); wildcard/empty is rejected."
    )
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(artists_router, prefix="/api/v1")
app.include_router(genres_router,  prefix="/api/v1")
app.include_router(tracks_router,  prefix="/api/v1")
app.include_router(playlists_router, prefix="/api/v1")
app.include_router(favorites_router, prefix="/api/v1")
app.include_router(dashboard_router, prefix="/api/v1")
app.include_router(stats_router,   prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(users_router,   prefix="/api/v1")


# ── Global exception handlers ─────────────────────────────────────────────────

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    logger.warning(f"ValueError on {request.url}: {exc}")
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(FileNotFoundError)
async def file_not_found_handler(request: Request, exc: FileNotFoundError) -> JSONResponse:
    logger.error(f"FileNotFoundError on {request.url}: {exc}")
    return JSONResponse(
        status_code=503,
        content={
            "detail": str(exc),
            "hint": "Run python elt_pipeline.py to create the database.",
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled error on {request.url}: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# ── Health & root ─────────────────────────────────────────────────────────────

@app.get("/", tags=["Root"])
def root():
    return {
        "app":     "VOXMETRIK_V2",
        "version": "2.0.0",
        "docs":    "/docs",
        "health":  "/health",
    }


@app.get("/health", response_model=HealthResponse, tags=["Root"])
def health():
    db_path = settings.db_path_resolved
    if not db_path.exists():
        return HealthResponse(
            status="degraded",
            version="2.0.0",
            table_count=0,
            database=str(db_path) if settings.health_verbose else None,
        )
    try:
        conn   = duckdb.connect(str(db_path))
        tables = list_tables(conn)
        ver    = conn.execute("SELECT version()").fetchone()[0]
        conn.close()
        return HealthResponse(
            status="ok",
            version=ver,
            table_count=len(tables),
            database=str(db_path) if settings.health_verbose else None,
            tables=tables if settings.health_verbose else [],
        )
    except Exception as exc:
        logger.error(f"Health check error: {exc}")
        return HealthResponse(
            status="error",
            version="2.0.0",
            table_count=0,
            database=str(db_path) if settings.health_verbose else None,
        )


# ── Dev entry-point ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )
