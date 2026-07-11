from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.db.duckdb_client import DuckDBClient, get_duckdb_client

logger = get_logger(__name__)


class BaseRepository:
    """Read-optimized DuckDB access — no business logic."""

    def __init__(self, client: DuckDBClient | None = None) -> None:
        self._client = client or get_duckdb_client()

    @property
    def client(self) -> DuckDBClient:
        return self._client

    def table_exists(self, name: str) -> bool:
        return name.lower() in {t.lower() for t in self._client.list_tables()}

    def fetch_all(
        self,
        sql: str,
        params: list | tuple | None = None,
        *,
        label: str = "repo_query",
    ) -> list[dict[str, Any]]:
        return self._client.fetch_all(sql, list(params or []), label=label)

    def fetch_one(
        self,
        sql: str,
        params: list | tuple | None = None,
        *,
        label: str = "repo_query",
    ) -> dict[str, Any] | None:
        return self._client.fetch_one(sql, list(params or []), label=label)

    def fetch_scalar(
        self,
        sql: str,
        params: list | tuple | None = None,
        *,
        label: str = "repo_scalar",
    ) -> Any:
        return self._client.fetch_scalar(sql, list(params or []), label=label)
