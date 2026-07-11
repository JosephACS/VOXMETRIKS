from __future__ import annotations

from functools import lru_cache
from pathlib import Path

_SQL_ROOT = Path(__file__).resolve().parent.parent / "sql"


@lru_cache(maxsize=64)
def load_sql(name: str) -> str:
    """Load a SQL file from app/sql/{name}.sql."""
    path = _SQL_ROOT / f"{name}.sql"
    if not path.exists():
        raise FileNotFoundError(f"SQL file not found: {path}")
    return path.read_text(encoding="utf-8").strip()
