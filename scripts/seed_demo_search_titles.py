#!/usr/bin/env python3
"""Inject recognizable demo track titles into existing warehouse (no full rebuild)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from elt.extract.bootstrap_catalog import DEMO_TRACK_TITLES

WAREHOUSE = ROOT / "data" / "warehouse" / "voxmetrik.duckdb"


def main() -> None:
    import duckdb

    conn = duckdb.connect(str(WAREHOUSE))
    total = 0
    for i, title in enumerate(DEMO_TRACK_TITLES, start=1):
        spotify_id = f"boot_{i:06d}"
        syn_prefix = f"syn_{spotify_id}_"
        conn.execute(
            "UPDATE dim_track SET nombre_track = ? WHERE spotify_track_id = ?",
            [title, spotify_id],
        )
        conn.execute(
            """
            UPDATE dim_track
            SET nombre_track = ? || ' · #' || CAST(id_track AS VARCHAR)
            WHERE spotify_track_id LIKE ?
            """,
            [title, f"{syn_prefix}%"],
        )
        n = conn.execute(
            """
            SELECT COUNT(*) FROM dim_track
            WHERE spotify_track_id = ? OR spotify_track_id LIKE ?
            """,
            [spotify_id, f"{syn_prefix}%"],
        ).fetchone()[0]
        total += n
    conn.close()
    print(f"Patched {len(DEMO_TRACK_TITLES)} demo titles across {total:,} rows.")


if __name__ == "__main__":
    main()
