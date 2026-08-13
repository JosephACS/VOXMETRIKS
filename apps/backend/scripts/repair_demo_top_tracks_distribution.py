"""Repair flat demo top-track streams with deterministic varied weights.

Only touches fact_streaming when the Top-N distribution for the default
report window (last ~30 days of data) is too flat to demonstrate a
leaderboard. Idempotent via seeded weights.

    python apps/backend/scripts/repair_demo_top_tracks_distribution.py
"""

from __future__ import annotations

import hashlib
import sys
from datetime import timedelta
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
_ROOT = _BACKEND.parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

SEED = "044-voxmetriks-demo-top-tracks"
TOP_N = 50
FLAT_RATIO = 0.55


def _weight(track_id: int, rank_hint: int) -> float:
    digest = hashlib.sha256(f"{SEED}:{track_id}".encode()).hexdigest()
    jitter = (int(digest[:8], 16) % 1000) / 1000.0
    base = max(0.12, 1.0 - (rank_hint * 0.07))
    return base * (0.85 + 0.3 * jitter)


def main() -> int:
    import duckdb

    db = _ROOT / "data" / "warehouse" / "voxmetrik.duckdb"
    if not db.exists():
        print(f"DB missing: {db}")
        return 1

    conn = duckdb.connect(str(db))
    try:
        tables = {r[0] for r in conn.execute("SHOW TABLES").fetchall()}
        if "fact_streaming" not in tables:
            print("No fact_streaming")
            return 1

        bounds = conn.execute(
            "SELECT MIN(fecha_evento)::DATE, MAX(fecha_evento)::DATE FROM fact_streaming"
        ).fetchone()
        if not bounds or bounds[1] is None:
            print("No fact_streaming dates")
            return 0
        end = bounds[1] + timedelta(days=1)
        start = bounds[1] - timedelta(days=29)

        rows = conn.execute(
            """
            SELECT id_track, COALESCE(SUM(streams), COUNT(*)) AS total
            FROM fact_streaming
            WHERE fecha_evento >= ? AND fecha_evento < ?
            GROUP BY 1
            ORDER BY total DESC
            LIMIT ?
            """,
            [start, end, TOP_N],
        ).fetchall()
        if len(rows) < 5:
            print("Not enough tracks to repair in window")
            return 0

        totals = [int(r[1] or 0) for r in rows]
        mx, mn = max(totals), min(totals)
        if mx > 0 and mn / mx < FLAT_RATIO:
            print(f"Window distribution already useful (min/max={mn}/{mx}); skip")
            return 0

        print(f"Flat window Top-{len(rows)} (min/max={mn}/{mx}) -> reweight synthetic rows")
        weight_map = {int(r[0]): _weight(int(r[0]), i) for i, r in enumerate(rows)}
        cols = {r[0] for r in conn.execute("DESCRIBE fact_streaming").fetchall()}
        has_synth = "is_synthetic" in cols

        updated = 0
        for tid, w in weight_map.items():
            # Rank-shaped absolute plays so ties dissolve even when sources were identical.
            target = max(1, int(round(1000 * float(w))))
            if has_synth:
                conn.execute(
                    """
                    UPDATE fact_streaming
                    SET streams = ?
                    WHERE id_track = ?
                      AND fecha_evento >= ? AND fecha_evento < ?
                      AND COALESCE(is_synthetic, TRUE)
                    """,
                    [target, tid, start, end],
                )
            else:
                conn.execute(
                    """
                    UPDATE fact_streaming
                    SET streams = ?
                    WHERE id_track = ?
                      AND fecha_evento >= ? AND fecha_evento < ?
                    """,
                    [target, tid, start, end],
                )
            updated += 1

        print(f"Repaired {updated} tracks in [{start}, {end}) seed={SEED}")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
