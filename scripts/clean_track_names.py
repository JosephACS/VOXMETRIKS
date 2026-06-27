#!/usr/bin/env python3
"""
Clean dirty display text directly in the warehouse (no full ELT rebuild).

Removes ONLY leftovers from old demo/synthetic seeding, never real titles:
  - " · #12345" / " — #12345"  (middot/dash + id disambiguator added by the
    old `seed_demo_search_titles.py`)
  - " #12345" trailing ids of 4+ digits (old `bootstrap_catalog.py` synthetics)
  - "[syn-123]" synthetic markers
  - U+FFFD replacement characters and collapsed whitespace

It deliberately does NOT strip short hashes or leading hashes, so real names
like "Funk #49", "#1 Hits", "#Acoustic" or "# (Hashtag)" stay intact.

Usage (repo root):
    python scripts/clean_track_names.py --dry-run   # report only
    python scripts/clean_track_names.py             # apply
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WAREHOUSE = ROOT / "data" / "warehouse" / "voxmetrik.duckdb"

REPLACEMENT_CHAR = "\uFFFD"

# (table, column) pairs that hold human-readable names shown in the UI.
TARGETS = [
    ("dim_track", "nombre_track"),
    ("dim_artista", "nombre_artista"),
    ("dim_album", "nombre_album"),
    ("agg_tracks_populares", "nombre_track"),
    ("agg_tracks_populares", "nombre_artista"),
    ("agg_tracks_populares", "nombre_album"),
    ("agg_top_artistas", "nombre_artista"),
    ("agg_artist_growth", "nombre_artista"),
]


def clean_expr(col: str) -> str:
    c = f'"{col}"'
    # Order matters: drop markers/suffixes, then collapse whitespace, then trim.
    return (
        "trim(regexp_replace("
        "regexp_replace("
        "regexp_replace("
        "regexp_replace("
        f"regexp_replace({c}, '" + REPLACEMENT_CHAR + "', '', 'g'),"
        " '(?i)\\s*\\[syn-\\d+\\]\\s*$', '', 'g'),"
        " '\\s*[—–·•∙‧]\\s*#\\d+\\s*$', '', 'g'),"
        " '\\s+#\\d{4,}\\s*$', '', 'g'),"
        " '\\s+', ' ', 'g'))"
    )


def table_has_column(conn, table: str, column: str) -> bool:
    try:
        cols = [c[1] for c in conn.execute(f"PRAGMA table_info('{table}')").fetchall()]
    except Exception:
        return False
    return column in cols


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean demo/synthetic noise in warehouse names")
    parser.add_argument("--dry-run", action="store_true", help="Report affected rows without writing")
    args = parser.parse_args()

    if not WAREHOUSE.exists():
        raise SystemExit(f"Warehouse not found: {WAREHOUSE}\nRun import_from_pocketbase.py first.")

    import duckdb

    conn = duckdb.connect(str(WAREHOUSE), read_only=args.dry_run)
    total_fixed = 0
    try:
        for table, col in TARGETS:
            if not table_has_column(conn, table, col):
                continue
            expr = clean_expr(col)
            c = f'"{col}"'
            where = f"{c} IS NOT NULL AND {c} <> {expr}"

            affected = conn.execute(f"SELECT COUNT(*) FROM {table} WHERE {where}").fetchone()[0]
            if not affected:
                print(f"[clean] {table}.{col}: clean")
                continue

            sample = conn.execute(
                f"SELECT {c} AS dirty, {expr} AS clean FROM {table} WHERE {where} LIMIT 5"
            ).fetchall()
            print(f"[clean] {table}.{col}: {affected:,} rows to fix")
            for dirty, clean in sample:
                print(f"        '{dirty}'  ->  '{clean}'")

            if not args.dry_run:
                conn.execute(f"UPDATE {table} SET {c} = {expr} WHERE {where}")
                total_fixed += affected

        if args.dry_run:
            print("[clean] dry-run — no changes written.")
        else:
            conn.commit()
            print(f"[clean] done — {total_fixed:,} values cleaned.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
