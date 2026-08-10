"""Strategic AGG read model — Spec 049 / TAF14.

Longitudinal table agg_strategic_kpi_period refreshed from existing sources.
Never coerces unknown values to zero. No FX. No invented SLA / churn / security %.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Optional

import duckdb

from app.core.database import transactional
from app.core.time_util import utc_now
from app.packages.business_analytics.application.recurring_revenue import (
    compute_recurring_revenue,
)
from app.packages.business_analytics.application.use_cases import _warehouse_value

OFFICIAL_OBJECTIVES: tuple[tuple[str, str], ...] = (
    ("OE-01", "Aumentar organizaciones activas"),
    ("OE-02", "Generar ingresos recurrentes"),
    ("OE-03", "Mejorar renovación"),
    ("OE-04", "Demostrar valor mediante ROI"),
    ("OE-05", "Aumentar adopción"),
    ("OE-06", "Garantizar calidad de datos"),
    ("OE-07", "Proteger información empresarial"),
    ("OE-08", "Mantener sostenibilidad operativa"),
)

OBJECTIVE_TITLES = {code: title for code, title in OFFICIAL_OBJECTIVES}

EVIDENCE_PATHS: dict[str, str] = {
    "OE-02": "/business-analytics/kpis",
    "OE-03": "/subscriptions/overview",
    "OE-04": "/campaigns",
    "OE-05": "/business-analytics/kpis",
    "OE-06": "/business-analytics/quality",
    "OE-08": "/business-analytics/alerts",
}

REPORT_PATH = "/reports"
DECISION_PATH = "/business-decisions"

_ROW_COLS = (
    "id",
    "organization_id",
    "objective_code",
    "kpi_code",
    "period_start",
    "period_end",
    "value",
    "unit",
    "source_label",
    "quality_status",
    "is_synthetic",
    "is_proxy",
    "availability_status",
    "unavailable_reason",
    "computed_at",
)


@dataclass(frozen=True)
class StrategicKpiRow:
    organization_id: Optional[int]
    objective_code: str
    kpi_code: str
    period_start: date
    period_end: date
    value: Optional[float]
    unit: str
    source_label: str
    quality_status: str
    is_synthetic: bool
    is_proxy: bool
    availability_status: str
    unavailable_reason: Optional[str]
    computed_at: datetime


def default_period(as_of: Optional[date] = None) -> tuple[date, date]:
    today = as_of or utc_now().date()
    start = date(today.year, today.month, 1)
    last_day = calendar.monthrange(today.year, today.month)[1]
    end = date(today.year, today.month, last_day)
    if end > today:
        end = today
    return start, end


def _next_id(conn: duckdb.DuckDBPyConnection) -> int:
    return int(
        conn.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM agg_strategic_kpi_period").fetchone()[0]
    )


def _table_exists(conn: duckdb.DuckDBPyConnection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM information_schema.tables WHERE table_name = ? LIMIT 1",
        [name],
    ).fetchone()
    return bool(row)


def _classification_flags(conn: duckdb.DuckDBPyConnection, *, warehouse_backed: bool) -> tuple[bool, bool]:
    """Return (is_synthetic, is_proxy) for warehouse-derived metrics."""
    if not warehouse_backed:
        return False, False
    try:
        from app.packages.identity.services.data_classification import (
            SYNTHETIC,
            classify_warehouse_activity,
        )

        label = classify_warehouse_activity(conn)
        is_synthetic = label == SYNTHETIC
        # Academic warehouse activity used as adoption proxy when synthetic/demo/unknown.
        is_proxy = label in (SYNTHETIC, "demo", "mixed", "unknown")
        return is_synthetic, is_proxy
    except Exception:
        return False, True


def _row(
    *,
    organization_id: Optional[int],
    objective_code: str,
    kpi_code: str,
    period_start: date,
    period_end: date,
    value: Optional[float],
    unit: str,
    source_label: str,
    quality_status: str,
    is_synthetic: bool = False,
    is_proxy: bool = False,
    unavailable_reason: Optional[str] = None,
    computed_at: Optional[datetime] = None,
) -> StrategicKpiRow:
    if value is None:
        availability = "unavailable"
        reason = unavailable_reason or quality_status or "value_unavailable"
        # Never store zero for unknown — leave value as None.
        stored: Optional[float] = None
    else:
        availability = "available"
        reason = None
        stored = float(value)
    return StrategicKpiRow(
        organization_id=organization_id,
        objective_code=objective_code,
        kpi_code=kpi_code,
        period_start=period_start,
        period_end=period_end,
        value=stored,
        unit=unit,
        source_label=source_label,
        quality_status=quality_status,
        is_synthetic=is_synthetic,
        is_proxy=is_proxy,
        availability_status=availability,
        unavailable_reason=reason,
        computed_at=computed_at or utc_now(),
    )


def _compute_oe01(
    conn: duckdb.DuckDBPyConnection,
    *,
    organization_id: Optional[int],
    period_start: date,
    period_end: date,
    include_global: bool,
) -> list[StrategicKpiRow]:
    rows: list[StrategicKpiRow] = []
    if organization_id is not None:
        try:
            member_cnt = conn.execute(
                """
                SELECT COUNT(*) FROM app_organization_member
                WHERE organization_id = ? AND status = 'active'
                """,
                [organization_id],
            ).fetchone()
            sub_cnt = conn.execute(
                """
                SELECT COUNT(*) FROM app_subscription
                WHERE organization_id = ? AND status IN ('active', 'trialing', 'past_due')
                """,
                [organization_id],
            ).fetchone()
            active_members = float(member_cnt[0]) if member_cnt else None
            active_subs = float(sub_cnt[0]) if sub_cnt else None
            rows.append(
                _row(
                    organization_id=organization_id,
                    objective_code="OE-01",
                    kpi_code="active_members",
                    period_start=period_start,
                    period_end=period_end,
                    value=active_members,
                    unit="count",
                    source_label="organizations:membership",
                    quality_status="ok" if active_members is not None else "schema_unavailable",
                )
            )
            rows.append(
                _row(
                    organization_id=organization_id,
                    objective_code="OE-01",
                    kpi_code="org_active_subscriptions",
                    period_start=period_start,
                    period_end=period_end,
                    value=active_subs,
                    unit="count",
                    source_label="subscriptions:status",
                    quality_status="ok" if active_subs is not None else "schema_unavailable",
                )
            )
        except duckdb.CatalogException:
            rows.append(
                _row(
                    organization_id=organization_id,
                    objective_code="OE-01",
                    kpi_code="active_members",
                    period_start=period_start,
                    period_end=period_end,
                    value=None,
                    unit="count",
                    source_label="organizations:membership",
                    quality_status="schema_unavailable",
                    unavailable_reason="membership_or_subscription_tables_missing",
                )
            )
    if include_global:
        try:
            org_cnt = conn.execute(
                "SELECT COUNT(*) FROM app_organization WHERE status = 'active'"
            ).fetchone()
            value = float(org_cnt[0]) if org_cnt else None
            rows.append(
                _row(
                    organization_id=None,
                    objective_code="OE-01",
                    kpi_code="platform_active_organizations",
                    period_start=period_start,
                    period_end=period_end,
                    value=value,
                    unit="count",
                    source_label="organizations:status",
                    quality_status="ok" if value is not None else "schema_unavailable",
                )
            )
        except duckdb.CatalogException:
            rows.append(
                _row(
                    organization_id=None,
                    objective_code="OE-01",
                    kpi_code="platform_active_organizations",
                    period_start=period_start,
                    period_end=period_end,
                    value=None,
                    unit="count",
                    source_label="organizations:status",
                    quality_status="schema_unavailable",
                    unavailable_reason="organization_table_missing",
                )
            )
    return rows


def _compute_oe02(
    conn: duckdb.DuckDBPyConnection,
    *,
    organization_id: int,
    period_start: date,
    period_end: date,
) -> list[StrategicKpiRow]:
    rev = compute_recurring_revenue(conn, organization_id=organization_id)
    source = rev.get("source_label") or "subscriptions:plan_price"
    quality = rev.get("quality_status") or "ok"
    rows = [
        _row(
            organization_id=organization_id,
            objective_code="OE-02",
            kpi_code="active_mrr",
            period_start=period_start,
            period_end=period_end,
            value=rev.get("active_mrr"),
            unit=rev.get("primary_currency") or "currency",
            source_label=source,
            quality_status=quality if rev.get("active_mrr") is None else "ok",
            unavailable_reason=None if rev.get("active_mrr") is not None else quality,
        ),
        _row(
            organization_id=organization_id,
            objective_code="OE-02",
            kpi_code="active_arr",
            period_start=period_start,
            period_end=period_end,
            value=rev.get("active_arr"),
            unit=rev.get("primary_currency") or "currency",
            source_label=source,
            quality_status=quality if rev.get("active_arr") is None else "ok",
            unavailable_reason=None if rev.get("active_arr") is not None else quality,
        ),
    ]
    # Preserve multi-currency breakdown without inventing FX for a single KPI.
    for bucket in rev.get("active_by_currency") or []:
        ccy = bucket.get("currency")
        if not ccy:
            continue
        rows.append(
            _row(
                organization_id=organization_id,
                objective_code="OE-02",
                kpi_code=f"active_mrr_{ccy}",
                period_start=period_start,
                period_end=period_end,
                value=bucket.get("mrr"),
                unit=str(ccy),
                source_label=source,
                quality_status="ok",
            )
        )
    return rows


def _compute_oe03(
    conn: duckdb.DuckDBPyConnection,
    *,
    organization_id: int,
    period_start: date,
    period_end: date,
) -> list[StrategicKpiRow]:
    rev = compute_recurring_revenue(conn, organization_id=organization_id)
    past = rev.get("past_due_by_currency") or []
    source = rev.get("source_label") or "subscriptions:plan_price"
    rows: list[StrategicKpiRow] = []
    if len(past) == 1:
        rows.append(
            _row(
                organization_id=organization_id,
                objective_code="OE-03",
                kpi_code="past_due_mrr",
                period_start=period_start,
                period_end=period_end,
                value=past[0].get("mrr"),
                unit=past[0].get("currency") or "currency",
                source_label=source,
                quality_status="ok",
            )
        )
    elif len(past) == 0:
        rows.append(
            _row(
                organization_id=organization_id,
                objective_code="OE-03",
                kpi_code="past_due_mrr",
                period_start=period_start,
                period_end=period_end,
                value=None,
                unit="currency",
                source_label=source,
                quality_status="no_past_due_recurring",
                unavailable_reason="no_past_due_recurring",
            )
        )
    else:
        rows.append(
            _row(
                organization_id=organization_id,
                objective_code="OE-03",
                kpi_code="past_due_mrr",
                period_start=period_start,
                period_end=period_end,
                value=None,
                unit="currency",
                source_label=source,
                quality_status="multi_currency_no_fx",
                unavailable_reason="multi_currency_no_fx",
            )
        )
        for bucket in past:
            ccy = bucket.get("currency")
            if not ccy:
                continue
            rows.append(
                _row(
                    organization_id=organization_id,
                    objective_code="OE-03",
                    kpi_code=f"past_due_mrr_{ccy}",
                    period_start=period_start,
                    period_end=period_end,
                    value=bucket.get("mrr"),
                    unit=str(ccy),
                    source_label=source,
                    quality_status="ok",
                )
            )

    # CS risk count is a real signal — not churn/renewal_rate without denominator.
    try:
        if _table_exists(conn, "app_cs_risk"):
            risk = conn.execute(
                """
                SELECT COUNT(*) FROM app_cs_risk
                WHERE organization_id = ?
                  AND status IN ('open', 'intervention_required', 'monitoring')
                """,
                [organization_id],
            ).fetchone()
            rows.append(
                _row(
                    organization_id=organization_id,
                    objective_code="OE-03",
                    kpi_code="open_cs_risks",
                    period_start=period_start,
                    period_end=period_end,
                    value=float(risk[0]) if risk else None,
                    unit="count",
                    source_label="customer_success:risks",
                    quality_status="ok",
                )
            )
        else:
            rows.append(
                _row(
                    organization_id=organization_id,
                    objective_code="OE-03",
                    kpi_code="renewal_rate",
                    period_start=period_start,
                    period_end=period_end,
                    value=None,
                    unit="ratio",
                    source_label="customer_success:renewal",
                    quality_status="denominator_unavailable",
                    unavailable_reason="renewal_rate_requires_valid_denominator",
                )
            )
    except Exception:
        rows.append(
            _row(
                organization_id=organization_id,
                objective_code="OE-03",
                kpi_code="renewal_rate",
                period_start=period_start,
                period_end=period_end,
                value=None,
                unit="ratio",
                source_label="customer_success:renewal",
                quality_status="denominator_unavailable",
                unavailable_reason="renewal_rate_requires_valid_denominator",
            )
        )
    return rows


def _compute_oe04(
    conn: duckdb.DuckDBPyConnection,
    *,
    organization_id: int,
    period_start: date,
    period_end: date,
) -> list[StrategicKpiRow]:
    try:
        row = conn.execute(
            """
            SELECT roi_value, status, unavailable_reason FROM app_campaign_roi_snapshot
            WHERE organization_id = ? ORDER BY id DESC LIMIT 1
            """,
            [organization_id],
        ).fetchone()
    except duckdb.CatalogException:
        row = None
    if row and row[1] == "available" and row[0] is not None:
        return [
            _row(
                organization_id=organization_id,
                objective_code="OE-04",
                kpi_code="campaign_roi",
                period_start=period_start,
                period_end=period_end,
                value=float(row[0]),
                unit="ratio",
                source_label="campaigns:roi_snapshot",
                quality_status="ok",
                is_synthetic=False,
                is_proxy=False,
            )
        ]
    reason = None
    if row:
        reason = row[2] or row[1] or "roi_unavailable"
    else:
        reason = "roi_attribution_missing"
    return [
        _row(
            organization_id=organization_id,
            objective_code="OE-04",
            kpi_code="campaign_roi",
            period_start=period_start,
            period_end=period_end,
            value=None,
            unit="ratio",
            source_label="campaigns:roi_snapshot",
            quality_status="roi_unavailable",
            unavailable_reason=str(reason),
        )
    ]


def _compute_oe05(
    conn: duckdb.DuckDBPyConnection,
    *,
    organization_id: int,
    period_start: date,
    period_end: date,
) -> list[StrategicKpiRow]:
    value, source, quality = _warehouse_value(conn, "total_streams")
    is_synthetic, is_proxy = _classification_flags(conn, warehouse_backed=True)
    # Prefer skip_rate companion as secondary adoption signal when present.
    skip_val, skip_src, skip_q = _warehouse_value(conn, "skip_rate")
    rows = [
        _row(
            organization_id=organization_id,
            objective_code="OE-05",
            kpi_code="total_streams",
            period_start=period_start,
            period_end=period_end,
            value=value,
            unit="count",
            source_label=source,
            quality_status=quality if value is not None else (quality or "null_value"),
            is_synthetic=is_synthetic,
            is_proxy=is_proxy,
            unavailable_reason=None if value is not None else "adoption_activity_unavailable",
        )
    ]
    if skip_val is not None or skip_q:
        rows.append(
            _row(
                organization_id=organization_id,
                objective_code="OE-05",
                kpi_code="skip_rate",
                period_start=period_start,
                period_end=period_end,
                value=skip_val,
                unit="percent",
                source_label=skip_src,
                quality_status=skip_q,
                is_synthetic=is_synthetic,
                is_proxy=is_proxy,
                unavailable_reason=None if skip_val is not None else "skip_rate_unavailable",
            )
        )
    return rows


def _compute_oe06(
    conn: duckdb.DuckDBPyConnection,
    *,
    organization_id: int,
    period_start: date,
    period_end: date,
) -> list[StrategicKpiRow]:
    rows: list[StrategicKpiRow] = []
    try:
        if _table_exists(conn, "app_data_quality_result"):
            q = conn.execute(
                """
                SELECT status FROM app_data_quality_result
                WHERE organization_id IS NULL OR organization_id = ?
                ORDER BY id DESC LIMIT 1
                """,
                [organization_id],
            ).fetchone()
            if q:
                status = str(q[0])
                value = 1.0 if status == "pass" else (0.5 if status == "warn" else 0.0)
                # Explicit: fail/warn are measured results, not "unknown → zero".
                rows.append(
                    _row(
                        organization_id=organization_id,
                        objective_code="OE-06",
                        kpi_code="latest_quality_check",
                        period_start=period_start,
                        period_end=period_end,
                        value=value,
                        unit="score",
                        source_label="business_analytics:quality",
                        quality_status=status,
                    )
                )
            else:
                rows.append(
                    _row(
                        organization_id=organization_id,
                        objective_code="OE-06",
                        kpi_code="latest_quality_check",
                        period_start=period_start,
                        period_end=period_end,
                        value=None,
                        unit="score",
                        source_label="business_analytics:quality",
                        quality_status="no_quality_runs",
                        unavailable_reason="no_quality_runs",
                    )
                )
        else:
            rows.append(
                _row(
                    organization_id=organization_id,
                    objective_code="OE-06",
                    kpi_code="latest_quality_check",
                    period_start=period_start,
                    period_end=period_end,
                    value=None,
                    unit="score",
                    source_label="business_analytics:quality",
                    quality_status="schema_unavailable",
                    unavailable_reason="quality_table_missing",
                )
            )
    except Exception as exc:
        rows.append(
            _row(
                organization_id=organization_id,
                objective_code="OE-06",
                kpi_code="latest_quality_check",
                period_start=period_start,
                period_end=period_end,
                value=None,
                unit="score",
                source_label="business_analytics:quality",
                quality_status="fail",
                unavailable_reason=str(exc)[:200],
            )
        )

    try:
        if _table_exists(conn, "ctl_pipeline_stages"):
            stage = conn.execute(
                """
                SELECT COUNT(*) FROM ctl_pipeline_stages
                WHERE UPPER(COALESCE(status, '')) IN ('OK', 'SUCCESS', 'COMPLETED')
                """
            ).fetchone()
            rows.append(
                _row(
                    organization_id=organization_id,
                    objective_code="OE-06",
                    kpi_code="ctl_ok_stages",
                    period_start=period_start,
                    period_end=period_end,
                    value=float(stage[0]) if stage else None,
                    unit="count",
                    source_label="warehouse:ctl_pipeline_stages",
                    quality_status="ok",
                    is_proxy=True,
                )
            )
        else:
            rows.append(
                _row(
                    organization_id=organization_id,
                    objective_code="OE-06",
                    kpi_code="ctl_ok_stages",
                    period_start=period_start,
                    period_end=period_end,
                    value=None,
                    unit="count",
                    source_label="warehouse:ctl_pipeline_stages",
                    quality_status="schema_unavailable",
                    unavailable_reason="ctl_pipeline_stages_missing",
                )
            )
    except Exception:
        rows.append(
            _row(
                organization_id=organization_id,
                objective_code="OE-06",
                kpi_code="ctl_ok_stages",
                period_start=period_start,
                period_end=period_end,
                value=None,
                unit="count",
                source_label="warehouse:ctl_pipeline_stages",
                quality_status="fail",
                unavailable_reason="ctl_pipeline_stages_query_failed",
            )
        )
    return rows


def _compute_oe07(
    conn: duckdb.DuckDBPyConnection,
    *,
    organization_id: int,
    period_start: date,
    period_end: date,
) -> list[StrategicKpiRow]:
    rows: list[StrategicKpiRow] = []
    # Evidence counts only — never invent a security percentage.
    try:
        if _table_exists(conn, "app_audit_log"):
            audit = conn.execute(
                """
                SELECT COUNT(*) FROM app_audit_log
                WHERE organization_id = ?
                """,
                [organization_id],
            ).fetchone()
            rows.append(
                _row(
                    organization_id=organization_id,
                    objective_code="OE-07",
                    kpi_code="audit_events",
                    period_start=period_start,
                    period_end=period_end,
                    value=float(audit[0]) if audit else None,
                    unit="count",
                    source_label="organizations:audit_log",
                    quality_status="ok",
                )
            )
        else:
            rows.append(
                _row(
                    organization_id=organization_id,
                    objective_code="OE-07",
                    kpi_code="audit_events",
                    period_start=period_start,
                    period_end=period_end,
                    value=None,
                    unit="count",
                    source_label="organizations:audit_log",
                    quality_status="schema_unavailable",
                    unavailable_reason="audit_log_missing",
                )
            )
    except Exception:
        rows.append(
            _row(
                organization_id=organization_id,
                objective_code="OE-07",
                kpi_code="audit_events",
                period_start=period_start,
                period_end=period_end,
                value=None,
                unit="count",
                source_label="organizations:audit_log",
                quality_status="fail",
                unavailable_reason="audit_query_failed",
            )
        )

    rows.append(
        _row(
            organization_id=organization_id,
            objective_code="OE-07",
            kpi_code="security_coverage_pct",
            period_start=period_start,
            period_end=period_end,
            value=None,
            unit="percent",
            source_label="security:coverage",
            quality_status="undefined_metric",
            unavailable_reason="security_percentage_not_defined",
        )
    )
    return rows


def _compute_oe08(
    conn: duckdb.DuckDBPyConnection,
    *,
    organization_id: Optional[int],
    period_start: date,
    period_end: date,
    include_global: bool,
) -> list[StrategicKpiRow]:
    rows: list[StrategicKpiRow] = []
    if organization_id is not None:
        # Org-scoped: open business alerts as operational signal (not SLA).
        try:
            if _table_exists(conn, "app_business_alert"):
                alerts = conn.execute(
                    """
                    SELECT COUNT(*) FROM app_business_alert
                    WHERE organization_id = ? AND status = 'open'
                    """,
                    [organization_id],
                ).fetchone()
                rows.append(
                    _row(
                        organization_id=organization_id,
                        objective_code="OE-08",
                        kpi_code="open_business_alerts",
                        period_start=period_start,
                        period_end=period_end,
                        value=float(alerts[0]) if alerts else None,
                        unit="count",
                        source_label="business_analytics:alerts",
                        quality_status="ok",
                    )
                )
            else:
                rows.append(
                    _row(
                        organization_id=organization_id,
                        objective_code="OE-08",
                        kpi_code="open_business_alerts",
                        period_start=period_start,
                        period_end=period_end,
                        value=None,
                        unit="count",
                        source_label="business_analytics:alerts",
                        quality_status="schema_unavailable",
                        unavailable_reason="alerts_table_missing",
                    )
                )
        except Exception:
            rows.append(
                _row(
                    organization_id=organization_id,
                    objective_code="OE-08",
                    kpi_code="open_business_alerts",
                    period_start=period_start,
                    period_end=period_end,
                    value=None,
                    unit="count",
                    source_label="business_analytics:alerts",
                    quality_status="fail",
                    unavailable_reason="alerts_query_failed",
                )
            )
        rows.append(
            _row(
                organization_id=organization_id,
                objective_code="OE-08",
                kpi_code="sla_compliance",
                period_start=period_start,
                period_end=period_end,
                value=None,
                unit="ratio",
                source_label="ops:sla",
                quality_status="undefined_sla",
                unavailable_reason="sla_not_defined",
            )
        )

    if include_global:
        rows.append(
            _row(
                organization_id=None,
                objective_code="OE-08",
                kpi_code="platform_health_probe",
                period_start=period_start,
                period_end=period_end,
                value=None,
                unit="status",
                source_label="ops:health",
                quality_status="probe_not_cached",
                unavailable_reason="platform_health_requires_live_probe_not_cached_as_kpi",
            )
        )
    return rows


def compute_strategic_rows(
    conn: duckdb.DuckDBPyConnection,
    *,
    organization_id: Optional[int],
    period_start: date,
    period_end: date,
    include_global: bool = False,
) -> list[StrategicKpiRow]:
    rows: list[StrategicKpiRow] = []
    if organization_id is not None:
        rows.extend(
            _compute_oe01(
                conn,
                organization_id=organization_id,
                period_start=period_start,
                period_end=period_end,
                include_global=False,
            )
        )
        rows.extend(
            _compute_oe02(
                conn,
                organization_id=organization_id,
                period_start=period_start,
                period_end=period_end,
            )
        )
        rows.extend(
            _compute_oe03(
                conn,
                organization_id=organization_id,
                period_start=period_start,
                period_end=period_end,
            )
        )
        rows.extend(
            _compute_oe04(
                conn,
                organization_id=organization_id,
                period_start=period_start,
                period_end=period_end,
            )
        )
        rows.extend(
            _compute_oe05(
                conn,
                organization_id=organization_id,
                period_start=period_start,
                period_end=period_end,
            )
        )
        rows.extend(
            _compute_oe06(
                conn,
                organization_id=organization_id,
                period_start=period_start,
                period_end=period_end,
            )
        )
        rows.extend(
            _compute_oe07(
                conn,
                organization_id=organization_id,
                period_start=period_start,
                period_end=period_end,
            )
        )
        rows.extend(
            _compute_oe08(
                conn,
                organization_id=organization_id,
                period_start=period_start,
                period_end=period_end,
                include_global=False,
            )
        )
    if include_global:
        rows.extend(
            _compute_oe01(
                conn,
                organization_id=None,
                period_start=period_start,
                period_end=period_end,
                include_global=True,
            )
        )
        rows.extend(
            _compute_oe08(
                conn,
                organization_id=None,
                period_start=period_start,
                period_end=period_end,
                include_global=True,
            )
        )
    return rows


def refresh_strategic_kpi_period(
    conn: duckdb.DuckDBPyConnection,
    *,
    organization_id: Optional[int],
    period_start: Optional[date] = None,
    period_end: Optional[date] = None,
    include_global: bool = False,
    fail: bool = False,
) -> list[StrategicKpiRow]:
    """Transactional replace of strategic rows for the given scope+period."""
    if period_start is None or period_end is None:
        period_start, period_end = default_period()
    # Compute and replace under the process-wide DuckDB lock. Per-statement
    # locking cannot protect the DELETE -> INSERT unit from another request.
    with transactional(conn):
        rows = compute_strategic_rows(
            conn,
            organization_id=organization_id,
            period_start=period_start,
            period_end=period_end,
            include_global=include_global,
        )
        if fail:
            raise RuntimeError("forced_refresh_failure")
        # DuckDB ART indexes can reject reuse of deleted primary keys in the same
        # connection; keep a monotonic watermark across the replace.
        next_id = int(
            conn.execute("SELECT COALESCE(MAX(id), 0) FROM agg_strategic_kpi_period").fetchone()[0]
        )
        if organization_id is not None:
            conn.execute(
                """
                DELETE FROM agg_strategic_kpi_period
                WHERE organization_id = ?
                  AND period_start = ?
                  AND period_end = ?
                """,
                [organization_id, period_start, period_end],
            )
        if include_global:
            conn.execute(
                """
                DELETE FROM agg_strategic_kpi_period
                WHERE organization_id IS NULL
                  AND period_start = ?
                  AND period_end = ?
                """,
                [period_start, period_end],
            )
        for r in rows:
            next_id += 1
            conn.execute(
                f"""
                INSERT INTO agg_strategic_kpi_period
                    ({', '.join(_ROW_COLS)})
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    next_id,
                    r.organization_id,
                    r.objective_code,
                    r.kpi_code,
                    r.period_start,
                    r.period_end,
                    r.value,
                    r.unit,
                    r.source_label,
                    r.quality_status,
                    r.is_synthetic,
                    r.is_proxy,
                    r.availability_status,
                    r.unavailable_reason,
                    r.computed_at,
                ],
            )
    return rows


def _classification_badge(row: dict[str, Any]) -> str:
    if row.get("availability_status") == "unavailable" or row.get("value") is None:
        return "unavailable"
    if row.get("is_synthetic"):
        return "synthetic"
    if row.get("is_proxy"):
        return "proxy"
    if str(row.get("source_label") or "").startswith("campaigns:"):
        return "simulated"
    return "real"


def _primary_kpi_for_objective(rows: list[dict[str, Any]], objective_code: str) -> Optional[dict[str, Any]]:
    preferred = {
        "OE-01": ("active_members", "platform_active_organizations", "org_active_subscriptions"),
        "OE-02": ("active_mrr", "active_arr"),
        "OE-03": ("past_due_mrr", "open_cs_risks", "renewal_rate"),
        "OE-04": ("campaign_roi",),
        "OE-05": ("total_streams", "skip_rate", "daily_streams"),
        "OE-06": ("latest_quality_check", "ctl_ok_stages"),
        "OE-07": ("audit_events", "security_coverage_pct"),
        "OE-08": ("open_business_alerts", "platform_health_probe", "sla_compliance"),
    }.get(objective_code, ())
    by_code = {r["kpi_code"]: r for r in rows if r["objective_code"] == objective_code}
    for code in preferred:
        if code in by_code:
            return by_code[code]
    scoped = [r for r in rows if r["objective_code"] == objective_code]
    return scoped[0] if scoped else None


def list_strategic_rows(
    conn: duckdb.DuckDBPyConnection,
    *,
    organization_id: int,
    period_start: date,
    period_end: date,
    include_global: bool = False,
) -> list[dict[str, Any]]:
    params: list[Any] = [organization_id, period_start, period_end]
    where = "organization_id = ? AND period_start = ? AND period_end = ?"
    if include_global:
        where = (
            "((organization_id = ? AND period_start = ? AND period_end = ?) "
            "OR (organization_id IS NULL AND period_start = ? AND period_end = ?))"
        )
        params = [organization_id, period_start, period_end, period_start, period_end]
    raw = conn.execute(
        f"""
        SELECT {', '.join(_ROW_COLS)}
        FROM agg_strategic_kpi_period
        WHERE {where}
        ORDER BY objective_code, kpi_code, id
        """,
        params,
    ).fetchall()
    out: list[dict[str, Any]] = []
    for r in raw:
        item = dict(zip(_ROW_COLS, r))
        item["classification"] = _classification_badge(item)
        out.append(item)
    return out


def strategic_overview(
    conn: duckdb.DuckDBPyConnection,
    *,
    organization_id: int,
    include_global: bool = False,
    can_create_decision: bool = False,
    can_draft_report: bool = False,
    can_refresh_strategic: bool = False,
    auto_refresh: bool = False,
) -> dict[str, Any]:
    period_start, period_end = default_period()
    existing = list_strategic_rows(
        conn,
        organization_id=organization_id,
        period_start=period_start,
        period_end=period_end,
        include_global=include_global,
    )
    if auto_refresh and not existing:
        refresh_strategic_kpi_period(
            conn,
            organization_id=organization_id,
            period_start=period_start,
            period_end=period_end,
            include_global=include_global,
        )
        existing = list_strategic_rows(
            conn,
            organization_id=organization_id,
            period_start=period_start,
            period_end=period_end,
            include_global=include_global,
        )

    # Prior periods for trend (≥2 comparable periods required).
    prior_periods = conn.execute(
        """
        SELECT DISTINCT period_start, period_end
        FROM agg_strategic_kpi_period
        WHERE organization_id = ?
        ORDER BY period_start DESC
        LIMIT 5
        """,
        [organization_id],
    ).fetchall()
    comparable_periods = len(prior_periods)

    objectives: list[dict[str, Any]] = []
    for code, title in OFFICIAL_OBJECTIVES:
        primary = _primary_kpi_for_objective(existing, code)
        kpis = [r for r in existing if r["objective_code"] == code]
        trend = None
        if primary and comparable_periods >= 2:
            hist = conn.execute(
                """
                SELECT value, period_start FROM agg_strategic_kpi_period
                WHERE organization_id = ?
                  AND objective_code = ?
                  AND kpi_code = ?
                ORDER BY period_start DESC
                LIMIT 2
                """,
                [organization_id, code, primary["kpi_code"]],
            ).fetchall()
            if len(hist) >= 2 and hist[0][0] is not None and hist[1][0] is not None:
                trend = {
                    "current": float(hist[0][0]),
                    "previous": float(hist[1][0]),
                    "delta": float(hist[0][0]) - float(hist[1][0]),
                }
        evidence_path = EVIDENCE_PATHS.get(code)
        if code == "OE-01":
            evidence_path = f"/organizations/{organization_id}"
        elif code == "OE-07":
            evidence_path = f"/organizations/{organization_id}/audit"
        objectives.append(
            {
                "objective_code": code,
                "title": title,
                "kpi": primary,
                "kpis": kpis,
                "period_start": period_start.isoformat(),
                "period_end": period_end.isoformat(),
                "evidence_path": evidence_path,
                "report_path": REPORT_PATH,
                "decision_path": DECISION_PATH,
                "trend": trend,
                "empty": primary is None,
            }
        )

    return {
        "organization_id": organization_id,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "include_global": include_global,
        "comparable_periods": comparable_periods,
        "objectives": objectives,
        "decision_capability": {
            "can_create_decision": can_create_decision,
            "can_draft_report": can_draft_report,
            "can_refresh_strategic": can_refresh_strategic,
            "is_ai": False,
            "recommendation_mode": "rule_based",
        },
    }
