# -*- coding: utf-8 -*-
"""Workpanel — centro táctico (evaluación Construcción del Software)."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Optional

import duckdb

from app.core.database import table_exists


def _safe(conn: duckdb.DuckDBPyConnection, sql: str, params: list[Any] | None = None) -> Any:
    try:
        if params:
            return conn.execute(sql, params).fetchone()
        return conn.execute(sql).fetchone()
    except Exception:
        return None


def _count(conn: duckdb.DuckDBPyConnection, sql: str, params: list[Any] | None = None) -> Optional[int]:
    row = _safe(conn, sql, params)
    if row is None or row[0] is None:
        return None
    return int(row[0])


def _float(conn: duckdb.DuckDBPyConnection, sql: str, params: list[Any] | None = None) -> Optional[float]:
    row = _safe(conn, sql, params)
    if row is None or row[0] is None:
        return None
    return float(row[0])


def _parse_period(period: Optional[str]) -> tuple[date, date, str]:
    """Return (start, end_exclusive, label). Default: calendar month of today."""
    today = date.today()
    if period:
        try:
            y, m = period.split("-")
            start = date(int(y), int(m), 1)
            if m == "12":
                end = date(int(y) + 1, 1, 1)
            else:
                end = date(int(y), int(m) + 1, 1)
            return start, end, f"{start.year:04d}-{start.month:02d}"
        except Exception:
            pass
    start = date(today.year, today.month, 1)
    if today.month == 12:
        end = date(today.year + 1, 1, 1)
    else:
        end = date(today.year, today.month + 1, 1)
    return start, end, f"{start.year:04d}-{start.month:02d}"


def _month_labels_from_dates(values: list[Any]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for v in values:
        if v is None:
            continue
        if hasattr(v, "year") and hasattr(v, "month"):
            key = f"{int(v.year):04d}-{int(v.month):02d}"
        else:
            s = str(v)
            if len(s) >= 7 and s[4] == "-":
                key = s[:7]
            else:
                continue
        if key not in seen:
            seen.add(key)
            out.append(key)
    out.sort()
    return out


def _collect_available_periods(
    conn: duckdb.DuckDBPyConnection,
    *,
    organization_id: Optional[int],
) -> dict[str, list[str]]:
    """Union of YYYY-MM periods per scope source (spec 044)."""
    org_months: list[str] = []
    plat_months: list[str] = []
    global_months: list[str] = []

    if table_exists(conn, "agg_daily_streams"):
        try:
            rows = conn.execute(
                "SELECT DISTINCT fecha FROM agg_daily_streams WHERE fecha IS NOT NULL"
            ).fetchall()
            global_months = _month_labels_from_dates([r[0] for r in rows])
        except Exception:
            pass

    if organization_id is not None and table_exists(conn, "app_payment"):
        try:
            rows = conn.execute(
                """
                SELECT DISTINCT COALESCE(settled_at, created_at)
                FROM app_payment
                WHERE organization_id = ?
                """,
                [organization_id],
            ).fetchall()
            org_months = _month_labels_from_dates([r[0] for r in rows])
        except Exception:
            pass
    if organization_id is not None and table_exists(conn, "app_invoice") and not org_months:
        try:
            rows = conn.execute(
                """
                SELECT DISTINCT COALESCE(due_date, created_at)
                FROM app_invoice WHERE organization_id = ?
                """,
                [organization_id],
            ).fetchall()
            org_months = _month_labels_from_dates([r[0] for r in rows])
        except Exception:
            pass

    if table_exists(conn, "app_job_execution"):
        try:
            rows = conn.execute(
                """
                SELECT DISTINCT COALESCE(finished_at, started_at, created_at)
                FROM app_job_execution
                WHERE COALESCE(finished_at, started_at, created_at) IS NOT NULL
                """
            ).fetchall()
            plat_months = _month_labels_from_dates([r[0] for r in rows])
        except Exception:
            pass

    today = date.today()
    current = f"{today.year:04d}-{today.month:02d}"

    def _no_future(months: list[str]) -> list[str]:
        return [m for m in months if m <= current]

    return {
        "organization": _no_future(org_months),
        "platform": _no_future(plat_months),
        "global_analytics": _no_future(global_months),
    }


def resolve_workpanel_period(
    conn: duckdb.DuckDBPyConnection,
    *,
    period: Optional[str],
    organization_id: Optional[int],
    role: str,
) -> tuple[date, date, str, dict[str, Any]]:
    """Validate period against available months. Raises ValueError on bad input."""
    sources = _collect_available_periods(conn, organization_id=organization_id)
    role_l = (role or "user").lower()
    if role_l == "engineer":
        union = sorted(
            set(sources["platform"]) | set(sources["global_analytics"]) | set(sources["organization"])
        )
    else:
        union = sorted(
            set(sources["organization"]) | set(sources["global_analytics"]) | set(sources["platform"])
        )

    today = date.today()
    current = f"{today.year:04d}-{today.month:02d}"
    union = [m for m in union if m <= current]

    default = None
    if sources["global_analytics"]:
        default = sources["global_analytics"][-1]
    elif union:
        default = union[-1]

    meta = {
        "available_periods": union,
        "default_period": default,
        "period_sources": sources,
    }

    if period is None or str(period).strip() == "":
        if default is None:
            start, end, label = _parse_period(None)
            # Prefer warehouse max month inside _parse_period path via build — keep calendar only if empty
            return start, end, label, meta
        period = default

    p = str(period).strip()
    if len(p) != 7 or p[4] != "-":
        raise ValueError("invalid_period_format")
    if p > current:
        raise ValueError("future_period")
    if union and p not in union:
        raise ValueError("unknown_period")

    start, end, label = _parse_period(p)
    return start, end, label, meta


def _filter_metrics_for_role(metrics: list[dict[str, Any]], role: str) -> list[dict[str, Any]]:
    """Spec 044 — sectioned Workpanel: admin vs engineer visible metric ids."""
    r = (role or "user").lower()
    if r == "engineer":
        allow = {
            "failed_jobs",
            "active_subscriptions",
            "streams_period",
            "catalog_tracks",
            "playback_availability",
        }
    elif r == "admin":
        allow = {
            "income_collected",
            "invoices_pending",
            "open_opportunities",
            "open_alerts",
            "streams_period",
            "catalog_tracks",
            "playback_availability",
        }
    else:
        allow = set()
    return [m for m in metrics if m.get("id") in allow]


def _sections_for_role(role: str) -> list[dict[str, Any]]:
    r = (role or "user").lower()
    if r == "engineer":
        return [
            {
                "id": "platform",
                "title": "Estado técnico de la plataforma",
                "description": "Señales operativas generales de los procesos internos.",
                "badge": "Plataforma",
                "scope": "platform",
                "metric_ids": ["failed_jobs", "active_subscriptions"],
            },
            {
                "id": "global_analytics",
                "title": "Analítica y almacén de datos",
                "description": "Volumen, disponibilidad y reproducibilidad del catálogo analítico global.",
                "badge": "Analítica global",
                "scope": "global_analytics",
                "metric_ids": ["streams_period", "catalog_tracks", "playback_availability"],
                "quick_links": [{"label": "Ingeniería de datos", "path": "/elt-pipeline"}],
            },
        ]
    if r == "admin":
        return [
            {
                "id": "organization",
                "title": "Resumen de la organización activa",
                "description": "Indicadores operativos y comerciales de la organización seleccionada.",
                "badge": "Organización",
                "scope": "organization",
                "metric_ids": [
                    "income_collected",
                    "invoices_pending",
                    "open_opportunities",
                    "open_alerts",
                ],
            },
            {
                "id": "global_analytics",
                "title": "Analítica musical global",
                "description": (
                    "Actividad del catálogo analítico de VOXMETRIKS. "
                    "No representa únicamente a la organización seleccionada."
                ),
                "badge": "Analítica global",
                "scope": "global_analytics",
                "metric_ids": ["streams_period", "catalog_tracks", "playback_availability"],
            },
        ]
    return []



def _prev_period(start: date) -> tuple[date, date]:
    if start.month == 1:
        p_start = date(start.year - 1, 12, 1)
        p_end = start
    else:
        p_start = date(start.year, start.month - 1, 1)
        p_end = start
    return p_start, p_end


def _metric(
    *,
    id: str,
    label: str,
    value: Optional[float | int],
    unit: str,
    period: str,
    explanation: str,
    detail_path: str,
    available: bool,
    previous: Optional[float | int] = None,
    status: str = "ok",
    scope: str = "organization",
    display_caption: Optional[str] = None,
) -> dict[str, Any]:
    delta = None
    if value is not None and previous is not None and previous != 0:
        delta = round((float(value) - float(previous)) / float(previous) * 100.0, 1)
    avail = available and value is not None
    # Semantic zeros: healthy operational outcome vs missing data.
    if avail and value == 0 and id in {
        "failed_jobs",
        "open_alerts",
        "invoices_pending",
        "open_opportunities",
    }:
        status = "healthy_zero"
        if id == "failed_jobs" and not display_caption:
            display_caption = "Sin fallos"
        if id == "open_alerts" and not display_caption:
            display_caption = "Sin alertas"
        if id == "invoices_pending" and not display_caption:
            display_caption = "Sin facturas pendientes"
        if id == "open_opportunities" and not display_caption:
            display_caption = "Sin oportunidades abiertas"
    return {
        "id": id,
        "label": label,
        "value": value,
        "unit": unit,
        "period": period,
        "previous_value": previous,
        "variation_pct": delta,
        "explanation": explanation,
        "detail_path": detail_path,
        "available": avail,
        "status": status if avail else "unavailable",
        "scope": scope,
        "display_caption": display_caption,
    }


def build_workpanel(
    conn: duckdb.DuckDBPyConnection,
    *,
    period: Optional[str] = None,
    organization_id: Optional[int] = None,
    role: str = "user",
) -> dict[str, Any]:
    start, end, label, period_meta = resolve_workpanel_period(
        conn, period=period, organization_id=organization_id, role=role
    )

    p_start, p_end = _prev_period(start)
    org_clause = ""
    org_params: list[Any] = []
    if organization_id is not None:
        org_clause = " AND organization_id = ?"
        org_params = [organization_id]

    # --- metrics ---
    income = None
    income_prev = None
    if table_exists(conn, "app_payment"):
        income = _float(
            conn,
            f"""
            SELECT COALESCE(SUM(amount), 0) FROM app_payment
            WHERE status IN ('recorded', 'reconciled', 'partially_refunded')
              AND COALESCE(settled_at, created_at) >= ?
              AND COALESCE(settled_at, created_at) < ?
              {org_clause}
            """,
            [start, end, *org_params],
        )
        income_prev = _float(
            conn,
            f"""
            SELECT COALESCE(SUM(amount), 0) FROM app_payment
            WHERE status IN ('recorded', 'reconciled', 'partially_refunded')
              AND COALESCE(settled_at, created_at) >= ?
              AND COALESCE(settled_at, created_at) < ?
              {org_clause}
            """,
            [p_start, p_end, *org_params],
        )

    subs = None
    if table_exists(conn, "personal_subscription"):
        # Align with simple report b2c-subscriptions-active (personal/B2C plans).
        subs = _count(
            conn,
            "SELECT COUNT(*) FROM personal_subscription WHERE status = 'active'",
        )
    elif table_exists(conn, "app_subscription"):
        subs = _count(
            conn,
            f"SELECT COUNT(*) FROM app_subscription WHERE status = 'active'{org_clause}",
            org_params or None,
        )

    streams = None
    streams_prev = None
    streams_synthetic = False
    if table_exists(conn, "agg_daily_streams"):
        streams = _count(
            conn,
            """
            SELECT COALESCE(SUM(total_streams), 0) FROM agg_daily_streams
            WHERE fecha >= ? AND fecha < ?
            """,
            [start, end],
        )
        streams_prev = _count(
            conn,
            """
            SELECT COALESCE(SUM(total_streams), 0) FROM agg_daily_streams
            WHERE fecha >= ? AND fecha < ?
            """,
            [p_start, p_end],
        )
        streams_synthetic = True  # warehouse demo activity
    elif table_exists(conn, "fact_streaming"):
        streams = _count(
            conn,
            """
            SELECT COALESCE(SUM(streams), COUNT(*)) FROM fact_streaming
            WHERE fecha_evento >= ? AND fecha_evento < ?
            """,
            [start, end],
        )
        streams_synthetic = True

    catalog = None
    if table_exists(conn, "dim_track"):
        catalog = _count(conn, "SELECT COUNT(*) FROM dim_track")

    cached_sources = None
    if table_exists(conn, "dim_track") and table_exists(conn, "app_track_audio_source"):
        cached_sources = _count(
            conn,
            """
            SELECT COUNT(*) FROM app_track_audio_source
            WHERE provider IS NOT NULL AND TRIM(CAST(provider AS VARCHAR)) <> ''
            """,
        )
    elif table_exists(conn, "dim_track"):
        cached_sources = 0

    invoices_pending = None
    if table_exists(conn, "app_invoice"):
        invoices_pending = _count(
            conn,
            f"""
            SELECT COUNT(*) FROM app_invoice
            WHERE status IN ('issued', 'partially_paid', 'past_due')
            {org_clause}
            """,
            org_params or None,
        )

    open_opps = None
    opp_table = "app_crm_opportunity" if table_exists(conn, "app_crm_opportunity") else (
        "app_opportunity" if table_exists(conn, "app_opportunity") else None
    )
    if opp_table:
        open_opps = _count(
            conn,
            f"""
            SELECT COUNT(*) FROM {opp_table}
            WHERE LOWER(CAST(stage AS VARCHAR)) NOT IN ('won', 'lost', 'closed', 'closed_won', 'closed_lost')
            {org_clause}
            """,
            org_params or None,
        )

    alerts = None
    if table_exists(conn, "app_business_alert"):
        alerts = _count(
            conn,
            f"""
            SELECT COUNT(*) FROM app_business_alert
            WHERE LOWER(CAST(status AS VARCHAR)) IN ('open', 'active', 'new')
            {org_clause}
            """,
            org_params or None,
        )

    failed_jobs = None
    if table_exists(conn, "app_job_execution"):
        failed_jobs = _count(
            conn,
            """
            SELECT COUNT(*) FROM app_job_execution
            WHERE status IN ('failed', 'dead_letter')
            """,
        )

    analytics_updated = None
    if table_exists(conn, "agg_daily_streams"):
        row = _safe(conn, "SELECT MAX(fecha) FROM agg_daily_streams")
        if row and row[0] is not None:
            analytics_updated = str(row[0])
    if table_exists(conn, "ctl_carga_dataset"):
        row = _safe(conn, "SELECT MAX(fecha_carga) FROM ctl_carga_dataset")
        if row and row[0] is not None:
            analytics_updated = str(row[0])

    metrics = [
        _metric(
            id="income_collected",
            label="Ingresos cobrados",
            value=income,
            unit="moneda",
            period=label,
            previous=income_prev,
            explanation="Pagos confirmados durante el periodo.",
            detail_path="/complex-reports?report=income-by-month",
            available=income is not None,
            scope="organization",
            display_caption="Organización activa" if income is not None else None,
        ),
        _metric(
            id="active_subscriptions",
            label="Suscripciones personales — plataforma",
            value=subs,
            unit="suscripciones",
            period="actual",
            explanation="Suscripciones personales vigentes en la plataforma.",
            detail_path="/simple-reports?report=b2c-subscriptions-active",
            available=subs is not None,
            scope="platform",
            display_caption="Suscripciones personales de la plataforma",
        ),
        _metric(
            id="streams_period",
            label="Reproducciones del periodo",
            value=streams,
            unit="reproducciones",
            period=label,
            previous=streams_prev,
            explanation="Actividad musical del catálogo global analítico en el periodo.",
            detail_path="/complex-reports?report=streams-by-day",
            available=streams is not None,
            scope="global_analytics",
            display_caption="Catálogo global analítico" if streams is not None else None,
        ),
        _metric(
            id="catalog_tracks",
            label="Canciones en catálogo",
            value=catalog,
            unit="canciones",
            period="actual",
            explanation="Volumen del catálogo global analítico (no exclusivo de la organización).",
            detail_path="/discover",
            available=catalog is not None,
            scope="global_analytics",
            display_caption="Catálogo global analítico" if catalog is not None else None,
        ),
        _metric(
            id="playback_availability",
            label="Disponibilidad de reproducción",
            value=cached_sources if cached_sources is not None else 0,
            unit="fuentes",
            period="actual",
            explanation=(
                "Fuentes verificadas en caché. La resolución bajo demanda está activa: "
                "las fuentes se buscan automáticamente al reproducir. "
                f"Catálogo musical: {catalog if catalog is not None else '—'}."
            ),
            detail_path="/platform-ops/audio-unresolved",
            available=catalog is not None,
            scope="global_analytics",
            display_caption=(
                f"Resolución bajo demanda activa · catálogo {int(catalog):,}"
                if catalog is not None
                else "Resolución bajo demanda activa"
            ),
        ),
        _metric(
            id="invoices_pending",
            label="Facturas pendientes o vencidas",
            value=invoices_pending,
            unit="facturas",
            period="actual",
            explanation="Facturas de la organización que aún requieren cobro.",
            detail_path="/simple-reports?report=invoices-pending-overdue",
            available=invoices_pending is not None,
            scope="organization",
        ),
        _metric(
            id="open_opportunities",
            label="Oportunidades comerciales abiertas",
            value=open_opps,
            unit="oportunidades",
            period="actual",
            explanation="Negocios en curso de la organización activa.",
            detail_path="/simple-reports?report=crm-opportunities-open",
            available=open_opps is not None,
            scope="organization",
        ),
    ]

    # Restrict sensitive ops metrics for plain users
    if role in {"admin", "engineer"}:
        metrics.extend(
            [
                _metric(
                    id="open_alerts",
                    label="Alertas de negocio abiertas",
                    value=alerts if alerts is not None else 0,
                    unit="alertas",
                    period="actual",
                    explanation="Situaciones que requieren revisión.",
                    detail_path="/simple-reports?report=business-alerts-open",
                    available=True,
                    scope="organization",
                ),
                _metric(
                    id="failed_jobs",
                    label="Trabajos o cargas fallidas",
                    value=failed_jobs if failed_jobs is not None else 0,
                    unit="ejecuciones",
                    period="actual",
                    explanation="Sin fallos durante el periodo."
                    if (failed_jobs or 0) == 0
                    else "Ejecuciones de trabajos con estado fallido.",
                    detail_path="/simple-reports?report=job-executions-failed",
                    available=True,
                    scope="platform",
                ),
            ]
        )

    metrics = _filter_metrics_for_role(metrics, role)

    pendings: list[dict[str, Any]] = []
    for m in metrics:
        if m["id"] in {
            "invoices_pending",
            "open_alerts",
            "failed_jobs",
            "open_opportunities",
        } and m.get("value") and float(m["value"]) > 0:
            pendings.append(
                {
                    "id": m["id"],
                    "label": m["label"],
                    "value": m["value"],
                    "detail_path": m["detail_path"],
                    "severity": "high" if m["id"] in {"failed_jobs", "open_alerts"} else "medium",
                }
            )

    return {
        "title": "Workpanel",
        "subtitle": "Resumen táctico del negocio y la plataforma.",
        "period": label,
        "period_start": start.isoformat(),
        "period_end_exclusive": end.isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "analytics_updated_at": analytics_updated,
        "organization_id": organization_id,
        "includes_synthetic_events": streams_synthetic,
        "available_periods": period_meta.get("available_periods") or [],
        "default_period": period_meta.get("default_period"),
        "period_sources": period_meta.get("period_sources") or {},
        "sections": _sections_for_role(role),
        "metrics": metrics,
        "pendings": pendings,
        "links": [
            {"label": "Reportes simples", "path": "/simple-reports"},
            {"label": "Informes complejos", "path": "/complex-reports"},
        ],
    }
