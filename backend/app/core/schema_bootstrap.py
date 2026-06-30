"""Process-wide flag: app/user DDL ran once at API startup."""

from __future__ import annotations

_schema_ready = False


def mark_schema_ready() -> None:
    global _schema_ready
    _schema_ready = True


def schema_ready() -> bool:
    return _schema_ready
