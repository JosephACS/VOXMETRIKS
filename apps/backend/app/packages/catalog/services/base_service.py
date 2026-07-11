"""Backward-compatible re-exports; prefer ``app.core.query_helpers``."""

from app.core.query_helpers import count_rows, fetch_rows

__all__ = ["count_rows", "fetch_rows"]
