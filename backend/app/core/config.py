"""
backend/config.py
=================
Centralised configuration via pydantic-settings.
All settings are read from environment variables (or .env file).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env from backend/ first, then project root
_HERE = Path(__file__).resolve().parent          # backend/app/core/
_BACKEND = _HERE.parent.parent                   # backend/
_PROJECT_ROOT = _BACKEND.parent                  # VOXMETRIK_V2/

# Load backend/.env first, then project root (root wins on duplicate keys)
if (_BACKEND / ".env").exists():
    load_dotenv(dotenv_path=str(_BACKEND / ".env"), override=False)
if (_PROJECT_ROOT / ".env").exists():
    load_dotenv(dotenv_path=str(_PROJECT_ROOT / ".env"), override=True)

_ENV_FILES = tuple(
    str(p)
    for p in (_BACKEND / ".env", _PROJECT_ROOT / ".env")
    if p.exists()
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILES or ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # DuckDB — leave empty to use auto-resolved default
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

    # Security / ops
    cors_origins: str = "http://localhost:4200,http://127.0.0.1:4200"
    health_verbose: bool = False
    seed_demo_users: bool = True
    auth_rate_limit: int = 20
    auth_rate_window_sec: int = 60

    # Audio playback — YouTube Data API v3 key (resolves real, full-length
    # playback via the official IFrame player). Leave blank to disable.
    youtube_api_key: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        raw = self.cors_origins.strip()
        if raw == "*":
            return ["*"]
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


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()