"""
elt/load/load_duckdb.py
=======================
Standalone helper: loads a Silver Parquet file directly into an existing
DuckDB warehouse (raw_spotify staging table only — does NOT rebuild dimensions).

Use this when you want to refresh raw data without running the full pipeline.
For a complete rebuild, use:
    python elt/pipelines/elt_pipeline.py

Usage:
    python elt/load/load_duckdb.py
    python elt/load/load_duckdb.py --parquet data/silver/silver_spotify.parquet
    python elt/load/load_duckdb.py --rebuild-all
"""

import argparse
import logging
import sys
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────────────
_HERE         = Path(__file__).resolve().parent          # elt/load/
_PROJECT_ROOT = _HERE.parent.parent                      # VOXMETRIK_V2/

sys.path.insert(0, str(_PROJECT_ROOT / "elt" / "pipelines"))

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)-8s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger("voxmetrik.load_duckdb")

# ── Defaults ──────────────────────────────────────────────────────────────────
DEFAULT_DB      = _PROJECT_ROOT / "data" / "warehouse" / "voxmetrik.duckdb"
DEFAULT_PARQUET = _PROJECT_ROOT / "data" / "silver" / "silver_spotify.parquet"
BRONZE_PARQUET  = _PROJECT_ROOT / "data" / "bronze" / "raw_spotify.parquet"


def load_parquet_to_duckdb(parquet_path: Path, db_path: Path) -> int:
    """
    Load a Parquet file into raw_spotify staging table.
    Returns number of rows loaded.
    """
    import duckdb
    import pandas as pd

    if not parquet_path.exists():
        raise FileNotFoundError(f"Parquet not found: {parquet_path}")

    logger.info(f"Loading parquet: {parquet_path}")
    df = pd.read_parquet(str(parquet_path))
    logger.info(f"  Rows: {len(df):,},  Columns: {list(df.columns)}")

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(db_path), read_only=False)

    try:
        # Minimal staging table (created if missing)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS raw_spotify (
                id               INTEGER PRIMARY KEY,
                track_id         VARCHAR,
                track_name       VARCHAR,
                artists          VARCHAR,
                album_name       VARCHAR,
                popularity       INTEGER,
                duration_ms      INTEGER,
                explicit         BOOLEAN,
                danceability     DOUBLE,
                energy           DOUBLE,
                key_col          INTEGER,
                loudness         DOUBLE,
                mode_col         INTEGER,
                speechiness      DOUBLE,
                acousticness     DOUBLE,
                instrumentalness DOUBLE,
                liveness         DOUBLE,
                valence          DOUBLE,
                tempo            DOUBLE,
                time_signature   INTEGER,
                track_genre      VARCHAR,
                fecha_ingesta    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Only keep columns that exist in the table
        existing_cols = [
            row[0] for row in conn.execute("DESCRIBE raw_spotify").fetchall()
            if row[0] != "id" and row[0] != "fecha_ingesta"
        ]
        available = [c for c in existing_cols if c in df.columns]

        df_load = df[available].copy().reset_index(drop=True)
        df_load.insert(0, "id", range(1, len(df_load) + 1))

        conn.execute("DELETE FROM raw_spotify")
        conn.register("_df_load", df_load)
        cols_sql = ", ".join(available)
        conn.execute(f"INSERT INTO raw_spotify (id, {cols_sql}) SELECT id, {cols_sql} FROM _df_load")
        conn.unregister("_df_load")
        conn.commit()

        count = conn.execute("SELECT COUNT(*) FROM raw_spotify").fetchone()[0]
        logger.info(f"raw_spotify → {count:,} rows loaded ✓")
        return count

    finally:
        conn.close()


def rebuild_all(db_path: Path, parquet_path: Path) -> None:
    """Run the full ELT pipeline (delegates to elt_pipeline.py logic)."""
    try:
        from elt_pipeline import (
            _open_connection, apply_schema, silver_transform,
            gold_load_staging, gold_build_warehouse, verify_warehouse,
        )
        import pandas as pd

        logger.info("Running full warehouse rebuild via elt_pipeline…")
        df_silver = pd.read_parquet(str(parquet_path))
        conn = _open_connection(db_path)
        try:
            apply_schema(conn)
            gold_load_staging(conn, df_silver)
            gold_build_warehouse(conn)
            verify_warehouse(conn)
            conn.commit()
        finally:
            conn.close()
        logger.info("Full rebuild complete ✓")
    except ImportError:
        logger.error(
            "Cannot import elt_pipeline.  Run directly:\n"
            "  python elt/pipelines/elt_pipeline.py"
        )
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load Parquet data into the VOXMETRIK DuckDB warehouse"
    )
    parser.add_argument(
        "--parquet",
        type=Path,
        default=DEFAULT_PARQUET,
        help=f"Path to Parquet file (default: {DEFAULT_PARQUET})",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB,
        help=f"Path to DuckDB file (default: {DEFAULT_DB})",
    )
    parser.add_argument(
        "--rebuild-all",
        action="store_true",
        help="Rebuild full dimensional model (not just staging table)",
    )
    parser.add_argument(
        "--use-bronze",
        action="store_true",
        help=f"Use Bronze parquet ({BRONZE_PARQUET}) instead of Silver",
    )
    args = parser.parse_args()

    parquet = BRONZE_PARQUET if args.use_bronze else args.parquet

    if args.rebuild_all:
        rebuild_all(args.db, parquet)
    else:
        load_parquet_to_duckdb(parquet, args.db)


if __name__ == "__main__":
    main()