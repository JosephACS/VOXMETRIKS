# -*- coding: utf-8 -*-
"""Query runners for simple reports (parametrized DuckDB SQL)."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import duckdb

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def table_exists(conn: duckdb.DuckDBPyConnection, name: str) -> bool:
    try:
        row = conn.execute(
            "SELECT 1 FROM information_schema.tables WHERE table_name = ? LIMIT 1",
            [name],
        ).fetchone()
        return row is not None
    except Exception:
        try:
            conn.execute(f"SELECT 1 FROM {name} LIMIT 0")
            return True
        except Exception:
            return False


def _rows_to_dicts(conn: duckdb.DuckDBPyConnection, sql: str, params: list[Any]) -> list[dict[str, Any]]:
    cur = conn.execute(sql, params)
    cols = [d[0] for d in cur.description]
    out = []
    for row in cur.fetchall():
        item = {}
        for i, c in enumerate(cols):
            v = row[i]
            if isinstance(v, datetime):
                v = v.isoformat(sep=" ", timespec="seconds")
            item[c] = v
        out.append(item)
    return out


def _safe_query(
    conn: duckdb.DuckDBPyConnection,
    sql: str,
    params: list[Any],
    *,
    required_tables: tuple[str, ...] = (),
) -> list[dict[str, Any]]:
    for t in required_tables:
        if not table_exists(conn, t):
            return []
    try:
        return _rows_to_dicts(conn, sql, params)
    except Exception:
        logger.exception("simple report query failed")
        return []


def run_report(
    conn: duckdb.DuckDBPyConnection,
    report_id: str,
    *,
    organization_id: Optional[int] = None,
    filters: Optional[dict[str, Any]] = None,
    search: Optional[str] = None,
    limit: int = 25,
    offset: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    filters = filters or {}
    runner = RUNNERS.get(report_id)
    if runner is None:
        return [], 0
    items = runner(conn, organization_id=organization_id, filters=filters, search=search)
    total = len(items)
    return items[offset : offset + limit], total


# ---------------------------------------------------------------------------
# Individual runners
# ---------------------------------------------------------------------------

def _business_alerts_open(conn, *, organization_id=None, filters=None, search=None):
    filters = filters or {}
    where = ["status IN ('open')"]
    params: list[Any] = []
    if organization_id is not None:
        where.append("organization_id = ?")
        params.append(organization_id)
    sev = filters.get("severity")
    if sev:
        where.append("severity = ?")
        params.append(sev)
    if search:
        where.append("(title ILIKE ? OR CAST(id AS VARCHAR) ILIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    sql = f"""
        SELECT id, severity, title, status, created_at
        FROM app_business_alert
        WHERE {' AND '.join(where)}
        ORDER BY CASE severity WHEN 'critical' THEN 1 WHEN 'warning' THEN 2 ELSE 3 END, created_at DESC
    """
    return _safe_query(conn, sql, params, required_tables=("app_business_alert",))


def _kpi_last_update(conn, *, organization_id=None, filters=None, search=None):
    params: list[Any] = []
    org_join = ""
    if organization_id is not None:
        org_join = "AND s.organization_id = ?"
        params.append(organization_id)
    search_clause = ""
    if search:
        search_clause = "AND (d.code ILIKE ? OR d.name ILIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    sql = f"""
        SELECT d.code AS kpi_code,
               COALESCE(d.name, d.code) AS kpi_name,
               MAX(s.created_at) AS last_updated_at,
               MAX(s.period) AS period,
               MAX(s.quality_status) AS quality_status
        FROM app_kpi_definition d
        LEFT JOIN app_kpi_snapshot s ON s.kpi_definition_id = d.id {org_join}
        WHERE 1=1 {search_clause}
        GROUP BY d.code, d.name
        ORDER BY last_updated_at DESC NULLS LAST
    """
    return _safe_query(conn, sql, params, required_tables=("app_kpi_definition", "app_kpi_snapshot"))


def _crm_opportunities_open(conn, *, organization_id=None, filters=None, search=None):
    filters = filters or {}
    where = [
        "deleted_at IS NULL",
        "stage NOT IN ('closed_won', 'closed_lost', 'canceled')",
    ]
    params: list[Any] = []
    if organization_id is not None:
        where.append("organization_id = ?")
        params.append(organization_id)
    if filters.get("stage"):
        where.append("stage = ?")
        params.append(filters["stage"])
    sql = f"""
        SELECT id, stage, owner_user_id, expected_close_date, updated_at
        FROM app_crm_opportunity
        WHERE {' AND '.join(where)}
        ORDER BY updated_at DESC
    """
    return _safe_query(conn, sql, params, required_tables=("app_crm_opportunity",))


def _crm_quotations_pending(conn, *, organization_id=None, filters=None, search=None):
    """Organization-scoped via opportunity (quotation) or contract org."""
    if organization_id is None:
        return []
    if table_exists(conn, "app_crm_approval_request") and table_exists(conn, "app_crm_opportunity"):
        # quotation_version → quotation → opportunity.organization_id
        # contract → organization_id when present
        has_qv = table_exists(conn, "app_crm_quotation_version") and table_exists(
            conn, "app_crm_quotation"
        )
        has_contract = table_exists(conn, "app_crm_contract") and _has_column(
            conn, "app_crm_contract", "organization_id"
        )
        unions: list[str] = []
        params: list[Any] = []
        if has_qv:
            unions.append(
                """
                SELECT a.id, a.object_type, a.object_id, a.status, a.requested_at
                FROM app_crm_approval_request a
                JOIN app_crm_quotation_version v ON a.object_type = 'quotation_version'
                    AND v.id = a.object_id
                JOIN app_crm_quotation q ON q.id = v.quotation_id
                JOIN app_crm_opportunity o ON o.id = q.opportunity_id
                WHERE a.status = 'pending' AND o.organization_id = ?
                """
            )
            params.append(organization_id)
        if has_contract:
            unions.append(
                """
                SELECT a.id, a.object_type, a.object_id, a.status, a.requested_at
                FROM app_crm_approval_request a
                JOIN app_crm_contract c ON a.object_type = 'contract' AND c.id = a.object_id
                WHERE a.status = 'pending' AND c.organization_id = ?
                """
            )
            params.append(organization_id)
        if not unions:
            return []
        sql = " UNION ALL ".join(unions) + " ORDER BY requested_at DESC"
        return _safe_query(
            conn,
            sql,
            params,
            required_tables=("app_crm_approval_request",),
        )
    if table_exists(conn, "app_crm_quotation_version") and table_exists(
        conn, "app_crm_quotation"
    ) and table_exists(conn, "app_crm_opportunity"):
        return _safe_query(
            conn,
            """
            SELECT v.id, 'quotation_version' AS object_type, v.quotation_id AS object_id,
                   v.status, v.updated_at AS requested_at
            FROM app_crm_quotation_version v
            JOIN app_crm_quotation q ON q.id = v.quotation_id
            JOIN app_crm_opportunity o ON o.id = q.opportunity_id
            WHERE v.status = 'pending_approval' AND o.organization_id = ?
            ORDER BY v.updated_at DESC
            """,
            [organization_id],
            required_tables=("app_crm_quotation_version",),
        )
    return []


def _campaigns_active(conn, *, organization_id=None, filters=None, search=None):
    where = ["status = 'active'"]
    params: list[Any] = []
    if organization_id is not None:
        where.append("organization_id = ?")
        params.append(organization_id)
    if search:
        where.append("name ILIKE ?")
        params.append(f"%{search}%")
    sql = f"""
        SELECT id, name, status, start_date, end_date
        FROM app_campaign
        WHERE {' AND '.join(where)}
        ORDER BY start_date DESC NULLS LAST
    """
    return _safe_query(conn, sql, params, required_tables=("app_campaign",))


def _releases_pending(conn, *, organization_id=None, filters=None, search=None):
    filters = filters or {}
    where = ["status IN ('submitted', 'under_review', 'changes_requested')"]
    params: list[Any] = []
    if organization_id is not None:
        where.append("organization_id = ?")
        params.append(organization_id)
    if filters.get("status"):
        where = ["status = ?"]
        params = [filters["status"]]
        if organization_id is not None:
            where.append("organization_id = ?")
            params.append(organization_id)
    sql = f"""
        SELECT id, status, reviewer_id, updated_at
        FROM app_release_submission
        WHERE {' AND '.join(where)}
        ORDER BY updated_at DESC
    """
    return _safe_query(conn, sql, params, required_tables=("app_release_submission",))


def _release_issues_open(conn, *, organization_id=None, filters=None, search=None):
    if organization_id is None:
        return []
    if not table_exists(conn, "app_release_review_issue"):
        return []
    if table_exists(conn, "app_release_submission"):
        return _safe_query(
            conn,
            """
            SELECT i.id, i.submission_id, i.severity, i.message, i.resolved
            FROM app_release_review_issue i
            JOIN app_release_submission s ON s.id = i.submission_id
            WHERE COALESCE(i.resolved, FALSE) = FALSE
              AND s.organization_id = ?
            ORDER BY i.id DESC
            """,
            [organization_id],
            required_tables=("app_release_review_issue", "app_release_submission"),
        )
    return []


def _tracks_without_cover(conn, *, organization_id=None, filters=None, search=None):
    if not table_exists(conn, "dim_track"):
        return []
    if table_exists(conn, "app_track_cover"):
        return _safe_query(
            conn,
            """
            SELECT t.id_track AS track_id, t.nombre_track AS track_name,
                   COALESCE(c.status, 'missing') AS cover_status
            FROM dim_track t
            LEFT JOIN app_track_cover c ON c.track_id = t.id_track
            WHERE c.track_id IS NULL OR c.status <> 'ok' OR c.image_url IS NULL OR TRIM(c.image_url) = ''
            ORDER BY t.id_track
            LIMIT 2000
            """,
            [],
            required_tables=("dim_track",),
        )
    return _safe_query(
        conn,
        """
        SELECT id_track AS track_id, nombre_track AS track_name, 'unknown' AS cover_status
        FROM dim_track
        ORDER BY id_track
        LIMIT 500
        """,
        [],
        required_tables=("dim_track",),
    )


def _tracks_incomplete_metadata(conn, *, organization_id=None, filters=None, search=None):
    return _safe_query(
        conn,
        """
        SELECT id_track AS track_id, nombre_track AS track_name,
               id_artista, id_album, id_genero
        FROM dim_track
        WHERE id_artista IS NULL OR id_album IS NULL OR id_genero IS NULL
           OR TRIM(COALESCE(nombre_track, '')) = ''
        ORDER BY id_track
        """,
        [],
        required_tables=("dim_track",),
    )


def _rights_contracts_active(conn, *, organization_id=None, filters=None, search=None):
    where = ["status = 'active'"]
    params: list[Any] = []
    if organization_id is not None:
        where.append("organization_id = ?")
        params.append(organization_id)
    sql = f"""
        SELECT id, rights_type, status, valid_from, valid_to
        FROM app_rights_contract
        WHERE {' AND '.join(where)}
        ORDER BY valid_to ASC NULLS LAST
    """
    return _safe_query(conn, sql, params, required_tables=("app_rights_contract",))


def _rights_conflicts_open(conn, *, organization_id=None, filters=None, search=None):
    where = ["status = 'open'"]
    params: list[Any] = []
    if organization_id is not None:
        where.append("organization_id = ?")
        params.append(organization_id)
    sql = f"""
        SELECT id, asset_id, rights_type, status, territory_code
        FROM app_rights_conflict
        WHERE {' AND '.join(where)}
        ORDER BY id DESC
    """
    return _safe_query(conn, sql, params, required_tables=("app_rights_conflict",))


def _rights_contracts_expiring(conn, *, organization_id=None, filters=None, search=None):
    filters = filters or {}
    try:
        days = int(filters.get("within_days") or 90)
    except (TypeError, ValueError):
        days = 90
    days = max(1, min(days, 365))
    cutoff = _now() + timedelta(days=days)
    where = ["status = 'active'", "valid_to IS NOT NULL", "valid_to <= ?"]
    params: list[Any] = [cutoff]
    if organization_id is not None:
        where.append("organization_id = ?")
        params.append(organization_id)
    sql = f"""
        SELECT id, rights_type, status, valid_to,
               CAST(date_diff('day', CURRENT_DATE, CAST(valid_to AS DATE)) AS INTEGER) AS days_remaining
        FROM app_rights_contract
        WHERE {' AND '.join(where)}
        ORDER BY valid_to ASC
    """
    return _safe_query(conn, sql, params, required_tables=("app_rights_contract",))


def _b2c_active(conn, *, organization_id=None, filters=None, search=None):
    return _safe_query(
        conn,
        """
        SELECT id, user_id, plan_id, status, current_period_end
        FROM personal_subscription
        WHERE status = 'active'
        ORDER BY current_period_end ASC NULLS LAST
        """,
        [],
        required_tables=("personal_subscription",),
    )


def _b2c_past_due(conn, *, organization_id=None, filters=None, search=None):
    return _safe_query(
        conn,
        """
        SELECT id, user_id, status, access_state, current_period_end
        FROM personal_subscription
        WHERE status IN ('past_due', 'canceled')
           OR LOWER(COALESCE(access_state, '')) IN ('limited', 'blocked')
        ORDER BY current_period_end ASC NULLS LAST
        """,
        [],
        required_tables=("personal_subscription",),
    )


def _b2b_active(conn, *, organization_id=None, filters=None, search=None):
    where = ["status IN ('trialing', 'active')"]
    params: list[Any] = []
    if organization_id is not None:
        where.append("organization_id = ?")
        params.append(organization_id)
    sql = f"""
        SELECT id, organization_id, plan_id, status, current_period_end
        FROM app_subscription
        WHERE {' AND '.join(where)}
        ORDER BY current_period_end ASC NULLS LAST
    """
    return _safe_query(conn, sql, params, required_tables=("app_subscription",))


def _b2b_past_due(conn, *, organization_id=None, filters=None, search=None):
    where = ["status IN ('past_due', 'canceled')"]
    params: list[Any] = []
    if organization_id is not None:
        where.append("organization_id = ?")
        params.append(organization_id)
    sql = f"""
        SELECT id, organization_id, status, access_state, current_period_end
        FROM app_subscription
        WHERE {' AND '.join(where)}
        ORDER BY current_period_end ASC NULLS LAST
    """
    return _safe_query(conn, sql, params, required_tables=("app_subscription",))


def _invoices_pending(conn, *, organization_id=None, filters=None, search=None):
    filters = filters or {}
    where = ["status IN ('issued', 'partially_paid', 'past_due')"]
    params: list[Any] = []
    if organization_id is not None:
        where.append("organization_id = ?")
        params.append(organization_id)
    if filters.get("status"):
        where = ["status = ?"]
        params = [filters["status"]]
        if organization_id is not None:
            where.append("organization_id = ?")
            params.append(organization_id)
    sql = f"""
        SELECT id, invoice_number, status, total, due_date, organization_id
        FROM app_invoice
        WHERE {' AND '.join(where)}
        ORDER BY due_date ASC NULLS LAST
    """
    return _safe_query(conn, sql, params, required_tables=("app_invoice",))


def _payment_attempts_failed(conn, *, organization_id=None, filters=None, search=None):
    if organization_id is None:
        return []
    if not table_exists(conn, "app_payment_attempt"):
        return []
    if _has_column(conn, "app_payment_attempt", "organization_id"):
        return _safe_query(
            conn,
            """
            SELECT id, invoice_id, status, failure_reason, created_at
            FROM app_payment_attempt
            WHERE status = 'failed' AND organization_id = ?
            ORDER BY created_at DESC
            """,
            [organization_id],
            required_tables=("app_payment_attempt",),
        )
    if table_exists(conn, "app_invoice"):
        return _safe_query(
            conn,
            """
            SELECT a.id, a.invoice_id, a.status, a.failure_reason, a.created_at
            FROM app_payment_attempt a
            JOIN app_invoice i ON i.id = a.invoice_id
            WHERE a.status = 'failed' AND i.organization_id = ?
            ORDER BY a.created_at DESC
            """,
            [organization_id],
            required_tables=("app_payment_attempt", "app_invoice"),
        )
    return []


def _royalty_settlements_open(conn, *, organization_id=None, filters=None, search=None):
    where = ["status NOT IN ('finalized', 'reversed')"]
    params: list[Any] = []
    if organization_id is not None and _has_column(conn, "app_royalty_settlement_run", "organization_id"):
        where.append("organization_id = ?")
        params.append(organization_id)
    # column names may vary; try common set
    cols = _existing_columns(
        conn,
        "app_royalty_settlement_run",
        ["id", "status", "period_start", "period_end", "updated_at", "created_at"],
    )
    if not cols:
        return []
    select_cols = ", ".join(cols)
    # alias created_at as updated_at if needed
    if "updated_at" not in cols and "created_at" in cols:
        select_cols = select_cols.replace("created_at", "created_at AS updated_at")
    if "period_start" not in cols:
        select_cols = select_cols  # leave as-is; FE shows available keys
    sql = f"""
        SELECT {select_cols}
        FROM app_royalty_settlement_run
        WHERE {' AND '.join(where)}
        ORDER BY id DESC
    """
    return _safe_query(conn, sql, params, required_tables=("app_royalty_settlement_run",))


def _payouts_with_error(conn, *, organization_id=None, filters=None, search=None):
    if table_exists(conn, "app_payout_failure"):
        return _safe_query(
            conn,
            """
            SELECT id, instruction_id, failure_code, message, created_at
            FROM app_payout_failure
            ORDER BY created_at DESC
            """,
            [],
            required_tables=("app_payout_failure",),
        )
    return _safe_query(
        conn,
        """
        SELECT id, id AS instruction_id, status AS failure_code,
               COALESCE(error_message, status) AS message, updated_at AS created_at
        FROM app_payout_instruction
        WHERE status = 'failed'
        ORDER BY updated_at DESC
        """,
        [],
        required_tables=("app_payout_instruction",),
    )


def _support_cases_open(conn, *, organization_id=None, filters=None, search=None):
    filters = filters or {}
    where = ["status NOT IN ('resolved', 'closed')"]
    params: list[Any] = []
    if organization_id is not None:
        where.append("organization_id = ?")
        params.append(organization_id)
    if filters.get("priority"):
        where.append("priority = ?")
        params.append(filters["priority"])
    subject_col = "subject" if _has_column(conn, "app_support_case", "subject") else "CAST(id AS VARCHAR)"
    sql = f"""
        SELECT id, priority, status, {subject_col} AS subject, created_at
        FROM app_support_case
        WHERE {' AND '.join(where)}
        ORDER BY created_at DESC
    """
    return _safe_query(conn, sql, params, required_tables=("app_support_case",))


def _cs_risks_open(conn, *, organization_id=None, filters=None, search=None):
    items: list[dict[str, Any]] = []
    if table_exists(conn, "app_customer_risk"):
        where = ["status IN ('open', 'intervention_required', 'monitoring')"]
        params: list[Any] = []
        if organization_id is not None:
            where.append("organization_id = ?")
            params.append(organization_id)
        sql = f"""
            SELECT id, 'risk' AS kind, status, severity, organization_id, updated_at
            FROM app_customer_risk
            WHERE {' AND '.join(where)}
        """
        items.extend(_safe_query(conn, sql, params, required_tables=("app_customer_risk",)))
    if table_exists(conn, "app_customer_intervention"):
        where = ["status IN ('planned', 'in_progress')"]
        params = []
        if organization_id is not None and _has_column(conn, "app_customer_intervention", "organization_id"):
            where.append("organization_id = ?")
            params.append(organization_id)
        org_expr = "organization_id" if _has_column(conn, "app_customer_intervention", "organization_id") else "NULL"
        upd = "updated_at" if _has_column(conn, "app_customer_intervention", "updated_at") else "created_at"
        sev = "severity" if _has_column(conn, "app_customer_intervention", "severity") else "'medium'"
        sql = f"""
            SELECT id, 'intervention' AS kind, status, {sev} AS severity,
                   {org_expr} AS organization_id, {upd} AS updated_at
            FROM app_customer_intervention
            WHERE {' AND '.join(where)}
        """
        items.extend(_safe_query(conn, sql, params, required_tables=("app_customer_intervention",)))
    items.sort(key=lambda x: str(x.get("updated_at") or ""), reverse=True)
    return items


def _cs_renewals_low(conn, *, organization_id=None, filters=None, search=None):
    where = [
        "(LOWER(CAST(readiness_state AS VARCHAR)) IN ('low', 'at_risk', 'poor', 'not_ready')"
        " OR CAST(score AS DOUBLE) < 50)"
    ]
    params: list[Any] = []
    if organization_id is not None:
        where.append("organization_id = ?")
        params.append(organization_id)
    sql = f"""
        SELECT id, organization_id, readiness_state, score, evaluated_at
        FROM app_renewal_readiness
        WHERE {' AND '.join(where)}
        ORDER BY evaluated_at DESC NULLS LAST
    """
    return _safe_query(conn, sql, params, required_tables=("app_renewal_readiness",))


def _playlists_empty(conn, *, organization_id=None, filters=None, search=None):
    return _safe_query(
        conn,
        """
        SELECT p.id, p.name, p.user_id, p.created_at
        FROM app_playlist p
        LEFT JOIN app_playlist_track pt ON pt.playlist_id = p.id
        GROUP BY p.id, p.name, p.user_id, p.created_at
        HAVING COUNT(pt.track_id) = 0
        ORDER BY p.created_at DESC
        """,
        [],
        required_tables=("app_playlist", "app_playlist_track"),
    )


def _tracks_without_audio(conn, *, organization_id=None, filters=None, search=None):
    if not table_exists(conn, "dim_track"):
        return []
    if table_exists(conn, "app_track_audio_source"):
        return _safe_query(
            conn,
            """
            SELECT t.id_track AS track_id, t.nombre_track AS track_name
            FROM dim_track t
            LEFT JOIN app_track_audio_source s ON s.track_id = t.id_track
            WHERE s.track_id IS NULL
            ORDER BY t.id_track
            LIMIT 1000
            """,
            [],
            required_tables=("dim_track",),
        )
    return []


def _data_quality_failed(conn, *, organization_id=None, filters=None, search=None):
    # Spec 044: platform-scoped for engineer. Do not pretend org filter.
    return _safe_query(
        conn,
        """
        SELECT id, check_code, status, details, measured_at
        FROM app_data_quality_result
        WHERE status = 'fail'
        ORDER BY measured_at DESC NULLS LAST
        """,
        [],
        required_tables=("app_data_quality_result",),
    )


def _etl_loads_failed(conn, *, organization_id=None, filters=None, search=None):
    if not table_exists(conn, "app_job_execution"):
        return []
    if table_exists(conn, "app_background_job"):
        return _safe_query(
            conn,
            """
            SELECT e.id, e.job_id, COALESCE(j.job_code, CAST(e.job_id AS VARCHAR)) AS job_code,
                   e.status, e.error_message, e.finished_at
            FROM app_job_execution e
            LEFT JOIN app_background_job j ON j.id = e.job_id
            WHERE e.status IN ('failed', 'dead_letter')
            ORDER BY e.finished_at DESC NULLS LAST
            """,
            [],
            required_tables=("app_job_execution",),
        )
    return _safe_query(
        conn,
        """
        SELECT id, job_id, CAST(job_id AS VARCHAR) AS job_code,
               status, error_message, finished_at
        FROM app_job_execution
        WHERE status IN ('failed', 'dead_letter')
        ORDER BY finished_at DESC NULLS LAST
        """,
        [],
        required_tables=("app_job_execution",),
    )


def _analytical_tables_refresh(conn, *, organization_id=None, filters=None, search=None):
    candidates = [
        ("agg_dashboard_cache", "computed_at", "computed_at"),
        ("agg_daily_streams", "fecha", "max(fecha)"),
        ("agg_tracks_populares", None, None),
        ("agg_artist_growth", None, None),
        ("agg_genero_popularidad", None, None),
        ("agg_user_engagement", None, None),
        ("agg_platform_usage", None, None),
    ]
    results = []
    for table, col, expr in candidates:
        if not table_exists(conn, table):
            continue
        try:
            if col and expr == "computed_at":
                row = conn.execute(f"SELECT MAX({col}) FROM {table}").fetchone()
                results.append({
                    "table_name": table,
                    "last_updated_at": row[0].isoformat(sep=" ", timespec="seconds") if row and row[0] else None,
                    "source": col,
                })
            elif col:
                row = conn.execute(f"SELECT MAX({col}) FROM {table}").fetchone()
                results.append({
                    "table_name": table,
                    "last_updated_at": str(row[0]) if row and row[0] is not None else None,
                    "source": col,
                })
            else:
                results.append({
                    "table_name": table,
                    "last_updated_at": None,
                    "source": "tabla presente (sin columna de refresco)",
                })
        except Exception:
            results.append({
                "table_name": table,
                "last_updated_at": None,
                "source": "no disponible",
            })
    return results


def _audio_source_errors(conn, *, organization_id=None, filters=None, search=None):
    return _safe_query(
        conn,
        """
        SELECT s.track_id, COALESCE(t.nombre_track, CAST(s.track_id AS VARCHAR)) AS track_name,
               s.provider, s.status, s.failure_count
        FROM app_track_audio_source s
        LEFT JOIN dim_track t ON t.id_track = s.track_id
        WHERE s.status IN ('error', 'not_found', 'disabled')
        ORDER BY COALESCE(s.failure_count, 0) DESC, s.track_id
        """,
        [],
        required_tables=("app_track_audio_source",),
    )


def _ops_incidents_open(conn, *, organization_id=None, filters=None, search=None):
    return _safe_query(
        conn,
        """
        SELECT id, title, severity, status, reported_at
        FROM app_operational_incident
        WHERE status IN ('open', 'investigating')
        ORDER BY reported_at DESC
        """,
        [],
        required_tables=("app_operational_incident",),
    )


def _job_executions_failed(conn, *, organization_id=None, filters=None, search=None):
    return _safe_query(
        conn,
        """
        SELECT id, job_id, status, error_message, finished_at
        FROM app_job_execution
        WHERE status IN ('failed', 'dead_letter')
        ORDER BY finished_at DESC NULLS LAST
        """,
        [],
        required_tables=("app_job_execution",),
    )


def _sessions_active(conn, *, organization_id=None, filters=None, search=None):
    # Never return token
    return _safe_query(
        conn,
        """
        SELECT s.user_id, u.email, s.created_at, s.expires_at
        FROM app_session s
        LEFT JOIN app_user u ON u.id = s.user_id
        WHERE s.expires_at IS NULL OR s.expires_at > CURRENT_TIMESTAMP
        ORDER BY s.created_at DESC
        """,
        [],
        required_tables=("app_session",),
    )


def _roles_permissions(conn, *, organization_id=None, filters=None, search=None):
    items: list[dict[str, Any]] = []
    if table_exists(conn, "app_platform_role") and table_exists(conn, "app_platform_permission"):
        items.extend(_safe_query(
            conn,
            """
            SELECT r.code AS role_code, COALESCE(r.display_name, r.code) AS role_name,
                   p.code AS permission_code, 'platform' AS scope
            FROM app_platform_role r
            JOIN app_platform_role_permission rp ON rp.role_id = r.id
            JOIN app_platform_permission p ON p.id = rp.permission_id
            ORDER BY r.code, p.code
            """,
            [],
            required_tables=("app_platform_role", "app_platform_role_permission", "app_platform_permission"),
        ))
    if table_exists(conn, "app_business_role") and table_exists(conn, "app_permission"):
        items.extend(_safe_query(
            conn,
            """
            SELECT r.code AS role_code, COALESCE(r.display_name, r.code) AS role_name,
                   p.code AS permission_code, 'organization' AS scope
            FROM app_business_role r
            JOIN app_role_permission rp ON rp.role_id = r.id
            JOIN app_permission p ON p.id = rp.permission_id
            ORDER BY r.code, p.code
            """,
            [],
            required_tables=("app_business_role", "app_role_permission", "app_permission"),
        ))
    if not items and table_exists(conn, "app_user"):
        # Fallback: distinct global roles from users
        rows = _safe_query(
            conn,
            "SELECT DISTINCT role AS role_code, role AS role_name, '*' AS permission_code, 'global' AS scope FROM app_user WHERE role IS NOT NULL",
            [],
            required_tables=("app_user",),
        )
        items.extend(rows)
    return items


def _has_column(conn: duckdb.DuckDBPyConnection, table: str, column: str) -> bool:
    try:
        row = conn.execute(
            """
            SELECT 1 FROM information_schema.columns
            WHERE table_name = ? AND column_name = ?
            LIMIT 1
            """,
            [table, column],
        ).fetchone()
        return row is not None
    except Exception:
        return False


def _existing_columns(conn: duckdb.DuckDBPyConnection, table: str, candidates: list[str]) -> list[str]:
    return [c for c in candidates if _has_column(conn, table, c)]


RUNNERS = {
    "business-alerts-open": _business_alerts_open,
    "kpi-last-update": _kpi_last_update,
    "crm-opportunities-open": _crm_opportunities_open,
    "crm-quotations-pending": _crm_quotations_pending,
    "campaigns-active": _campaigns_active,
    "releases-pending-review": _releases_pending,
    "release-review-issues-open": _release_issues_open,
    "tracks-without-cover": _tracks_without_cover,
    "tracks-incomplete-metadata": _tracks_incomplete_metadata,
    "rights-contracts-active": _rights_contracts_active,
    "rights-conflicts-open": _rights_conflicts_open,
    "rights-contracts-expiring": _rights_contracts_expiring,
    "b2c-subscriptions-active": _b2c_active,
    "b2c-subscriptions-past-due": _b2c_past_due,
    "b2b-subscriptions-active": _b2b_active,
    "b2b-subscriptions-past-due": _b2b_past_due,
    "invoices-pending-overdue": _invoices_pending,
    "payment-attempts-failed": _payment_attempts_failed,
    "royalty-settlements-open": _royalty_settlements_open,
    "payouts-with-error": _payouts_with_error,
    "support-cases-open": _support_cases_open,
    "cs-risks-open": _cs_risks_open,
    "cs-renewals-low-readiness": _cs_renewals_low,
    "playlists-empty": _playlists_empty,
    "tracks-without-audio": _tracks_without_audio,
    "data-quality-failed": _data_quality_failed,
    "etl-loads-failed": _etl_loads_failed,
    "analytical-tables-refresh": _analytical_tables_refresh,
    "audio-source-errors": _audio_source_errors,
    "ops-incidents-open": _ops_incidents_open,
    "job-executions-failed": _job_executions_failed,
    "sessions-active": _sessions_active,
    "roles-permissions": _roles_permissions,
}
