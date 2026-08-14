"""Schema readiness — per database/connection, with a process-wide startup hint.

A process-global flag MUST NOT skip DDL on an independent DuckDB file.
Startup still skips repeated DDL on the same warehouse path.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

_schema_ready = False
_ready_ids: set[str] = set()


def connection_schema_id(conn: Any) -> str:
    """Stable id for the main attached database of ``conn``."""
    try:
        rows = conn.execute("PRAGMA database_list").fetchall()
    except Exception:  # noqa: BLE001
        return f"conn:{id(conn)}"
    for row in rows:
        name = row[1] if len(row) > 1 else ""
        file = row[2] if len(row) > 2 else ""
        if str(name) != "main":
            continue
        if file:
            try:
                return str(Path(str(file)).resolve())
            except Exception:  # noqa: BLE001
                return str(file)
        return f"memory:{id(conn)}"
    return f"conn:{id(conn)}"


def schema_ready_for_connection(conn: Any) -> bool:
    return connection_schema_id(conn) in _ready_ids


def mark_connection_schema_ready(conn: Any) -> None:
    _ready_ids.add(connection_schema_id(conn))


def mark_schema_ready() -> None:
    global _schema_ready
    _schema_ready = True


def reset_schema_ready_for_tests() -> None:
    """Test-only: allow ensure_* to recreate tables after DB wipe."""
    global _schema_ready
    _schema_ready = False
    _ready_ids.clear()


def schema_ready() -> bool:
    return _schema_ready
