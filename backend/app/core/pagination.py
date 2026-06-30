"""Keyset (cursor) pagination helpers for stable catalog ordering."""

from __future__ import annotations

from typing import Optional, Tuple


def encode_track_cursor(popularity: Optional[int], track_id: int) -> str:
    pop = int(popularity) if popularity is not None else -1
    return f"{pop}:{int(track_id)}"


def decode_track_cursor(cursor: str) -> Tuple[int, int]:
    raw = (cursor or "").strip()
    if ":" not in raw:
        raise ValueError("Invalid cursor")
    pop_s, id_s = raw.split(":", 1)
    return int(pop_s), int(id_s)


def track_cursor_predicate(*, alias: str = "dt") -> str:
    """Rows strictly after ``(popularity DESC, id_track ASC)`` cursor."""
    pop = f"COALESCE({alias}.popularity, -1)"
    return f"({pop} < ? OR ({pop} = ? AND {alias}.id_track > ?))"
