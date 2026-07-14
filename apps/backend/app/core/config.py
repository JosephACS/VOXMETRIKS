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
# Prefer project-root .env for non-empty keys only. Never clobber an already-set
# (or intentionally empty) variable with a blank ``DB_PATH=`` line.
if (_PROJECT_ROOT / ".env").exists():
    from dotenv import dotenv_values

    for _key, _val in (dotenv_values(str(_PROJECT_ROOT / ".env")) or {}).items():
        if _val is None or not str(_val).strip():
            continue
        os.environ[_key] = str(_val)

_ENV_FILES = tuple(str(p) for p in _env_candidates if p.exists())


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILES or ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
        env_ignore_empty=True,
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
    # 0 = disabled. Local/dev defaults to no global limit so home covers +
    # playback never hit 429. Production should set GLOBAL_RATE_LIMIT (e.g. 120–300).
    # Paths ending in /cover and /audio-source stay exempt even when enabled.
    global_rate_limit: int = 0
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
    # Soft TTL for negative audio / cover cache entries (seconds).
    audio_not_found_ttl_sec: int = 3600
    cover_not_found_ttl_sec: int = 3600
    # Per-provider HTTP timeout for YouTube / Audius lookups.
    audio_provider_timeout_sec: float = 12.0
    # Show is_demo / enterprise-demo orgs in the selector (opt-in).
    show_demo_organizations: bool = False

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

    # CRM — Spec 017
    # If None (default), any discount > 0 requires sales_manager approval.
    # If set to a float, discounts exceeding this % require approval.
    crm_discount_approval_threshold: float | None = None
    # Seed demo CRM users (sales_agent@voxmetrik.io / sales_manager@voxmetrik.io)
    seed_demo_crm_users: bool = True

    # Audio playback — YouTube Data API v3 key (resolves real, full-length
    # playback via the official IFrame player). Leave blank to disable.
    youtube_api_key: str = ""

    # ── Google Sign-In ───────────────────────────────────────────
    # OAuth 2.0 Client ID (Web) from Google Cloud Console. Used to verify
    # the ID token returned by Google Identity Services. Blank → button hidden.
    google_client_id: str = ""

    # ── Email (SMTP) — console | smtp | resend ──────────────────
    # EMAIL_PROVIDER=console (default) never sends real mail.
    # smtp: use Gmail *app password*, never the account password.
    # resend: optional HTTP API via RESEND_API_KEY.
    email_provider: str = "console"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_username: str = ""  # alias preferred over smtp_user
    smtp_password: str = ""
    smtp_from: str = ""
    email_from_address: str = ""  # preferred From address
    email_from_name: str = "VOXMETRIKS"
    smtp_use_tls: bool = True
    resend_api_key: str = ""
    resend_from_address: str = ""
    email_smoke_test_to: str = ""
    app_public_name: str = "VOXMETRIKS"
    email_code_ttl_min: int = 15
    email_code_max_attempts: int = 5
    email_resend_cooldown_sec: int = 60
    password_reset_ttl_min: int = 30
    # Frontend base for email links. Prefer FRONTEND_BASE_URL; APP_PUBLIC_BASE_URL kept as alias.
    frontend_base_url: str = ""
    app_public_base_url: str = ""

    @property
    def is_production(self) -> bool:
        """True when ENVIRONMENT denotes a production deployment."""
        return self.environment.strip().lower() in {"production", "prod"}

    @property
    def is_development(self) -> bool:
        return not self.is_production

    @property
    def seed_demo_crm_users_enabled(self) -> bool:
        """Seed demo CRM users only in development."""
        if self.is_production:
            return False
        return self.seed_demo_crm_users

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
    def resolved_frontend_base_url(self) -> str:
        """Public frontend origin for email deep-links (FRONTEND_BASE_URL preferred)."""
        raw = (self.frontend_base_url or self.app_public_base_url or "").strip()
        return raw.rstrip("/") if raw else ""

    @property
    def resolved_email_from_name(self) -> str:
        """Always present VOXMETRIKS as the transactional From display name."""
        return "VOXMETRIKS"

    @property
    def email_enabled(self) -> bool:
        """True when a real provider is selected and credentials exist."""
        provider = (self.email_provider or "console").strip().lower()
        if provider == "smtp":
            user = (self.smtp_username or self.smtp_user or "").strip()
            return bool(self.smtp_host.strip() and user)
        if provider == "resend":
            return bool((self.resend_api_key or "").strip())
        return False

    @property
    def email_is_console(self) -> bool:
        if self.is_test_runtime:
            return True
        return (self.email_provider or "console").strip().lower() in {
            "console", "console_mock_email", "mock", "",
        }

    @property
    def resolved_email_from_address(self) -> str:
        return (
            (self.email_from_address or "").strip()
            or (self.smtp_from or "").strip()
            or (self.smtp_username or self.smtp_user or "").strip()
            or "noreply@localhost"
        )

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
        # 1 — Explicit env/config override (treat blank as unset — .env may set DB_PATH=)
        if self.db_path and self.db_path.strip():
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
        """Global API rate limit.

        - Local/dev: 0 (unlimited) so streaming home/covers/playback never 429.
        - Pytest/E2E: honour configured value (usually 0).
        - Production: 0 falls back to 120 unless an explicit positive limit is set.
        """
        if self.is_test_runtime:
            return self.global_rate_limit
        if not self.is_production:
            # Development: always unlimited unless an explicit positive override is set
            return self.global_rate_limit if self.global_rate_limit > 0 else 0
        if self.global_rate_limit <= 0:
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


_settings_override: Settings | None = None


def set_settings_override(settings: Settings | None) -> None:
    """Test harness hook — mutable override so all ``from … import get_settings`` stays valid."""
    global _settings_override
    _settings_override = settings
    _cached_settings.cache_clear()


@lru_cache(maxsize=1)
def _cached_settings() -> Settings:
    return Settings()


def get_settings() -> Settings:
    if _settings_override is not None:
        return _settings_override
    return _cached_settings()


# Backward-compatible with call sites that do ``get_settings.cache_clear()``.
get_settings.cache_clear = _cached_settings.cache_clear  # type: ignore[attr-defined]
