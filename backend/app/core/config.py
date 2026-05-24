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

for _candidate in [_BACKEND / ".env", _PROJECT_ROOT / ".env"]:
    if _candidate.exists():
        load_dotenv(dotenv_path=str(_candidate), override=False)
        break


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
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