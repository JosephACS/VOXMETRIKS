"""
backend/config.py
=================
Centralised configuration via pydantic-settings.
All settings are read from environment variables (or .env file).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import os
import sys

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env from apps/backend first, then repo root / infrastructure/environments
_HERE = Path(__file__).resolve().parent          # apps/backend/app/core/
_BACKEND = _HERE.parent.parent                   # apps/backend/


def _find_project_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "data" / "warehouse").is_dir():
            return candidate
        if (candidate / "apps" / "backend").is_dir() and (candidate / "data").is_dir():
            return candidate
    return start.parent.parent


_PROJECT_ROOT = _find_project_root(_BACKEND)

_env_candidates = [
    _BACKEND / ".env",
    _PROJECT_ROOT / ".env",
    _PROJECT_ROOT / "infrastructure" / "environments" / ".env",
]
for _env_path in _env_candidates:
    if _env_path.exists():
        load_dotenv(dotenv_path=str(_env_path), override=False)
if (_PROJECT_ROOT / ".env").exists():
    load_dotenv(dotenv_path=str(_PROJECT_ROOT / ".env"), override=True)

_ENV_FILES = tuple(str(p) for p in _env_candidates if p.exists())


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILES or ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    # Runtime environment — "development" (default) or "production".
    # Drives security hardening: demo-user seeding, dev_code exposure, API
    # docs availability and CORS wildcard handling. Defaults to development so
    # local/dev behaviour is unchanged unless ENVIRONMENT=production is set.
    environment: str = "development"
    debug: bool = False
    log_json: bool = False
    secret_key: str = "change-me-in-production"

    # DuckDB warehouse — env: DB_PATH
    db_path: str = ""

    # PocketBase
    pocketbase_url: str      = "http://127.0.0.1:8090"
    pocketbase_email: str    = ""
    pocketbase_password: str = ""

    # Server
    host: str      = "0.0.0.0"
    port: int      = 8000
    reload: bool   = False
    log_level: str = "INFO"
    api_prefix: str = "/api/v1"

    # Security / ops
    cors_origins: str = "http://localhost:4200,http://127.0.0.1:4200"
    health_verbose: bool = False
    seed_demo_users: bool = True
    auth_rate_limit: int = 20
    auth_rate_window_sec: int = 60
    global_rate_limit: int = 120
    global_rate_window_sec: int = 60
    # Set E2E=1 only in Playwright/pytest runs (.env.e2e, npm run e2e:backend).
    e2e_mode: bool = Field(default=False, validation_alias="E2E")

    # Cache TTL (seconds) — in-process, configurable per domain
    cache_enabled: bool = True
    cache_ttl_default: int = 60
    cache_ttl_dashboard: int = 120
    cache_ttl_analytics: int = 90
    cache_ttl_top_tracks: int = 180
    cache_ttl_recommendations: int = 120
    cache_ttl_smart_home: int = 90
    cache_ttl_audio: int = 300

    # Platform jobs (Phase 5)
    jobs_enabled: bool = True
    jobs_interval_sec: int = 300
    sse_enabled: bool = True
    ai_provider: str = "local"  # local | external | mock
    ai_llm_api_key: str = ""
    ai_llm_base_url: str = "https://api.openai.com/v1"
    ai_llm_model: str = "gpt-4o-mini"

    # Logging — file rotation (paths relative to backend/ unless absolute)
    log_dir: str = "logs"
    log_file_api: str = "api.log"
    log_file_errors: str = "errors.log"
    log_file_database: str = "database.log"
    log_max_bytes: int = 10_485_760  # 10 MB
    log_backup_count: int = 5
    log_to_files: bool = True

    # Pagination defaults
    pagination_default_page_size: int = 25
    pagination_max_page_size: int = 200

    # Audio playback — YouTube Data API v3 key (resolves real, full-length
    # playback via the official IFrame player). Leave blank to disable.
    youtube_api_key: str = ""

    # ── Google Sign-In ───────────────────────────────────────────
    # OAuth 2.0 Client ID (Web) from Google Cloud Console. Used to verify
    # the ID token returned by Google Identity Services. Blank → button hidden.
    google_client_id: str = ""

    # ── Email (SMTP) for verification codes ──────────────────────
    # Configure with a Gmail/Outlook/etc. account (use an app password).
    # If smtp_host/smtp_user are blank, registration runs in dev mode:
    # the code is logged server-side and returned in the API response so it
    # can be tested on localhost without a real mailbox.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    smtp_use_tls: bool = True
    app_public_name: str = "VOXMETRIK"
    email_code_ttl_min: int = 15
    email_code_max_attempts: int = 5

    @property
    def is_production(self) -> bool:
        """True when ENVIRONMENT denotes a production deployment."""
        return self.environment.strip().lower() in {"production", "prod"}

    @property
    def is_development(self) -> bool:
        return not self.is_production

    @property
    def seed_demo_users_enabled(self) -> bool:
        """Demo accounts are seeded only outside production.

        In production they are never created regardless of SEED_DEMO_USERS;
        in development the existing SEED_DEMO_USERS flag still applies.
        """
        if self.is_production:
            return False
        return self.seed_demo_users

    @property
    def docs_enabled(self) -> bool:
        """Interactive API docs (/docs, /redoc, /openapi.json) — off in production."""
        return not self.is_production

    @property
    def email_enabled(self) -> bool:
        return bool(self.smtp_host.strip() and self.smtp_user.strip())

    @property
    def email_from_address(self) -> str:
        return self.smtp_from.strip() or self.smtp_user.strip()

    @property
    def cors_origin_list(self) -> list[str]:
        raw = self.cors_origins.strip()
        if raw == "*":
            # Wildcard origins are permitted only outside production. In
            # production a "*" config is treated as "no explicit allow-list"
            # and collapses to an empty list so no cross-origin is granted
            # until real origins are configured via CORS_ORIGINS.
            return [] if self.is_production else ["*"]
        return [origin.strip() for origin in raw.split(",") if origin.strip()]

    @property
    def db_path_resolved(self) -> Path:
        # 1 — Explicit env/config override
        if self.db_path.strip():
            return Path(self.db_path.strip())

        # 2 — Walk up from this file to find the project root
        #     (identified by data/warehouse/ directory existing)
        for parent in Path(__file__).resolve().parents:
            candidate = parent / "data" / "warehouse" / "voxmetrik.duckdb"
            if candidate.parent.exists():
                return candidate

        # 3 — Hardcoded fallback relative to project root
        return _PROJECT_ROOT / "data" / "warehouse" / "voxmetrik.duckdb"

    @property
    def data_root(self) -> Path:
        return _PROJECT_ROOT / "data"

    @property
    def db_path_env(self) -> str:
        """Alias for DB_PATH documentation."""
        return str(self.db_path_resolved)

    @property
    def log_dir_resolved(self) -> Path:
        raw = self.log_dir.strip() or "logs"
        path = Path(raw)
        if not path.is_absolute():
            path = _BACKEND / path
        return path

    @property
    def is_test_runtime(self) -> bool:
        """True when running under pytest or explicit E2E harness."""
        if self.e2e_mode:
            return True
        if os.getenv("PYTEST_CURRENT_TEST"):
            return True
        if "pytest" in sys.modules:
            return True
        return False

    @property
    def effective_global_rate_limit(self) -> int:
        """Rate limit 0 is honoured only in E2E/pytest; otherwise restore default."""
        if self.global_rate_limit == 0 and not self.is_test_runtime:
            return 120
        return self.global_rate_limit

    @property
    def effective_auth_rate_limit(self) -> int:
        """Auth rate limit 0 is honoured only in E2E/pytest; otherwise restore default."""
        if self.auth_rate_limit == 0 and not self.is_test_runtime:
            return 20
        return self.auth_rate_limit

    @property
    def jobs_enabled_effective(self) -> bool:
        if self.is_test_runtime:
            return False
        return self.jobs_enabled


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
