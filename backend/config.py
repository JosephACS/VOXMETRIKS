"""
backend/config.py
=================
Centralized configuration via pydantic-settings.
All settings are read from environment variables (or .env file).
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env from backend/ first, then project root
_HERE = Path(__file__).resolve().parent
for _candidate in [_HERE / ".env", _HERE.parent / ".env"]:
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

    # DuckDB
    db_path: str = ""  # resolved below if empty

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
        if self.db_path.strip():
            return Path(self.db_path.strip())
        # Default: <project_root>/duckdb/voxmetrik.duckdb
        return _HERE.parent / "duckdb" / "voxmetrik.duckdb"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
