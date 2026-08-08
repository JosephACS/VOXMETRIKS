"""Recording demo fixtures — VOXMETRIKS Demo only (slug=voxmetriks-demo).

Idempotent synthetic fixtures for the academic video:
- org-scoped billing / CRM / alerts
- varied agg_daily_streams (global analytics warehouse, marked synthetic)

Does NOT touch other organizations.
Does NOT hardcode Angular values.
Opt-in:

    python apps/backend/scripts/seed_recording_demo_fixtures.py

No Git / no Docker.
"""

from __future__ import annotations

import hashlib
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

ORG_SLUG = "voxmetriks-demo"


def _table_exists(conn, table: str) -> bool:
    row = conn.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
        [table],
    ).fetchone()
    return bool(row and row[0] > 0)


def _next_id(conn, table: str) -> int:
    row = conn.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table}").fetchone()
    return int(row[0])


def _has_column(conn, table: str, column: str) -> bool:
    try:
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info('{table}')").fetchall()]
        return column in cols
    except Exception:
        return False


def _daily_streams(day: date) -> int:
    """Deterministic varied daily streams (no negatives)."""
    # Weekend bump
    weekend = 1 if day.weekday() >= 5 else 0
    h = hashlib.sha256(f"vox-demo-streams-{day.isoformat()}".encode()).hexdigest()
    n = int(h[:8], 16)
    # Map to ranges: low / mid / high
    bucket = n % 10
    if bucket <= 2:
        base = 4800 + (n % 1001)  # 4800–5800
    elif bucket <= 7:
        base = 6000 + (n % 1001)  # 6000–7000
    else:
        base = 7200 + (n % 1001)  # 7200–8200
    return int(base + weekend * 350)


def seed_recording_fixtures(conn) -> dict:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    report: dict = {"ok": True, "org_id": None, "actions": [], "errors": []}

    org = conn.execute(
        "SELECT id FROM app_organization WHERE slug = ?", [ORG_SLUG]
    ).fetchone()
    if not org:
        report["ok"] = False
        report["errors"].append("VOXMETRIKS Demo org not found (slug=voxmetriks-demo)")
        return report
    org_id = int(org[0])
    report["org_id"] = org_id

    # Period: prefer warehouse month, else current month
    period_start = date(now.year, now.month, 1)
    if _table_exists(conn, "agg_daily_streams"):
        row = conn.execute("SELECT MAX(fecha) FROM agg_daily_streams").fetchone()
        if row and row[0] is not None and hasattr(row[0], "year"):
            max_d = row[0]
            period_start = date(max_d.year, max_d.month, 1)
    if period_start.month == 12:
        period_end = date(period_start.year + 1, 1, 1)
    else:
        period_end = date(period_start.year, period_start.month + 1, 1)
    mid = period_start + timedelta(days=10)
    report["period"] = f"{period_start.year:04d}-{period_start.month:02d}"

    # --- Payments ~$480 for org in period ---
    if _table_exists(conn, "app_payment"):
        try:
            # Scale/create a marked recording payment via existing attempt if possible
            total = conn.execute(
                """
                SELECT COALESCE(SUM(amount), 0) FROM app_payment
                WHERE organization_id = ?
                  AND status IN ('recorded', 'reconciled', 'partially_refunded')
                  AND COALESCE(settled_at, created_at) >= ?
                  AND COALESCE(settled_at, created_at) < ?
                """,
                [org_id, period_start, period_end],
            ).fetchone()
            current = float(total[0] or 0)
            target = 480.0
            if current < 400:
                # Prefer updating a demo payment amount if one exists
                pay = conn.execute(
                    """
                    SELECT id, amount FROM app_payment
                    WHERE organization_id = ?
                      AND (provider_payment_id LIKE 'demo%' OR provider_payment_id LIKE 'REC-DEMO%')
                    ORDER BY id
                    LIMIT 1
                    """,
                    [org_id],
                ).fetchone()
                if pay:
                    pid = int(pay[0])
                    conn.execute(
                        """
                        UPDATE app_payment
                        SET amount = ?, status = 'reconciled', settled_at = ?, updated_at = ?,
                            provider_payment_id = 'REC-DEMO-PAY-480'
                        WHERE id = ? AND organization_id = ?
                        """,
                        [target, mid, now, pid, org_id],
                    )
                    report["actions"].append(f"payment_updated id={pid} amount={target}")
                elif _table_exists(conn, "app_payment_attempt"):
                    # Create attempt+payment chain
                    inv = None
                    if _table_exists(conn, "app_invoice"):
                        inv = conn.execute(
                            """
                            SELECT id FROM app_invoice
                            WHERE organization_id = ? AND invoice_number LIKE 'DEMO-INV%'
                            ORDER BY id LIMIT 1
                            """,
                            [org_id],
                        ).fetchone()
                    invoice_id = int(inv[0]) if inv else None
                    attempt_id = _next_id(conn, "app_payment_attempt")
                    key = "REC-DEMO-ATTEMPT-480"
                    existing = conn.execute(
                        "SELECT id FROM app_payment_attempt WHERE idempotency_key = ?", [key]
                    ).fetchone()
                    if existing:
                        attempt_id = int(existing[0])
                    else:
                        cols = "id, organization_id, invoice_id, provider_code, amount, currency, status, idempotency_key, created_at, updated_at"
                        # schema may vary — try minimal insert
                        try:
                            conn.execute(
                                f"""
                                INSERT INTO app_payment_attempt
                                  (id, organization_id, invoice_id, provider_code, amount, currency,
                                   status, idempotency_key, created_at, updated_at)
                                VALUES (?, ?, ?, 'mock', ?, 'USD', 'succeeded', ?, ?, ?)
                                """,
                                [attempt_id, org_id, invoice_id, target, key, now, now],
                            )
                        except Exception as e:
                            report["errors"].append(f"payment_attempt: {e}")
                            attempt_id = None
                    if attempt_id:
                        pay_exist = conn.execute(
                            "SELECT id FROM app_payment WHERE payment_attempt_id = ?",
                            [attempt_id],
                        ).fetchone()
                        if pay_exist:
                            conn.execute(
                                """
                                UPDATE app_payment SET amount = ?, status = 'reconciled',
                                  settled_at = ?, updated_at = ?, provider_payment_id = 'REC-DEMO-PAY-480'
                                WHERE id = ?
                                """,
                                [target, mid, now, int(pay_exist[0])],
                            )
                        else:
                            pid = _next_id(conn, "app_payment")
                            conn.execute(
                                """
                                INSERT INTO app_payment
                                  (id, organization_id, payment_attempt_id, provider_code, amount, currency,
                                   status, provider_payment_id, settled_at, reconciled_at, created_at, updated_at)
                                VALUES (?, ?, ?, 'mock', ?, 'USD', 'reconciled', 'REC-DEMO-PAY-480', ?, ?, ?, ?)
                                """,
                                [pid, org_id, attempt_id, target, mid, mid, now, now],
                            )
                        report["actions"].append(f"payment_ensured amount={target}")
            else:
                report["actions"].append(f"payment_ok current={current}")
        except Exception as e:
            report["errors"].append(f"payments: {e}")

    # --- Pending invoices: ensure at least 2 ---
    if _table_exists(conn, "app_invoice"):
        try:
            pending = conn.execute(
                """
                SELECT COUNT(*) FROM app_invoice
                WHERE organization_id = ?
                  AND status IN ('issued', 'partially_paid', 'past_due')
                """,
                [org_id],
            ).fetchone()
            n = int(pending[0] or 0)
            # Create DEMO-INV-PENDING-REC-003 if needed
            for num, label in [
                ("DEMO-INV-PENDING-002", "pending_a"),
                ("DEMO-INV-PENDING-REC-003", "pending_b"),
            ]:
                exists = conn.execute(
                    "SELECT id FROM app_invoice WHERE invoice_number = ?", [num]
                ).fetchone()
                if exists:
                    # DuckDB ART: SET organization_id (even to same value) can raise false PK duplicate
                    conn.execute(
                        """
                        UPDATE app_invoice
                        SET status = 'issued', updated_at = ?
                        WHERE invoice_number = ?
                          AND status NOT IN ('issued', 'partially_paid', 'past_due')
                        """,
                        [now, num],
                    )
                    continue
                if n >= 2 and num.endswith("003"):
                    continue
                # Need billing profile
                bp = conn.execute(
                    "SELECT id FROM app_billing_profile WHERE organization_id = ? LIMIT 1",
                    [org_id],
                ).fetchone() if _table_exists(conn, "app_billing_profile") else None
                if not bp:
                    report["actions"].append("invoice_skip_no_billing_profile")
                    break
                iid = _next_id(conn, "app_invoice")
                conn.execute(
                    """
                    INSERT INTO app_invoice
                      (id, organization_id, billing_profile_id, invoice_number, currency, status,
                       subtotal, total, amount_paid, amount_due, issued_at, due_date, created_at, updated_at)
                    VALUES (?, ?, ?, ?, 'USD', 'issued', 120.00, 120.00, 0, 120.00, ?, ?, ?, ?)
                    """,
                    [iid, org_id, int(bp[0]), num, mid, mid + timedelta(days=15), now, now],
                )
                n += 1
                report["actions"].append(f"invoice_created {num}")
            report["actions"].append(f"pending_invoices≈{n}")
        except Exception as e:
            report["errors"].append(f"invoices: {e}")

    # --- Open opportunities: ensure 3 ---
    if _table_exists(conn, "app_crm_opportunity"):
        try:
            open_n = conn.execute(
                """
                SELECT COUNT(*) FROM app_crm_opportunity
                WHERE organization_id = ?
                  AND deleted_at IS NULL
                  AND LOWER(CAST(stage AS VARCHAR)) NOT IN
                    ('won','lost','closed','closed_won','closed_lost')
                """,
                [org_id],
            ).fetchone()
            count_open = int(open_n[0] or 0)
            if count_open < 3:
                prosp = conn.execute(
                    "SELECT id FROM app_crm_prospect WHERE organization_id = ? LIMIT 1",
                    [org_id],
                ).fetchone() if _table_exists(conn, "app_crm_prospect") else None
                if prosp:
                    for i in range(3 - count_open):
                        name = f"Recording Demo Opportunity {i+1} (Synthetic)"
                        exists = conn.execute(
                            "SELECT id FROM app_crm_opportunity WHERE name = ? AND organization_id = ?",
                            [name, org_id],
                        ).fetchone()
                        if exists:
                            continue
                        oid = _next_id(conn, "app_crm_opportunity")
                        owner = None
                        if _table_exists(conn, "app_organization_member"):
                            owner = conn.execute(
                                """
                                SELECT m.user_id FROM app_organization_member m
                                LEFT JOIN app_user u ON u.id = m.user_id
                                WHERE m.organization_id = ?
                                  AND COALESCE(m.status, 'active') = 'active'
                                ORDER BY CASE WHEN LOWER(COALESCE(u.username, '')) = 'admin' THEN 0 ELSE 1 END,
                                         m.user_id
                                LIMIT 1
                                """,
                                [org_id],
                            ).fetchone()
                        if not owner:
                            owner = conn.execute(
                                "SELECT id FROM app_user WHERE LOWER(username) = 'admin' LIMIT 1"
                            ).fetchone()
                        if not owner:
                            owner = conn.execute(
                                "SELECT id FROM app_user ORDER BY id LIMIT 1"
                            ).fetchone()
                        if not owner:
                            report["errors"].append("opportunities: no owner_user_id available")
                            break
                        owner_user_id = int(owner[0])
                        conn.execute(
                            """
                            INSERT INTO app_crm_opportunity
                              (id, prospect_id, name, description, stage, probability,
                               expected_value, currency, expected_close_date, actual_close_date,
                               outcome, owner_user_id, organization_id, created_at, updated_at, deleted_at)
                            VALUES (?, ?, ?, '[SYNTHETIC] recording fixture', 'proposal', 50,
                                    3500.00, 'USD', NULL, NULL, NULL, ?, ?, ?, ?, NULL)
                            """,
                            [oid, int(prosp[0]), name, owner_user_id, org_id, now, now],
                        )
                        report["actions"].append(f"opportunity_created {name}")
            report["actions"].append(f"open_opportunities_ok")
        except Exception as e:
            report["errors"].append(f"opportunities: {e}")

    # --- One open business alert ---
    if _table_exists(conn, "app_business_alert"):
        try:
            title = "Recording Demo Alert (Synthetic)"
            existing = conn.execute(
                "SELECT id FROM app_business_alert WHERE title = ? AND organization_id = ?",
                [title, org_id],
            ).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE app_business_alert SET status = 'open', updated_at = ?
                    WHERE id = ?
                    """,
                    [now, int(existing[0])],
                )
                report["actions"].append("alert_reopened")
            else:
                aid = _next_id(conn, "app_business_alert")
                conn.execute(
                    """
                    INSERT INTO app_business_alert
                      (id, organization_id, severity, title, body, status, kpi_code, created_at, updated_at)
                    VALUES (?, ?, 'warning', ?, '[SYNTHETIC] Alerta de demostración para video',
                            'open', 'demo_recording', ?, ?)
                    """,
                    [aid, org_id, title, now, now],
                )
                report["actions"].append("alert_created")
        except Exception as e:
            report["errors"].append(f"alerts: {e}")

    # --- Varied daily streams (30 days ending at max fecha or today) ---
    if _table_exists(conn, "agg_daily_streams"):
        try:
            row = conn.execute("SELECT MAX(fecha) FROM agg_daily_streams").fetchone()
            end_day = row[0] if row and row[0] is not None else date.today()
            if not hasattr(end_day, "year"):
                end_day = date.today()
            start_day = end_day - timedelta(days=29)
            # Detect columns
            has_skip_rate = _has_column(conn, "agg_daily_streams", "skip_rate")
            has_skip_count = _has_column(conn, "agg_daily_streams", "skip_count")
            d = start_day
            updated = 0
            while d <= end_day:
                streams = _daily_streams(d)
                users = max(80, streams // 45)
                tracks = max(40, streams // 90)
                exists = conn.execute(
                    "SELECT 1 FROM agg_daily_streams WHERE fecha = ?", [d]
                ).fetchone()
                if exists:
                    if has_skip_rate:
                        conn.execute(
                            """
                            UPDATE agg_daily_streams
                            SET total_streams = ?, unique_users = ?, unique_tracks = ?
                            WHERE fecha = ?
                            """,
                            [streams, users, tracks, d],
                        )
                    else:
                        conn.execute(
                            """
                            UPDATE agg_daily_streams
                            SET total_streams = ?, unique_users = ?, unique_tracks = ?
                            WHERE fecha = ?
                            """,
                            [streams, users, tracks, d],
                        )
                else:
                    if has_skip_rate:
                        conn.execute(
                            """
                            INSERT INTO agg_daily_streams
                              (fecha, total_streams, unique_users, unique_tracks, avg_duration_ms, skip_rate)
                            VALUES (?, ?, ?, ?, 180000, 0.12)
                            """,
                            [d, streams, users, tracks],
                        )
                    elif has_skip_count:
                        conn.execute(
                            """
                            INSERT INTO agg_daily_streams
                              (fecha, total_streams, unique_users, unique_tracks, avg_duration_ms, skip_count)
                            VALUES (?, ?, ?, ?, 180000, 0)
                            """,
                            [d, streams, users, tracks],
                        )
                    else:
                        conn.execute(
                            """
                            INSERT INTO agg_daily_streams
                              (fecha, total_streams, unique_users, unique_tracks)
                            VALUES (?, ?, ?, ?)
                            """,
                            [d, streams, users, tracks],
                        )
                updated += 1
                d += timedelta(days=1)
            tot = conn.execute(
                """
                SELECT COALESCE(SUM(total_streams),0), COUNT(*),
                       COALESCE(AVG(total_streams),0), COALESCE(MAX(total_streams),0)
                FROM agg_daily_streams WHERE fecha >= ? AND fecha <= ?
                """,
                [start_day, end_day],
            ).fetchone()
            report["streams"] = {
                "days": updated,
                "total": int(tot[0]),
                "count": int(tot[1]),
                "average": round(float(tot[2]), 2),
                "max": int(tot[3]),
                "from": start_day.isoformat(),
                "to": end_day.isoformat(),
            }
            report["actions"].append("agg_daily_streams_varied")
        except Exception as e:
            report["errors"].append(f"streams: {e}")

    report["ok"] = report["ok"] and not report["errors"]
    return report


def main() -> int:
    from app.core.database import get_connection

    conn = get_connection()
    try:
        result = seed_recording_fixtures(conn)
        print(result)
        return 0 if result.get("ok") else 1
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
