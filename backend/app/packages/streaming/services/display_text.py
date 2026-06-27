"""Human-readable text cleanup for API responses."""

from __future__ import annotations

import re

_SYN_SUFFIX = re.compile(r"\s*\[syn-\d+\]\s*$", re.IGNORECASE)
_HASH_SUFFIX = re.compile(r"\s*[—–-]\s*#\d+\s*$")
_NUM_SUFFIX = re.compile(r"\s+#\d{4,}\s*$")


def sanitize_display_text(value: str | None) -> str:
    raw = (value or "").strip()
    if not raw:
        return "—"
    raw = raw.replace("\ufffd", "")
    raw = _SYN_SUFFIX.sub("", raw)
    raw = _HASH_SUFFIX.sub("", raw)
    raw = _NUM_SUFFIX.sub("", raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    return raw or "—"


_NAME_KEYS = ("nombre_track", "nombre_artista", "nombre_genero")


def clean_catalog_row(row: dict) -> dict:
    out = dict(row)
    for key in _NAME_KEYS:
        if key in out and out[key] is not None:
            out[key] = sanitize_display_text(str(out[key]))
    return out


def clean_catalog_rows(rows: list) -> list:
    return [clean_catalog_row(r) for r in rows]
