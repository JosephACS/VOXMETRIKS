#!/usr/bin/env python3
"""
Pre-warm the YouTube audio-source cache for catalog tracks.

Playback resolution is lazy (first play triggers a search). This script
resolves tracks ahead of time so users hear real audio instead of demo clips.

Search strategy (backend):
  1. YouTube Data API v3 when YOUTUBE_API_KEY is set (~100 searches/day free)
  2. yt-dlp fallback when quota is exhausted or no key (no daily quota cap)

Usage (repo root):
    python scripts/resolve_audio_youtube.py --limit 500
    python scripts/resolve_audio_youtube.py --limit 2000 --delay 0.4
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

WAREHOUSE = ROOT / "data" / "warehouse" / "voxmetrik.duckdb"


def main() -> None:
    parser = argparse.ArgumentParser(description="Pre-resolve YouTube ids for tracks")
    parser.add_argument("--limit", type=int, default=500, help="Max tracks to resolve this run")
    parser.add_argument("--delay", type=float, default=0.35, help="Seconds between searches")
    parser.add_argument(
        "--max-errors", type=int, default=5,
        help="Stop after this many consecutive transient errors",
    )
    args = parser.parse_args()

    if not WAREHOUSE.exists():
        raise SystemExit(f"Warehouse not found: {WAREHOUSE}")

    import duckdb
    from app.packages.streaming.services.audio_source_service import (
        STATUS_OK, STATUS_NOT_FOUND, STATUS_ERROR, resolve_audio_source,
    )

    conn = duckdb.connect(str(WAREHOUSE))

    rows = conn.execute(
        """
        SELECT dt.id_track, dt.nombre_track
        FROM dim_track dt
        LEFT JOIN app_track_audio_source a ON a.track_id = dt.id_track
        WHERE a.track_id IS NULL OR a.status NOT IN ('ok', 'not_found')
        ORDER BY dt.popularity DESC NULLS LAST, dt.id_track
        LIMIT ?
        """,
        [args.limit],
    ).fetchall()

    if not rows:
        print("[resolve] nothing to do — selected tracks already cached.")
        conn.close()
        return

    ok = miss = err = 0
    consecutive_err = 0
    print(f"[resolve] resolving {len(rows)} tracks (delay={args.delay}s)...")
    for i, (tid, name) in enumerate(rows, start=1):
        res = resolve_audio_source(conn, tid, force=False)
        status = (res or {}).get("status")
        if status == STATUS_OK:
            ok += 1
            consecutive_err = 0
        elif status == STATUS_NOT_FOUND:
            miss += 1
            consecutive_err = 0
        else:
            err += 1
            consecutive_err += 1
        conn.commit()

        if i % 25 == 0 or i == len(rows):
            print(f"  {i}/{len(rows)}  ok={ok} not_found={miss} err={err}  last={name!r}")

        if consecutive_err >= args.max_errors:
            print(f"[resolve] stopping after {consecutive_err} consecutive errors.")
            break
        time.sleep(args.delay)

    conn.close()
    print(f"[resolve] done — ok={ok} not_found={miss} err={err}")


if __name__ == "__main__":
    main()
