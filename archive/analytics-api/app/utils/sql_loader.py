from __future__ import annotations

from pathlib import Path
from typing import Any

_SQL_DIR = Path(__file__).resolve().parent.parent / "sql"


def load_sql(name: str) -> str:
    """Load a named SQL file from app/sql/{name}.sql."""
    path = _SQL_DIR / f"{name}.sql"
    if not path.exists():
        raise FileNotFoundError(f"SQL file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def apply_limit(sql: str, limit: int) -> str:
    if "LIMIT" in sql.upper():
        return sql
    return f"{sql.rstrip(';')}\nLIMIT ?"
