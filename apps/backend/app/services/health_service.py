"""Enterprise health and system status."""

from __future__ import annotations

from datetime import date, datetime, timezone

from app.core.logging import get_logger
from app.db.duckdb_client import DuckDBClient, get_duckdb_client
from app.models.schemas import EnterpriseHealthResponse, SystemHealthResponse
from app.services._warehouse import table_exists
from app.utils.data_validation import validate_warehouse

logger = get_logger(__name__)

GOLD_TABLES = (
    "agg_daily_streams",
    "agg_tracks_populares",
    "agg_artist_growth",
    "agg_user_engagement",
    "agg_dashboard_cache",
)


class HealthService:
    """Warehouse + ETL readiness probes."""

    def __init__(self, client: DuckDBClient | None = None) -> None:
        self._client = client or get_duckdb_client()

    def get_system_health(self) -> SystemHealthResponse:
        from app.pipeline.orchestrator import get_boot_state

        boot = get_boot_state()
        try:
            self._client.ping()
            db_connected = True
            validation = validate_warehouse(self._client)
        except Exception as exc:
            logger.error("health_db_failed error=%s", exc)
            return SystemHealthResponse(
                status="unhealthy",
                db_connected=False,
                tables_ok=False,
                etl_status=str(boot.get("etl_status", "unknown")),
                gold_ready=False,
                last_pipeline_run=_parse_ts(boot.get("finished_at")),
                row_counts=boot.get("validation", {}).get("row_counts", {}),
            )

        gold_ready = validation.gold_ready
        tables_ok = validation.tables_ok
        etl_status = str(boot.get("etl_status") or ("success" if gold_ready else "degraded"))

        if db_connected and tables_ok and gold_ready:
            status = "healthy"
        elif db_connected:
            status = "degraded"
        else:
            status = "unhealthy"

        return SystemHealthResponse(
            status=status,
            db_connected=db_connected,
            tables_ok=tables_ok,
            etl_status=etl_status,
            gold_ready=gold_ready,
            last_pipeline_run=_parse_ts(boot.get("finished_at")) or self._last_etl_timestamp(),
            row_counts=validation.row_counts,
        )

    def get_status(self) -> EnterpriseHealthResponse:
        """Legacy compact health (backward compatible)."""
        system = self.get_system_health()
        return EnterpriseHealthResponse(
            status="ok" if system.status == "healthy" else system.status,
            db="connected" if system.db_connected else "disconnected",
            etl=system.etl_status,
            last_run=system.last_pipeline_run.date() if system.last_pipeline_run else None,
            tables=len(self._client.list_tables()) if system.db_connected else 0,
            gold_tables=sum(1 for t in GOLD_TABLES if table_exists(self._client, t)),
        )

    def _last_etl_timestamp(self) -> datetime | None:
        if table_exists(self._client, "agg_dashboard_cache"):
            row = self._client.fetch_one(
                "SELECT MAX(computed_at) AS ts FROM agg_dashboard_cache",
                label="health_last_cache",
            )
            if row and row.get("ts"):
                return _coerce_datetime(row["ts"])

        if table_exists(self._client, "agg_daily_streams"):
            row = self._client.fetch_one(
                "SELECT MAX(fecha) AS last_date FROM agg_daily_streams",
                label="health_last_gold_date",
            )
            if row and row.get("last_date"):
                val = row["last_date"]
                if isinstance(val, datetime):
                    return val
                if isinstance(val, date):
                    return datetime.combine(val, datetime.min.time(), tzinfo=timezone.utc)
        return None


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _coerce_datetime(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time(), tzinfo=timezone.utc)
    return None
