#!/usr/bin/env python3
"""
Generate high-volume synthetic activity over the real music catalog.

This does NOT create fake tracks, artists, albums or genres. It only generates
users, playlists and behavioral facts (streams, searches, favorites, sessions).

Usage (repo root):
    python scripts/generate_activity.py --target 1600000
    python scripts/generate_activity.py --multiplier 2
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "analytics"))
sys.path.insert(0, str(ROOT / "apps" / "backend"))

WAREHOUSE = ROOT / "data" / "warehouse" / "voxmetrik.duckdb"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic activity over real tracks")
    parser.add_argument("--target", type=int, help="Total rows desired across activity fact tables")
    parser.add_argument("--multiplier", type=int, help="target = current activity rows × multiplier")
    args = parser.parse_args()

    if not args.target and not args.multiplier:
        raise SystemExit("Provide --target or --multiplier")
    if not WAREHOUSE.exists():
        raise SystemExit(f"Warehouse not found: {WAREHOUSE}\nRun import_from_pocketbase.py first.")

    import duckdb
    from app.packages.analytics.services.stats_service import generate_synthetic_activity

    conn = duckdb.connect(str(WAREHOUSE))
    try:
        result = generate_synthetic_activity(
            conn,
            target_total=args.target,
            multiplier=args.multiplier,
        )
        conn.commit()
    finally:
        conn.close()

    print(
        "[activity] "
        f"{result['before']:,} -> {result['after']:,} "
        f"(+{result['created']:,}); real tracks: {result.get('track_total', result['source_rows']):,}"
    )
    if result.get("purged_synthetic_tracks"):
        print(f"[activity] purged old synthetic tracks: {result['purged_synthetic_tracks']:,}")


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        print(f"[activity] {exc}", file=sys.stderr)
        sys.exit(1)
