from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_HERE = Path(__file__).resolve().parent
_APP_ROOT = _HERE.parent
_SERVICE_ROOT = _APP_ROOT.parent
_PROJECT_ROOT = _SERVICE_ROOT.parent

_ENV_FILES = tuple(
    str(p)
    for p in (_SERVICE_ROOT / ".env", _PROJECT_ROOT / ".env")
    if p.exists()
)
for env_path in (_SERVICE_ROOT / ".env", _PROJECT_ROOT / ".env"):
    if env_path.exists():
        load_dotenv(env_path, override=False)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILES or ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "VOXMETRIK Analytics API"
    environment: Literal["development", "production", "staging"] = "development"
    debug: bool = False
    log_level: str = "INFO"
    log_json: bool = False
    sql_log_enabled: bool = True

    db_path: str = ""
    host: str = "0.0.0.0"
    port: int = 8001
    cors_origins: str = "http://localhost:4200,http://127.0.0.1:4200"

    cache_enabled: bool = True
    cache_ttl_seconds: int = Field(default=60, ge=5, le=3600)
    cache_max_entries: int = Field(default=128, ge=16, le=2048)

    health_verbose: bool = False

    @field_validator("environment", mode="before")
    @classmethod
    def normalize_environment(cls, value: object) -> str:
        raw = str(value or "development").strip().lower()
        if raw in {"prod", "production"}:
            return "production"
        if raw in {"stage", "staging"}:
            return "staging"
        return "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"

    @property
    def docs_enabled(self) -> bool:
        return not self.is_production or self.debug

    @property
    def db_path_resolved(self) -> Path:
        if self.db_path.strip():
            return Path(self.db_path.strip())
        for parent in (_PROJECT_ROOT, _SERVICE_ROOT, *_PROJECT_ROOT.parents):
            candidate = parent / "data" / "warehouse" / "voxmetrik.duckdb"
            if candidate.exists():
                return candidate
        return _PROJECT_ROOT / "data" / "warehouse" / "voxmetrik.duckdb"

    @property
    def cors_origin_list(self) -> list[str]:
        raw = self.cors_origins.strip()
        if raw == "*":
            return [] if self.is_production else ["*"]
        return [origin.strip() for origin in raw.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
