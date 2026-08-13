"""Repair synthetic agg_daily_streams with deterministic varied demo values.

Uses the same generator as seed_044_consolidation_fixture._daily_streams.
Honestly synthetic / demo. Idempotent.

    python apps/backend/scripts/repair_demo_streams_series.py
"""

from __future__ import annotations

import hashlib
import random
import sys
from datetime import date, timedelta
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
_ROOT = _BACKEND.parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

STREAM_SEED = "044-voxmetriks-demo-streams"
STREAM_DAYS = 60


def _prng(key: str) -> random.Random:
    digest = hashlib.sha256(key.encode()).hexdigest()
    return random.Random(int(digest[:16], 16))


def _daily_streams(day: date) -> int:
    weekend = 1 if day.weekday() >= 5 else 0
    day_rng = _prng(f"{STREAM_SEED}:{day.isoformat()}")
    bucket = day_rng.randrange(10)
    if bucket <= 2:
        base = 4200 + day_rng.randrange(900)
    elif bucket <= 7:
        base = 5800 + day_rng.randrange(1400)
    else:
        base = 7800 + day_rng.randrange(2200)
    return max(0, int(base + weekend * (280 + day_rng.randrange(180))))


def main() -> int:
    import duckdb

    db = _ROOT / "data" / "warehouse" / "voxmetrik.duckdb"
    if not db.exists():
        print(f"missing {db}")
        return 1
    conn = duckdb.connect(str(db))
    try:
        row = conn.execute("SELECT MAX(fecha) FROM agg_daily_streams").fetchone()
        end_day = row[0] if row and row[0] is not None else date.today()
        if not hasattr(end_day, "year"):
            end_day = date.today()
        start_day = end_day - timedelta(days=STREAM_DAYS - 1)
        has_synthetic = False
        try:
            cols = {r[0] for r in conn.execute("DESCRIBE agg_daily_streams").fetchall()}
            has_synthetic = "is_synthetic" in cols
        except Exception:
            pass

        updated = 0
        d = start_day
        values: list[int] = []
        while d <= end_day:
            streams = _daily_streams(d)
            values.append(streams)
            users = max(60, streams // 48)
            tracks = max(30, streams // 95)
            exists = conn.execute(
                "SELECT 1 FROM agg_daily_streams WHERE fecha = ?", [d]
            ).fetchone()
            if exists:
                conn.execute(
                    """
                    UPDATE agg_daily_streams
                    SET total_streams = ?, unique_users = ?, unique_tracks = ?
                    WHERE fecha = ?
                    """,
                    [streams, users, tracks, d],
                )
            else:
                conn.execute(
                    """
                    INSERT INTO agg_daily_streams
                      (fecha, total_streams, unique_users, unique_tracks)
                    VALUES (?, ?, ?, ?)
                    """,
                    [d, streams, users, tracks],
                )
            if has_synthetic:
                conn.execute(
                    "UPDATE agg_daily_streams SET is_synthetic = TRUE WHERE fecha = ?",
                    [d],
                )
            updated += 1
            d += timedelta(days=1)

        uniq = len(set(values))
        print(
            {
                "ok": True,
                "days": updated,
                "unique_values": uniq,
                "min": min(values),
                "max": max(values),
                "from": start_day.isoformat(),
                "to": end_day.isoformat(),
                "seed": STREAM_SEED,
                "classification": "synthetic",
            }
        )
        return 0 if uniq > 1 else 2
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
