"""Helpers to re-point Settings at an isolated DuckDB during a single test."""

from __future__ import annotations

from pathlib import Path

from app.core.config import Settings, set_settings_override

_session_settings: Settings | None = None


def remember_session_settings(settings: Settings) -> None:
    global _session_settings
    _session_settings = settings


def clear_session_settings() -> None:
    global _session_settings
    _session_settings = None


def _reset_db_handles() -> None:
    from app.core.database import close_read_pool
    from app.db.duckdb_client import shutdown_duckdb_client

    shutdown_duckdb_client()
    close_read_pool()


def bind_test_db(db_path: Path | str) -> None:
    """Point settings at ``db_path`` and drop any shared DuckDB handle."""
    _reset_db_handles()
    if _session_settings is not None:
        data = _session_settings.model_dump()
        data["db_path"] = str(db_path)
        set_settings_override(Settings(**data))
        return
    # Fallback when session settings are missing — keep test payment/seed defaults.
    set_settings_override(
        Settings(
            db_path=str(db_path),
            payment_provider="academic_mock",
            seed_demo_users=True,
            seed_demo_crm_users=True,
        )
    )


def restore_session_db() -> None:
    """Restore the session pytest Settings and reopen the shared pool if possible."""
    _reset_db_handles()
    if _session_settings is None:
        return
    set_settings_override(_session_settings)
    try:
        from app.core.database import open_read_pool

        path = _session_settings.db_path_resolved
        if path.exists():
            open_read_pool(path)
    except Exception:
        pass
