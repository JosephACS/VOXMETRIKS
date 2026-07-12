"""Business analytics use cases — Spec 023.

Reuses existing warehouse analytics tables; KPI catalog is metadata wrapper.
"""

from __future__ import annotations

import json
from typing import Any, Optional

import duckdb

from app.core.time_util import utc_now
from app.packages.business_analytics.domain.entities import (
    AnalyticsViewPreference,
    BusinessAlert,
    DataQualityResult,
    KpiDefinition,
    KpiSnapshot,
    MetricSource,
    RecommendationRecord,
)
from app.packages.business_analytics.domain.errors import NotFoundError, ValidationError

_KPI_COLS = (
    "id", "code", "name", "formula_description", "version", "granularity", "frequency",
    "owner_role", "null_handling", "source_type", "status", "created_at", "updated_at",
)


def _next_id(conn: duckdb.DuckDBPyConnection, table: str) -> int:
    return int(conn.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table}").fetchone()[0])


def _now():
    return utc_now()


def _audit(conn, *, action: str, target_type: str, target_id: str,
           actor_user_id: Optional[int], organization_id: Optional[int] = None,
           request_id: Optional[str] = None) -> None:
    try:
        from app.packages.organizations.infrastructure.repositories.audit_repository import AuditRepository
        AuditRepository(conn).append(
            action=action, target_type=target_type, target_id=target_id,
            source="business_analytics.use_case", result="success",
            actor_user_id=actor_user_id, organization_id=organization_id,
            request_id=request_id,
        )
    except Exception:
        pass


def _map_kpi(row: tuple) -> KpiDefinition:
    return KpiDefinition(**dict(zip(_KPI_COLS, row)))


def _warehouse_value(conn: duckdb.DuckDBPyConnection, kpi_code: str) -> tuple[Optional[float], str, str]:
    """Return (value, source_label, quality_status) from warehouse."""
    try:
        if kpi_code == "total_streams":
            row = conn.execute("SELECT COUNT(*) FROM fact_streaming").fetchone()
            return float(row[0]) if row else None, "warehouse:fact_streaming", "ok"
        if kpi_code == "daily_streams":
            row = conn.execute(
                "SELECT COALESCE(SUM(total_streams), 0) FROM agg_daily_streams"
            ).fetchone()
            return float(row[0]) if row else None, "warehouse:agg_daily_streams", "ok"
        if kpi_code == "skip_rate":
            row = conn.execute("""
                SELECT CASE WHEN COUNT(*) = 0 THEN NULL
                    ELSE ROUND(SUM(CASE WHEN skipped THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2)
                END FROM fact_streaming
            """).fetchone()
            val = float(row[0]) if row and row[0] is not None else None
            quality = "ok" if val is not None else "null_value"
            return val, "warehouse:fact_streaming", quality
    except Exception:
        return None, "warehouse:unavailable", "fail"
    return None, "warehouse:unknown", "fail"


class KpiCatalogUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def list(self, *, status: Optional[str] = None) -> list[KpiDefinition]:
        where = "1=1"
        params: list[Any] = []
        if status:
            where += " AND status = ?"
            params.append(status)
        rows = self._conn.execute(
            f"SELECT {', '.join(_KPI_COLS)} FROM app_kpi_definition WHERE {where} ORDER BY code, version DESC",
            params,
        ).fetchall()
        return [_map_kpi(r) for r in rows]

    def get_by_code(self, code: str, version: Optional[int] = None) -> KpiDefinition:
        if version:
            row = self._conn.execute(
                f"SELECT {', '.join(_KPI_COLS)} FROM app_kpi_definition WHERE code = ? AND version = ?",
                [code, version],
            ).fetchone()
        else:
            row = self._conn.execute(
                f"SELECT {', '.join(_KPI_COLS)} FROM app_kpi_definition WHERE code = ? ORDER BY version DESC LIMIT 1",
                [code],
            ).fetchone()
        if not row:
            raise NotFoundError(f"KPI {code} not found")
        return _map_kpi(row)

    def create_version(
        self, code: str, *, name: str, formula_description: str,
        null_handling: str = "exclude", source_type: str = "warehouse",
        actor_user_id: Optional[int] = None,
    ) -> KpiDefinition:
        if null_handling not in ("exclude", "zero", "fail"):
            raise ValidationError("Invalid null_handling")
        latest = self._conn.execute(
            "SELECT COALESCE(MAX(version), 0) FROM app_kpi_definition WHERE code = ?", [code]
        ).fetchone()[0]
        now = _now()
        kid = _next_id(self._conn, "app_kpi_definition")
        self._conn.execute(
            f"""
            INSERT INTO app_kpi_definition
                (id, code, name, formula_description, version, granularity, frequency,
                 owner_role, null_handling, source_type, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'daily', 'daily', 'analyst', ?, ?, 'active', ?, ?)
            """,
            [kid, code, name, formula_description, int(latest) + 1, null_handling, source_type, now, now],
        )
        return self.get_by_code(code, version=int(latest) + 1)


class KpiSnapshotUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def capture(
        self, kpi_code: str, *, organization_id: Optional[int], period: str,
        is_synthetic: bool = False, actor_user_id: Optional[int] = None,
    ) -> KpiSnapshot:
        kpi = KpiCatalogUseCases(self._conn).get_by_code(kpi_code)
        value: Optional[float] = None
        source_label = kpi.source_type
        quality = "ok"

        if kpi_code == "campaign_roi":
            if organization_id:
                row = self._conn.execute(
                    """
                    SELECT roi_value, status, unavailable_reason FROM app_campaign_roi_snapshot
                    WHERE organization_id = ? ORDER BY id DESC LIMIT 1
                    """,
                    [organization_id],
                ).fetchone()
                if row and row[1] == "available" and row[0] is not None:
                    value = float(row[0])
                    source_label = "campaigns:roi_snapshot"
                else:
                    value = None
                    quality = "roi_unavailable"
                    source_label = "campaigns:roi_snapshot"
            else:
                value = None
                quality = "roi_unavailable"
        elif kpi_code in ("active_mrr", "active_arr", "past_due_mrr"):
            if organization_id is None:
                value = None
                quality = "org_required"
                source_label = "subscriptions:plan_price"
            else:
                from app.packages.business_analytics.application.recurring_revenue import (
                    compute_recurring_revenue,
                )
                rev = compute_recurring_revenue(self._conn, organization_id=organization_id)
                source_label = rev["source_label"]
                if kpi_code == "active_mrr":
                    value = rev["active_mrr"]
                    quality = rev["quality_status"] if value is None else "ok"
                elif kpi_code == "active_arr":
                    value = rev["active_arr"]
                    quality = rev["quality_status"] if value is None else "ok"
                else:
                    past = rev["past_due_by_currency"]
                    if len(past) == 1:
                        value = past[0]["mrr"]
                        quality = "ok"
                    elif len(past) == 0:
                        value = None
                        quality = "no_past_due_recurring"
                    else:
                        value = None
                        quality = "multi_currency_no_fx"
        elif kpi.source_type.startswith("warehouse"):
            value, source_label, quality = _warehouse_value(self._conn, kpi_code)
            if value is None and kpi.null_handling == "zero":
                value = 0.0
                quality = "zero_substituted"
            elif value is None and kpi.null_handling == "fail":
                quality = "fail"
        else:
            value, source_label, quality = _warehouse_value(self._conn, kpi_code)

        now = _now()
        sid = _next_id(self._conn, "app_kpi_snapshot")
        self._conn.execute(
            """
            INSERT INTO app_kpi_snapshot
                (id, kpi_definition_id, organization_id, period, value, quality_status,
                 source_label, is_synthetic, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [sid, kpi.id, organization_id, period, value, quality, source_label, is_synthetic, now],
        )
        row = self._conn.execute(
            "SELECT id, kpi_definition_id, organization_id, period, value, quality_status, "
            "source_label, is_synthetic, created_at FROM app_kpi_snapshot WHERE id = ?",
            [sid],
        ).fetchone()
        _audit(self._conn, action="kpi_snapshot.captured", target_type="kpi_snapshot",
               target_id=str(sid), actor_user_id=actor_user_id, organization_id=organization_id)
        return KpiSnapshot(*row)

    def list(
        self, *, organization_id: Optional[int] = None, kpi_code: Optional[str] = None,
        limit: int = 50,
    ) -> list[KpiSnapshot]:
        where = "1=1"
        params: list[Any] = []
        if organization_id is not None:
            where += " AND s.organization_id = ?"
            params.append(organization_id)
        if kpi_code:
            where += " AND d.code = ?"
            params.append(kpi_code)
        rows = self._conn.execute(
            f"""
            SELECT s.id, s.kpi_definition_id, s.organization_id, s.period, s.value,
                   s.quality_status, s.source_label, s.is_synthetic, s.created_at
            FROM app_kpi_snapshot s
            JOIN app_kpi_definition d ON d.id = s.kpi_definition_id
            WHERE {where}
            ORDER BY s.id DESC LIMIT ?
            """,
            params + [limit],
        ).fetchall()
        return [KpiSnapshot(*r) for r in rows]


class MetricSourceUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def list(self) -> list[MetricSource]:
        rows = self._conn.execute(
            "SELECT id, code, label, origin_system, description, created_at FROM app_metric_source ORDER BY code"
        ).fetchall()
        return [MetricSource(*r) for r in rows]


class DataQualityUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def run_check(
        self, check_code: str, *, organization_id: Optional[int] = None,
        actor_user_id: Optional[int] = None,
    ) -> DataQualityResult:
        now = _now()
        status = "pass"
        details = "OK"
        if check_code == "warehouse_streams_present":
            try:
                cnt = self._conn.execute("SELECT COUNT(*) FROM fact_streaming").fetchone()[0]
                if int(cnt) == 0:
                    status, details = "warn", "fact_streaming empty"
            except Exception as exc:
                status, details = "fail", str(exc)
        elif check_code == "kpi_null_handling":
            status, details = "pass", "null_handling policies configured"
        else:
            status, details = "warn", f"Unknown check {check_code}"

        qid = _next_id(self._conn, "app_data_quality_result")
        self._conn.execute(
            """
            INSERT INTO app_data_quality_result
                (id, check_code, organization_id, status, details, measured_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [qid, check_code, organization_id, status, details, now, now],
        )
        row = self._conn.execute(
            "SELECT id, check_code, organization_id, status, details, measured_at, created_at "
            "FROM app_data_quality_result WHERE id = ?",
            [qid],
        ).fetchone()
        return DataQualityResult(*row)

    def list(self, organization_id: Optional[int] = None) -> list[DataQualityResult]:
        if organization_id:
            rows = self._conn.execute(
                "SELECT id, check_code, organization_id, status, details, measured_at, created_at "
                "FROM app_data_quality_result WHERE organization_id IS NULL OR organization_id = ? "
                "ORDER BY id DESC",
                [organization_id],
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT id, check_code, organization_id, status, details, measured_at, created_at "
                "FROM app_data_quality_result ORDER BY id DESC"
            ).fetchall()
        return [DataQualityResult(*r) for r in rows]


class BusinessAlertUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def create(
        self, organization_id: int, *, severity: str, title: str, body: str,
        kpi_code: Optional[str] = None, actor_user_id: Optional[int] = None,
    ) -> BusinessAlert:
        now = _now()
        aid = _next_id(self._conn, "app_business_alert")
        self._conn.execute(
            """
            INSERT INTO app_business_alert
                (id, organization_id, severity, title, body, status, kpi_code, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'open', ?, ?, ?)
            """,
            [aid, organization_id, severity, title, body, kpi_code, now, now],
        )
        row = self._conn.execute(
            "SELECT id, organization_id, severity, title, body, status, kpi_code, created_at, updated_at "
            "FROM app_business_alert WHERE id = ?",
            [aid],
        ).fetchone()
        _audit(self._conn, action="business_alert.created", target_type="business_alert",
               target_id=str(aid), actor_user_id=actor_user_id, organization_id=organization_id)
        return BusinessAlert(*row)

    def ack(self, alert_id: int, organization_id: int, *, actor_user_id: int) -> BusinessAlert:
        row = self._conn.execute(
            "SELECT id FROM app_business_alert WHERE id = ? AND organization_id = ?",
            [alert_id, organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"Alert {alert_id} not found")
        now = _now()
        self._conn.execute(
            "UPDATE app_business_alert SET status = 'acked', updated_at = ? WHERE id = ?",
            [now, alert_id],
        )
        row2 = self._conn.execute(
            "SELECT id, organization_id, severity, title, body, status, kpi_code, created_at, updated_at "
            "FROM app_business_alert WHERE id = ?",
            [alert_id],
        ).fetchone()
        return BusinessAlert(*row2)

    def list(self, organization_id: int, *, status: Optional[str] = None) -> list[BusinessAlert]:
        where = "organization_id = ?"
        params: list[Any] = [organization_id]
        if status:
            where += " AND status = ?"
            params.append(status)
        rows = self._conn.execute(
            f"SELECT id, organization_id, severity, title, body, status, kpi_code, created_at, updated_at "
            f"FROM app_business_alert WHERE {where} ORDER BY id DESC",
            params,
        ).fetchall()
        return [BusinessAlert(*r) for r in rows]


class RecommendationUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def generate_rule_based(self, organization_id: int) -> list[RecommendationRecord]:
        """Rule-based recommendations only — never labeled as AI."""
        now = _now()
        recs: list[RecommendationRecord] = []
        rules = []

        skip_snap = KpiSnapshotUseCases(self._conn).capture(
            "skip_rate", organization_id=organization_id, period=now.date().isoformat(),
        )
        if skip_snap.value and skip_snap.value > 30:
            rules.append((
                "high_skip_rate",
                "Review playlist curation",
                f"Skip rate is {skip_snap.value}% (warehouse:fact_streaming)",
                "kpi_snapshot:skip_rate",
            ))

        roi_snap = self._conn.execute(
            "SELECT status, unavailable_reason FROM app_campaign_roi_snapshot "
            "WHERE organization_id = ? ORDER BY id DESC LIMIT 1",
            [organization_id],
        ).fetchone()
        if roi_snap and roi_snap[0] == "unavailable":
            rules.append((
                "campaign_roi_missing",
                "Complete campaign attribution before ROI decisions",
                f"ROI unavailable: {roi_snap[1]}",
                "campaigns:roi_snapshot",
            ))

        for rule_code, title, rationale, evidence in rules:
            rid = _next_id(self._conn, "app_recommendation_record")
            self._conn.execute(
                """
                INSERT INTO app_recommendation_record
                    (id, organization_id, rule_code, title, rationale, evidence_ref, is_ai, created_at)
                VALUES (?, ?, ?, ?, ?, ?, FALSE, ?)
                """,
                [rid, organization_id, rule_code, title, rationale, evidence, now],
            )
            row = self._conn.execute(
                "SELECT id, organization_id, rule_code, title, rationale, evidence_ref, is_ai, created_at "
                "FROM app_recommendation_record WHERE id = ?",
                [rid],
            ).fetchone()
            recs.append(RecommendationRecord(*row))
        return recs

    def list(self, organization_id: int) -> list[RecommendationRecord]:
        rows = self._conn.execute(
            "SELECT id, organization_id, rule_code, title, rationale, evidence_ref, is_ai, created_at "
            "FROM app_recommendation_record WHERE organization_id = ? ORDER BY id DESC",
            [organization_id],
        ).fetchall()
        return [RecommendationRecord(*r) for r in rows]


class AnalyticsDashboardUseCases:
    """Enterprise dashboard aggregating warehouse + KPI catalog."""

    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def overview(self, organization_id: int) -> dict[str, Any]:
        snap_uc = KpiSnapshotUseCases(self._conn)
        period = _now().date().isoformat()
        kpis = {}
        for code in (
            "total_streams", "daily_streams", "skip_rate",
            "active_mrr", "active_arr", "past_due_mrr",
        ):
            s = snap_uc.capture(code, organization_id=organization_id, period=period)
            kpis[code] = {
                "value": s.value,
                "source_label": s.source_label,
                "quality_status": s.quality_status,
                "is_synthetic": s.is_synthetic,
            }
        roi_snap = snap_uc.capture("campaign_roi", organization_id=organization_id, period=period)
        kpis["campaign_roi"] = {
            "value": roi_snap.value,
            "source_label": roi_snap.source_label,
            "quality_status": roi_snap.quality_status,
            "is_synthetic": roi_snap.is_synthetic,
        }
        from app.packages.business_analytics.application.recurring_revenue import (
            compute_recurring_revenue,
        )
        recurring = compute_recurring_revenue(self._conn, organization_id=organization_id)
        return {
            "organization_id": organization_id,
            "period": period,
            "kpis": kpis,
            "recurring_revenue": recurring,
            "trends_stub": {"message": "Trend series available when historical snapshots exist"},
            "comparatives_stub": {"message": "Comparative views require multiple periods"},
        }

    def drill_down(
        self, organization_id: int, *, dimension: str, value: Optional[str] = None,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {"dimension": dimension, "organization_id": organization_id}
        if dimension == "campaign":
            rows = self._conn.execute(
                "SELECT id, name, status FROM app_campaign WHERE organization_id = ? LIMIT 20",
                [organization_id],
            ).fetchall()
            result["items"] = [{"id": r[0], "name": r[1], "status": r[2]} for r in rows]
        elif dimension == "engagement":
            val, label, quality = _warehouse_value(self._conn, "total_streams")
            result["engagement"] = {"streams": val, "source_label": label, "quality": quality}
        elif dimension == "market" and value:
            rows = self._conn.execute(
                "SELECT id, name, status FROM app_campaign WHERE organization_id = ? AND market = ?",
                [organization_id, value],
            ).fetchall()
            result["campaigns"] = [{"id": r[0], "name": r[1]} for r in rows]
        else:
            result["message"] = "Drill-down data not available for this dimension"
        return result


class ViewPreferenceUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def save(
        self, user_id: int, organization_id: int, *, view_key: str, payload: dict,
    ) -> AnalyticsViewPreference:
        now = _now()
        existing = self._conn.execute(
            "SELECT id FROM app_analytics_view_preference WHERE user_id = ? AND organization_id = ? "
            "AND view_key = ?",
            [user_id, organization_id, view_key],
        ).fetchone()
        payload_json = json.dumps(payload)
        if existing:
            self._conn.execute(
                "UPDATE app_analytics_view_preference SET payload_json = ?, updated_at = ? WHERE id = ?",
                [payload_json, now, existing[0]],
            )
            vid = int(existing[0])
        else:
            vid = _next_id(self._conn, "app_analytics_view_preference")
            self._conn.execute(
                """
                INSERT INTO app_analytics_view_preference
                    (id, user_id, organization_id, view_key, payload_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [vid, user_id, organization_id, view_key, payload_json, now, now],
            )
        row = self._conn.execute(
            "SELECT id, user_id, organization_id, view_key, payload_json, created_at, updated_at "
            "FROM app_analytics_view_preference WHERE id = ?",
            [vid],
        ).fetchone()
        return AnalyticsViewPreference(*row)

    def get(self, user_id: int, organization_id: int, view_key: str) -> Optional[AnalyticsViewPreference]:
        row = self._conn.execute(
            "SELECT id, user_id, organization_id, view_key, payload_json, created_at, updated_at "
            "FROM app_analytics_view_preference WHERE user_id = ? AND organization_id = ? AND view_key = ?",
            [user_id, organization_id, view_key],
        ).fetchone()
        return AnalyticsViewPreference(*row) if row else None
