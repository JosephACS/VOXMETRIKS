"""Tokenized, accent-insensitive text search helpers for catalog queries."""

from __future__ import annotations

import re
import unicodedata
from typing import List, Sequence, Tuple

# Short words ignored so "vamonos a marte" matches title "Vámonos a Marte"
_STOPWORDS = frozenset({
    "a", "al", "de", "del", "el", "en", "la", "las", "lo", "los", "un", "una", "y",
    "the", "to", "of", "in", "on", "for", "and", "or",
    "feat", "ft", "featuring", "vol", "volume",
})

_ACCENT_PAIRS: Sequence[Tuple[str, str]] = (
    ("á", "a"), ("à", "a"), ("ä", "a"), ("â", "a"), ("ã", "a"),
    ("é", "e"), ("è", "e"), ("ë", "e"), ("ê", "e"),
    ("í", "i"), ("ì", "i"), ("ï", "i"), ("î", "i"),
    ("ó", "o"), ("ò", "o"), ("ö", "o"), ("ô", "o"), ("õ", "o"),
    ("ú", "u"), ("ù", "u"), ("ü", "u"), ("û", "u"),
    ("ñ", "n"),
)


def fold_text(value: str) -> str:
    """Lowercase + strip accents for matching."""
    if not value:
        return ""
    normalized = unicodedata.normalize("NFD", value.strip())
    stripped = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
    return stripped.lower()


def search_tokens(query: str) -> List[str]:
    """Split query into meaningful tokens (accent-folded, no stopwords)."""
    folded = fold_text(query)
    if not folded:
        return []
    # Collapse punctuation so "(feat." / "Vol." do not become broken tokens.
    cleaned = re.sub(r"[^a-z0-9À-ÿ]+", " ", folded, flags=re.IGNORECASE)
    tokens = [t for t in cleaned.split() if t and t not in _STOPWORDS and len(t) >= 2]
    if tokens:
        return tokens
    single = cleaned.replace(" ", "")
    return [single] if single else []


def duckdb_fold_expr(column_sql: str) -> str:
    """Nest DuckDB replace() calls to fold accents in SQL."""
    expr = f"lower({column_sql})"
    for src, dst in _ACCENT_PAIRS:
        expr = f"replace({expr}, '{src}', '{dst}')"
    return expr


def _word_boundary_haystack(expr: str) -> str:
    """Collapse punctuation to spaces so we can match word prefixes."""
    return f"regexp_replace({expr}, '[^a-z0-9]+', ' ', 'g')"


def build_track_search_filter(
    query: str,
    *,
    track_col: str = "dt.nombre_track",
    artist_col: str = "da.nombre_artista",
    genre_col: str = "dg.nombre_genero",
    search_fold_col: str | None = None,
) -> Tuple[str, List[str]]:
    """
    Build WHERE fragment: every token must be a prefix of some word in
    track / artist / genre (accent-insensitive).

    Avoids mid-word false positives like ``meda`` matching ``Someday``.
    Returns (sql_fragment, params).
    """
    tokens = search_tokens(query)
    if not tokens:
        return "1=0", []

    if search_fold_col:
        haystack = search_fold_col
    else:
        track_f = duckdb_fold_expr(track_col)
        artist_f = duckdb_fold_expr(f"COALESCE({artist_col}, '')")
        genre_f = duckdb_fold_expr(f"COALESCE({genre_col}, '')")
        haystack = f"({track_f} || ' ' || {artist_f} || ' ' || {genre_f})"

    word_haystack = _word_boundary_haystack(haystack)

    parts: List[str] = []
    params: List[str] = []
    for token in tokens:
        # Start of title/artist OR start of any later word
        parts.append(f"({word_haystack} LIKE ? OR {word_haystack} LIKE ?)")
        params.extend([f"{token}%", f"% {token}%"])
    return " AND ".join(parts), params
