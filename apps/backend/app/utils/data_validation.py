from __future__ import annotations

from dataclasses import dataclass, field

from app.core.logging import get_logger
from app.db.duckdb_client import DuckDBClient, get_duckdb_client

logger = get_logger(__name__)

CORE_TABLES = (
    "dim_track",
    "dim_usuario",
    "fact_streaming",
)

GOLD_TABLES = (
    "agg_daily_streams",
    "agg_tracks_populares",
    "agg_artist_growth",
    "agg_user_engagement",
    "agg_dashboard_cache",
)

COUNT_TABLES = {
    "streaming": "fact_streaming",
    "tracks": "dim_track",
    "users": "dim_usuario",
    "gold_daily": "agg_daily_streams",
}


@dataclass
class ValidationReport:
    tables_ok: bool
    gold_ready: bool
    row_counts: dict[str, int] = field(default_factory=dict)
    missing_tables: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        return self.tables_ok and self.gold_ready and not self.errors


def validate_warehouse(client: DuckDBClient | None = None) -> ValidationReport:
    """Validate warehouse schema, row counts, and basic ID integrity."""
    report = ValidationReport(tables_ok=True, gold_ready=True)
    try:
        db = client or get_duckdb_client()
    except Exception as exc:
        report.tables_ok = False
        report.gold_ready = False
        report.errors.append(f"warehouse_unreachable: {exc}")
        return report

    existing = {t.lower() for t in db.list_tables()}

    for table in CORE_TABLES:
        if table.lower() not in existing:
            report.missing_tables.append(table)
            report.tables_ok = False

    gold_present = sum(1 for t in GOLD_TABLES if t.lower() in existing)
    report.gold_ready = gold_present >= 3
    if not report.gold_ready:
        report.errors.append(f"gold_incomplete: {gold_present}/{len(GOLD_TABLES)} tables")

    for label, table in COUNT_TABLES.items():
        if table.lower() not in existing:
            report.row_counts[label] = 0
            continue
        try:
            count = int(db.fetch_scalar(f"SELECT COUNT(*) FROM {table}", label=f"validate_{label}") or 0)
            report.row_counts[label] = count
            if count == 0 and table in CORE_TABLES:
                report.errors.append(f"empty_table: {table}")
                if table != "fact_streaming":
                    report.tables_ok = False
        except Exception as exc:
            report.errors.append(f"count_failed:{table}:{exc}")

    if "fact_streaming" in existing and "dim_track" in existing:
        orphan = db.fetch_scalar(
            """
            SELECT COUNT(*) FROM fact_streaming fs
            LEFT JOIN dim_track dt ON dt.id_track = fs.id_track
            WHERE fs.id_track IS NOT NULL AND dt.id_track IS NULL
            LIMIT 1
            """,
            label="validate_stream_track_fk",
        )
        if orphan and int(orphan) > 0:
            report.errors.append(f"orphan_streams: {orphan}")

    if report.errors:
        logger.warning("warehouse_validation issues=%s", report.errors)
    return report
