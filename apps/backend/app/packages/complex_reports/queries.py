# -*- coding: utf-8 -*-
"""Complex report query runners — aggregates prepared in backend."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

import duckdb

from app.core.database import table_exists
from app.packages.complex_reports.registry import get_report


def _parse_bounds(date_from: Optional[str], date_to: Optional[str]) -> tuple[date, date]:
    today = date.today()
    end = today + timedelta(days=1)
    start = today - timedelta(days=30)
    if date_from:
        try:
            start = date.fromisoformat(date_from[:10])
        except Exception:
            pass
    if date_to:
        try:
            end = date.fromisoformat(date_to[:10]) + timedelta(days=1)
        except Exception:
            pass
    if start >= end:
        end = start + timedelta(days=1)
    # Prefer warehouse stream range when no explicit from/to and default empty
    return start, end


def _prefer_fact_stream_bounds(
    conn: duckdb.DuckDBPyConnection, start: date, end: date, explicit: bool
) -> tuple[date, date]:
    """Leaderboards must follow fact_streaming dates, not gold daily watermark."""
    if explicit or not table_exists(conn, "fact_streaming"):
        return start, end
    try:
        row = conn.execute(
            "SELECT MIN(fecha_evento)::DATE, MAX(fecha_evento)::DATE FROM fact_streaming"
        ).fetchone()
    except Exception:
        return start, end
    if not row or not row[1]:
        return start, end
    max_d = row[1]
    if not hasattr(max_d, "year"):
        return start, end
    end = max_d + timedelta(days=1)
    start = max_d - timedelta(days=29)
    return start, end


def _prefer_stream_bounds(conn: duckdb.DuckDBPyConnection, start: date, end: date, explicit: bool) -> tuple[date, date]:
    if explicit or not table_exists(conn, "agg_daily_streams"):
        return start, end
    row = conn.execute("SELECT MIN(fecha), MAX(fecha) FROM agg_daily_streams").fetchone()
    if not row or not row[1]:
        return start, end
    max_d = row[1]
    # last 30 days of available data
    end = max_d + timedelta(days=1) if hasattr(max_d, "year") else end
    start = (max_d - timedelta(days=29)) if hasattr(max_d, "year") else start
    return start, end


def _prefer_monthly_bounds(
    conn: duckdb.DuckDBPyConnection,
    start: date,
    end: date,
    explicit: bool,
    table: str,
    date_expr: str,
) -> tuple[date, date]:
    """When dates are implicit, use last ~12 months of available table data."""
    if explicit or not table_exists(conn, table):
        return start, end
    try:
        row = conn.execute(f"SELECT MIN({date_expr})::DATE, MAX({date_expr})::DATE FROM {table}").fetchone()
    except Exception:
        return start, end
    if not row or not row[1]:
        return start, end
    max_d = row[1]
    if not hasattr(max_d, "year"):
        return start, end
    end = max_d + timedelta(days=1)
    start = date(max_d.year, max_d.month, 1)
    # Walk back 11 months
    y, m = start.year, start.month
    for _ in range(11):
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    start = date(y, m, 1)
    return start, end


def _series_summary(points: list[dict[str, Any]], value_key: str = "value") -> dict[str, Any]:
    vals = [float(p[value_key]) for p in points if p.get(value_key) is not None]
    if not vals:
        return {"total": 0.0, "average": None, "max": None, "min": None, "count": 0}
    return {
        "total": round(sum(vals), 4),
        "average": round(sum(vals) / len(vals), 4),
        "max": max(vals),
        "min": min(vals),
        "count": len(vals),
    }


def run_complex_report(
    conn: duckdb.DuckDBPyConnection,
    report_id: str,
    *,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    organization_id: Optional[int] = None,
    limit: int = 20,
) -> dict[str, Any]:
    report = get_report(report_id)
    if report is None:
        raise KeyError(report_id)

    explicit = bool(date_from or date_to)
    start, end = _parse_bounds(date_from, date_to)
    if report_id in {"top-tracks-period", "top-artists-period"}:
        start, end = _prefer_fact_stream_bounds(conn, start, end, explicit)
    elif report_id.startswith("top-") or report_id == "streams-by-day":
        start, end = _prefer_stream_bounds(conn, start, end, explicit)

    base = {
        "report_id": report_id,
        "title": report.title,
        "question": report.question,
        "calculation": report.calculation,
        "chart_type": report.chart_type,
        "available": report.available,
        "unavailable_reason": report.unavailable_reason,
        "period_start": start.isoformat(),
        "period_end_exclusive": end.isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "includes_synthetic_events": False,
        "summary": {},
        "series": [],
        "rows": [],
        "columns": [],
    }

    if not report.available:
        return base

    limit = max(1, min(int(limit or 20), 100))
    org_sql = ""
    org_params: list[Any] = []
    if organization_id is not None:
        org_sql = " AND organization_id = ?"
        org_params = [organization_id]

    if report_id == "income-by-month":
        if not table_exists(conn, "app_payment"):
            return {**base, "available": False, "unavailable_reason": "No existe la tabla de pagos."}
        start, end = _prefer_monthly_bounds(
            conn, start, end, explicit, "app_payment", "COALESCE(settled_at, created_at)"
        )
        base["period_start"] = start.isoformat()
        base["period_end_exclusive"] = end.isoformat()
        rows = conn.execute(
            f"""
            SELECT strftime(COALESCE(settled_at, created_at), '%Y-%m') AS periodo,
                   SUM(amount) AS total
            FROM app_payment
            WHERE status IN ('recorded', 'reconciled', 'partially_refunded')
              AND COALESCE(settled_at, created_at) >= ?
              AND COALESCE(settled_at, created_at) < ?
              {org_sql}
            GROUP BY 1
            ORDER BY 1
            """,
            [start, end, *org_params],
        ).fetchall()
        series = [{"label": r[0], "value": float(r[1] or 0)} for r in rows]
        detail = [{"periodo": r[0], "ingresos": float(r[1] or 0)} for r in rows]
        return {
            **base,
            "summary": _series_summary(series),
            "series": series,
            "rows": detail,
            "columns": [
                {"key": "periodo", "label": "Periodo"},
                {"key": "ingresos", "label": "Ingresos"},
            ],
        }

    if report_id == "streams-by-day":
        base["includes_synthetic_events"] = True
        if table_exists(conn, "agg_daily_streams"):
            rows = conn.execute(
                """
                SELECT CAST(fecha AS VARCHAR), COALESCE(total_streams, 0)
                FROM agg_daily_streams
                WHERE fecha >= ? AND fecha < ?
                ORDER BY fecha
                """,
                [start, end],
            ).fetchall()
        elif table_exists(conn, "fact_streaming"):
            rows = conn.execute(
                """
                SELECT CAST(CAST(fecha_evento AS DATE) AS VARCHAR), COUNT(*)
                FROM fact_streaming
                WHERE fecha_evento >= ? AND fecha_evento < ?
                GROUP BY 1 ORDER BY 1
                """,
                [start, end],
            ).fetchall()
        else:
            return {**base, "available": False, "unavailable_reason": "No hay tablas de reproducciones."}
        series = [{"label": r[0], "value": int(r[1] or 0)} for r in rows]
        detail = [{"fecha": r[0], "reproducciones": int(r[1] or 0)} for r in rows]
        return {
            **base,
            "summary": _series_summary(series),
            "series": series,
            "rows": detail,
            "columns": [
                {"key": "fecha", "label": "Fecha"},
                {"key": "reproducciones", "label": "Reproducciones"},
            ],
        }

    if report_id == "top-tracks-period":
        base["includes_synthetic_events"] = True
        if not table_exists(conn, "fact_streaming"):
            return {**base, "available": False, "unavailable_reason": "No existe fact_streaming."}
        name_expr = "COALESCE(t.nombre_track, CAST(fs.id_track AS VARCHAR))"
        has_track = table_exists(conn, "dim_track")
        artist_expr = "CAST(NULL AS VARCHAR)"
        join = ""
        if has_track:
            join = "LEFT JOIN dim_track t ON t.id_track = fs.id_track"
            cols = {r[0] for r in conn.execute("DESCRIBE dim_track").fetchall()}
            if "artista" in cols:
                artist_expr = "COALESCE(t.artista, '—')"
            elif "nombre_artista" in cols:
                artist_expr = "COALESCE(t.nombre_artista, '—')"
            elif "id_artista" in cols and table_exists(conn, "dim_artista"):
                join += " LEFT JOIN dim_artista a ON a.id_artista = t.id_artista"
                artist_expr = "COALESCE(a.nombre_artista, '—')"
            else:
                artist_expr = "'—'"
        rows = conn.execute(
            f"""
            SELECT fs.id_track, {name_expr}, {artist_expr}, COALESCE(SUM(fs.streams), COUNT(*)) AS total
            FROM fact_streaming fs
            {join}
            WHERE fs.fecha_evento >= ? AND fs.fecha_evento < ?
            GROUP BY 1, 2, 3
            ORDER BY total DESC
            LIMIT ?
            """,
            [start, end, limit],
        ).fetchall()
        series = [{"label": str(r[1]), "value": int(r[3])} for r in rows]
        detail = [
            {
                "track_id": int(r[0]) if r[0] is not None else None,
                "cancion": r[1],
                "artista": r[2] or "—",
                "reproducciones": int(r[3]),
            }
            for r in rows
        ]
        return {
            **base,
            "summary": _series_summary(series),
            "series": series,
            "rows": detail,
            "columns": [
                {"key": "cancion", "label": "Canción"},
                {"key": "artista", "label": "Artista"},
                {"key": "reproducciones", "label": "Reproducciones"},
            ],
        }

    if report_id == "top-artists-period":
        base["includes_synthetic_events"] = True
        if not table_exists(conn, "fact_streaming") or not table_exists(conn, "dim_track"):
            return {**base, "available": False, "unavailable_reason": "Faltan fact_streaming o dim_track."}
        # dim_track may expose id_artista / artista
        cols = {r[0] for r in conn.execute("DESCRIBE dim_track").fetchall()}
        if "id_artista" in cols and table_exists(conn, "dim_artista"):
            rows = conn.execute(
                """
                SELECT COALESCE(a.nombre_artista, CAST(t.id_artista AS VARCHAR)),
                       COALESCE(SUM(fs.streams), COUNT(*)) AS total
                FROM fact_streaming fs
                JOIN dim_track t ON t.id_track = fs.id_track
                LEFT JOIN dim_artista a ON a.id_artista = t.id_artista
                WHERE fs.fecha_evento >= ? AND fs.fecha_evento < ?
                GROUP BY 1
                ORDER BY total DESC
                LIMIT ?
                """,
                [start, end, limit],
            ).fetchall()
        elif table_exists(conn, "agg_top_artistas"):
            rows = conn.execute(
                """
                SELECT nombre_artista, total_streams
                FROM agg_top_artistas
                ORDER BY total_streams DESC NULLS LAST
                LIMIT ?
                """,
                [limit],
            ).fetchall()
        else:
            return {**base, "available": False, "unavailable_reason": "No se pudo relacionar canciones con artistas."}
        series = [{"label": str(r[0]), "value": int(r[1] or 0)} for r in rows]
        detail = [{"artista": r[0], "reproducciones": int(r[1] or 0)} for r in rows]
        return {
            **base,
            "summary": _series_summary(series),
            "series": series,
            "rows": detail,
            "columns": [
                {"key": "artista", "label": "Artista"},
                {"key": "reproducciones", "label": "Reproducciones"},
            ],
        }

    if report_id == "top-genres-period":
        base["includes_synthetic_events"] = True
        if table_exists(conn, "agg_genre_trends"):
            rows = conn.execute(
                """
                SELECT nombre_genero, COALESCE(streams_7d, 0)
                FROM agg_genre_trends
                ORDER BY streams_7d DESC NULLS LAST
                LIMIT ?
                """,
                [limit],
            ).fetchall()
        elif table_exists(conn, "fact_streaming") and table_exists(conn, "dim_track"):
            cols = {r[0] for r in conn.execute("DESCRIBE dim_track").fetchall()}
            if "id_genero" not in cols:
                return {**base, "available": False, "unavailable_reason": "dim_track no tiene género."}
            rows = conn.execute(
                """
                SELECT COALESCE(g.nombre_genero, CAST(t.id_genero AS VARCHAR)),
                       COALESCE(SUM(fs.streams), COUNT(*))
                FROM fact_streaming fs
                JOIN dim_track t ON t.id_track = fs.id_track
                LEFT JOIN dim_genero g ON g.id_genero = t.id_genero
                WHERE fs.fecha_evento >= ? AND fs.fecha_evento < ?
                GROUP BY 1
                ORDER BY 2 DESC
                LIMIT ?
                """,
                [start, end, limit],
            ).fetchall()
        else:
            return {**base, "available": False, "unavailable_reason": "No hay datos de géneros."}
        series = [{"label": str(r[0]), "value": int(r[1] or 0)} for r in rows]
        detail = [{"genero": r[0], "reproducciones": int(r[1] or 0)} for r in rows]
        return {
            **base,
            "summary": _series_summary(series),
            "series": series,
            "rows": detail,
            "columns": [
                {"key": "genero", "label": "Género"},
                {"key": "reproducciones", "label": "Reproducciones"},
            ],
        }

    if report_id == "opportunity-win-rate-month":
        table = "app_crm_opportunity" if table_exists(conn, "app_crm_opportunity") else None
        if not table:
            return {**base, "available": False, "unavailable_reason": "No existe la tabla de oportunidades."}
        cols = {r[0] for r in conn.execute(f"DESCRIBE {table}").fetchall()}
        date_col = "updated_at" if "updated_at" in cols else ("closed_at" if "closed_at" in cols else "created_at")
        stage_col = "stage" if "stage" in cols else "status"
        start, end = _prefer_monthly_bounds(conn, start, end, explicit, table, date_col)
        base["period_start"] = start.isoformat()
        base["period_end_exclusive"] = end.isoformat()
        rows = conn.execute(
            f"""
            SELECT strftime({date_col}, '%Y-%m') AS periodo,
                   SUM(CASE WHEN LOWER(CAST({stage_col} AS VARCHAR)) IN ('won','closed_won') THEN 1 ELSE 0 END) AS ganadas,
                   SUM(CASE WHEN LOWER(CAST({stage_col} AS VARCHAR)) IN ('won','lost','closed','closed_won','closed_lost') THEN 1 ELSE 0 END) AS cerradas
            FROM {table}
            WHERE {date_col} >= ? AND {date_col} < ?
            {org_sql}
            GROUP BY 1
            ORDER BY 1
            """,
            [start, end, *org_params],
        ).fetchall()
        series = []
        detail = []
        for r in rows:
            closed = int(r[2] or 0)
            won = int(r[1] or 0)
            pct = round(won * 100.0 / closed, 2) if closed else None
            series.append({"label": r[0], "value": pct if pct is not None else 0})
            detail.append({"periodo": r[0], "ganadas": won, "cerradas": closed, "porcentaje": pct})
        return {
            **base,
            "summary": _series_summary([s for s in series if s["value"] is not None]),
            "series": series,
            "rows": detail,
            "columns": [
                {"key": "periodo", "label": "Periodo"},
                {"key": "ganadas", "label": "Ganadas"},
                {"key": "cerradas", "label": "Cerradas"},
                {"key": "porcentaje", "label": "Porcentaje"},
            ],
        }

    if report_id == "subscription-growth-month":
        if not table_exists(conn, "app_subscription"):
            return {**base, "available": False, "unavailable_reason": "No existe la tabla de suscripciones."}
        cols = {r[0] for r in conn.execute("DESCRIBE app_subscription").fetchall()}
        date_col = "created_at" if "created_at" in cols else "current_period_start"
        start, end = _prefer_monthly_bounds(conn, start, end, explicit, "app_subscription", date_col)
        base["period_start"] = start.isoformat()
        base["period_end_exclusive"] = end.isoformat()
        rows = conn.execute(
            f"""
            SELECT strftime({date_col}, '%Y-%m') AS periodo, COUNT(*) AS altas
            FROM app_subscription
            WHERE {date_col} >= ? AND {date_col} < ?
            {org_sql}
            GROUP BY 1
            ORDER BY 1
            """,
            [start, end, *org_params],
        ).fetchall()
        series = [{"label": r[0], "value": int(r[1] or 0)} for r in rows]
        detail = [{"periodo": r[0], "altas": int(r[1] or 0)} for r in rows]
        return {
            **base,
            "summary": _series_summary(series),
            "series": series,
            "rows": detail,
            "columns": [
                {"key": "periodo", "label": "Periodo"},
                {"key": "altas", "label": "Altas"},
            ],
        }

    if report_id == "releases-status-month":
        table = None
        for candidate in ("app_catalog_submission", "app_release_submission", "app_publishing_submission"):
            if table_exists(conn, candidate):
                table = candidate
                break
        if not table:
            return {
                **base,
                "available": False,
                "unavailable_reason": "No hay tabla operacional de envíos de lanzamiento disponible.",
            }
        cols = {r[0] for r in conn.execute(f"DESCRIBE {table}").fetchall()}
        date_col = "created_at" if "created_at" in cols else list(cols)[0]
        status_col = "status" if "status" in cols else None
        if not status_col:
            return {**base, "available": False, "unavailable_reason": "La tabla de lanzamientos no tiene estado."}
        start, end = _prefer_monthly_bounds(conn, start, end, explicit, table, date_col)
        base["period_start"] = start.isoformat()
        base["period_end_exclusive"] = end.isoformat()
        rows = conn.execute(
            f"""
            SELECT strftime({date_col}, '%Y-%m') AS periodo,
                   CAST({status_col} AS VARCHAR) AS estado,
                   COUNT(*) AS total
            FROM {table}
            WHERE {date_col} >= ? AND {date_col} < ?
            GROUP BY 1, 2
            ORDER BY 1, 2
            """,
            [start, end],
        ).fetchall()
        detail = [{"periodo": r[0], "estado": r[1], "cantidad": int(r[2])} for r in rows]
        series = [{"label": f"{r[0]} · {r[1]}", "value": int(r[2])} for r in rows]
        return {
            **base,
            "summary": _series_summary(series),
            "series": series,
            "rows": detail,
            "columns": [
                {"key": "periodo", "label": "Periodo"},
                {"key": "estado", "label": "Estado"},
                {"key": "cantidad", "label": "Cantidad"},
            ],
        }

    return {**base, "available": False, "unavailable_reason": "Informe no implementado."}
