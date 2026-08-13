"""Repair demo monthly series for complex reports (deterministic).

Spreads existing operational demo rows across ~12 months and clones
template rows where needed. Does not invent frontend values.

    python apps/backend/scripts/repair_demo_monthly_series.py
"""

from __future__ import annotations

import hashlib
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]
_ROOT = _BACKEND.parents[1]
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

SEED = "044-voxmetriks-demo-monthly"
MONTHS = 12
# VOXMETRIKS Demo org used by staff Reportes UI (X-Organization-Id).
DEMO_ORG_ID = 1
STATUSES = (
    "draft",
    "changes_requested",
    "published",
    "scheduled",
    "withdrawn",
)


def _h(key: str) -> int:
    return int(hashlib.sha256(f"{SEED}:{key}".encode()).hexdigest()[:8], 16)


def _month_starts(end: date, n: int) -> list[date]:
    y, m = end.year, end.month
    out: list[date] = []
    for _ in range(n):
        out.append(date(y, m, 1))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    out.reverse()
    return out


def main() -> int:
    import duckdb

    db = _ROOT / "data" / "warehouse" / "voxmetrik.duckdb"
    if not db.exists():
        print(f"DB missing: {db}")
        return 1

    conn = duckdb.connect(str(db))
    try:
        tables = {r[0] for r in conn.execute("SHOW TABLES").fetchall()}
        end = date.today().replace(day=1)
        if "agg_daily_streams" in tables:
            row = conn.execute("SELECT MAX(fecha) FROM agg_daily_streams").fetchone()
            if row and row[0] is not None and hasattr(row[0], "year"):
                end = date(row[0].year, row[0].month, 1)
        months = _month_starts(end, MONTHS)
        print(f"Spreading demo months ending {end.isoformat()} ({len(months)})")

        if "app_payment" in tables:
            # Ensure DEMO_ORG has one recorded payment per month (UI scopes by org).
            template = conn.execute(
                """
                SELECT payment_attempt_id, provider_code, currency
                FROM app_payment
                WHERE organization_id = ?
                ORDER BY id LIMIT 1
                """,
                [DEMO_ORG_ID],
            ).fetchone()
            if not template:
                template = conn.execute(
                    "SELECT payment_attempt_id, provider_code, currency FROM app_payment ORDER BY id LIMIT 1"
                ).fetchone()
            if template:
                attempt_id, provider, currency = template
                max_id = int(conn.execute("SELECT COALESCE(MAX(id),0) FROM app_payment").fetchone()[0])
                for i, m0 in enumerate(months):
                    ym = m0.strftime("%Y-%m")
                    existing = conn.execute(
                        """
                        SELECT id FROM app_payment
                        WHERE organization_id = ?
                          AND strftime(COALESCE(settled_at, created_at), '%Y-%m') = ?
                        ORDER BY id LIMIT 1
                        """,
                        [DEMO_ORG_ID, ym],
                    ).fetchone()
                    amount = 1800 + (_h(f"pay:{DEMO_ORG_ID}:{ym}") % 4200) + i * 55
                    ts = datetime(m0.year, m0.month, 12 + (i % 10), 12, 0, 0)
                    if existing:
                        conn.execute(
                            """
                            UPDATE app_payment
                            SET amount = ?, status = 'recorded',
                                created_at = ?, settled_at = ?, updated_at = ?
                            WHERE id = ?
                            """,
                            [float(amount), ts, ts, ts, existing[0]],
                        )
                    else:
                        max_id += 1
                        conn.execute(
                            """
                            INSERT INTO app_payment (
                              id, organization_id, payment_attempt_id, provider_code,
                              amount, currency, status, settled_at, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, 'recorded', ?, ?, ?)
                            """,
                            [
                                max_id,
                                DEMO_ORG_ID,
                                attempt_id,
                                provider,
                                float(amount),
                                currency or "USD",
                                ts,
                                ts,
                                ts,
                            ],
                        )
                print(f"app_payment: demo org {DEMO_ORG_ID} months repaired")

        if "app_subscription" in tables:
            template = conn.execute(
                """
                SELECT plan_id, plan_price_id, billing_currency, status, access_state
                FROM app_subscription
                WHERE organization_id = ?
                ORDER BY id LIMIT 1
                """,
                [DEMO_ORG_ID],
            ).fetchone()
            if not template:
                template = conn.execute(
                    """
                    SELECT plan_id, plan_price_id, billing_currency, status, access_state
                    FROM app_subscription ORDER BY id LIMIT 1
                    """
                ).fetchone()
            if template:
                plan_id, plan_price_id, currency, status, access = template
                max_id = int(conn.execute("SELECT COALESCE(MAX(id),0) FROM app_subscription").fetchone()[0])
                for i, m0 in enumerate(months):
                    ym = m0.strftime("%Y-%m")
                    n = 4 + (_h(f"sub:{DEMO_ORG_ID}:{ym}") % 9)
                    have = conn.execute(
                        """
                        SELECT COUNT(*) FROM app_subscription
                        WHERE organization_id = ? AND strftime(created_at,'%Y-%m') = ?
                        """,
                        [DEMO_ORG_ID, ym],
                    ).fetchone()[0]
                    need = max(0, n - int(have or 0))
                    for j in range(need):
                        max_id += 1
                        ts = datetime(m0.year, m0.month, min(3 + j, 27), 10, j % 50, 0)
                        conn.execute(
                            """
                            INSERT INTO app_subscription (
                              id, organization_id, plan_id, plan_price_id, status,
                              billing_currency, current_period_start, cancel_at_period_end,
                              access_state, created_at, updated_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, FALSE, ?, ?, ?)
                            """,
                            [
                                max_id,
                                DEMO_ORG_ID,
                                plan_id,
                                plan_price_id,
                                status or "active",
                                currency or "USD",
                                m0,
                                access or "full",
                                ts,
                                ts,
                            ],
                        )
                print(f"app_subscription: demo org {DEMO_ORG_ID} months repaired")

        if "app_crm_opportunity" in tables:
            conn.execute(
                "DELETE FROM app_crm_opportunity WHERE name LIKE ? AND organization_id = ?",
                [f"demo:{SEED}%", DEMO_ORG_ID],
            )
            template = conn.execute(
                """
                SELECT prospect_id, owner_user_id, currency
                FROM app_crm_opportunity
                WHERE organization_id = ?
                ORDER BY id LIMIT 1
                """,
                [DEMO_ORG_ID],
            ).fetchone()
            if not template:
                template = conn.execute(
                    """
                    SELECT prospect_id, owner_user_id, currency
                    FROM app_crm_opportunity ORDER BY id LIMIT 1
                    """
                ).fetchone()
            if template:
                prospect_id, owner_id, currency = template
                max_id = int(conn.execute("SELECT COALESCE(MAX(id),0) FROM app_crm_opportunity").fetchone()[0])
                for i, m0 in enumerate(months):
                    closed = 7 + (_h(f"crmn:{DEMO_ORG_ID}:{m0.isoformat()}") % 9)
                    won = max(1, int(round(closed * (0.28 + (_h(f"wr:{DEMO_ORG_ID}:{m0}") % 45) / 100))))
                    for j in range(closed):
                        max_id += 1
                        stage = "closed_won" if j < won else "closed_lost"
                        ts = datetime(m0.year, m0.month, min(4 + j, 27), 12, 0, 0)
                        conn.execute(
                            """
                            INSERT INTO app_crm_opportunity (
                              id, prospect_id, name, stage, probability, currency,
                              owner_user_id, organization_id, created_at, updated_at, actual_close_date
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            [
                                max_id,
                                prospect_id,
                                f"demo:{SEED}:{m0.isoformat()}:{j}",
                                stage,
                                50,
                                currency or "USD",
                                owner_id,
                                DEMO_ORG_ID,
                                ts,
                                ts,
                                m0,
                            ],
                        )
                print(f"app_crm_opportunity: demo org {DEMO_ORG_ID} months repaired")

        sub_table = None
        for candidate in ("app_catalog_submission", "app_release_submission", "app_publishing_submission"):
            if candidate in tables:
                sub_table = candidate
                break
        if not sub_table:
            # fallback search
            for t in tables:
                if "submission" in t.lower():
                    sub_table = t
                    break
        if sub_table:
            cols = {r[0] for r in conn.execute(f"DESCRIBE {sub_table}").fetchall()}
            if "status" in cols and "created_at" in cols and "id" in cols:
                try:
                    # DuckDB can throw spurious PK errors on UPDATE of this table;
                    # prefer created_at-only updates + INSERT clones for missing months.
                    rows = conn.execute(
                        f"""
                        SELECT id, organization_id, artist_profile_id, release_type, title,
                               created_by, status
                        FROM {sub_table}
                        WHERE organization_id = ?
                          AND COALESCE(is_demo, FALSE) = TRUE
                        ORDER BY id
                        """
                        if "is_demo" in cols
                        else f"""
                        SELECT id, organization_id, artist_profile_id, release_type, title,
                               created_by, status
                        FROM {sub_table}
                        WHERE organization_id = ?
                        ORDER BY id
                        """,
                        [DEMO_ORG_ID],
                    ).fetchall()
                    if not rows:
                        print(f"{sub_table}: no demo rows to spread")
                    else:
                        for i, (rid, *_rest) in enumerate(rows):
                            m0 = months[i % len(months)]
                            ts = datetime(m0.year, m0.month, 6 + (i % 20), 9, 0, 0)
                            conn.execute(
                                f"UPDATE {sub_table} SET created_at = ?, updated_at = ? WHERE id = ?",
                                [ts, ts, rid],
                            )
                        tmpl = rows[0]
                        org_id, artist_id, release_type, title, created_by = (
                            DEMO_ORG_ID,
                            tmpl[2],
                            tmpl[3],
                            tmpl[4],
                            tmpl[5],
                        )
                        max_id = conn.execute(
                            f"SELECT COALESCE(MAX(id), 0) FROM {sub_table}"
                        ).fetchone()[0]
                        # Ensure each month has a few status rows (deterministic demo).
                        for mi, m0 in enumerate(months):
                            for si, st in enumerate(STATUSES):
                                key = f"demo:{SEED}:rel:{m0.isoformat()}:{st}"
                                exists = None
                                if "idempotency_key" in cols:
                                    exists = conn.execute(
                                        f"SELECT 1 FROM {sub_table} WHERE idempotency_key = ?",
                                        [key],
                                    ).fetchone()
                                else:
                                    exists = conn.execute(
                                        f"""
                                        SELECT 1 FROM {sub_table}
                                        WHERE organization_id = ?
                                          AND status = ?
                                          AND strftime(created_at, '%Y-%m') = ?
                                          AND title LIKE 'Demo release %'
                                        LIMIT 1
                                        """,
                                        [DEMO_ORG_ID, st, m0.strftime("%Y-%m")],
                                    ).fetchone()
                                if exists:
                                    continue
                                max_id = int(max_id) + 1
                                ts = datetime(m0.year, m0.month, 8 + (si % 18), 10, 0, 0)
                                demo_title = f"Demo release {m0.strftime('%Y-%m')} · {st}"
                                if "is_demo" in cols and "idempotency_key" in cols:
                                    conn.execute(
                                        f"""
                                        INSERT INTO {sub_table}
                                          (id, organization_id, artist_profile_id, release_type, title,
                                           status, created_by, is_demo, idempotency_key, created_at, updated_at)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, TRUE, ?, ?, ?)
                                        """,
                                        [
                                            max_id,
                                            org_id,
                                            artist_id,
                                            release_type or "single",
                                            demo_title,
                                            st,
                                            created_by,
                                            key,
                                            ts,
                                            ts,
                                        ],
                                    )
                                else:
                                    conn.execute(
                                        f"""
                                        INSERT INTO {sub_table}
                                          (id, organization_id, artist_profile_id, release_type, title,
                                           status, created_by, created_at, updated_at)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                        """,
                                        [
                                            max_id,
                                            org_id,
                                            artist_id,
                                            release_type or "single",
                                            demo_title,
                                            st,
                                            created_by,
                                            ts,
                                            ts,
                                        ],
                                    )
                        print(f"{sub_table}: months repaired (clone+spread)")
                except Exception as exc:
                    print(f"{sub_table}: skipped ({exc})")
            else:
                print(f"{sub_table}: missing status/created_at/id")
        else:
            print("No submission table found for releases")

        print({"ok": True, "seed": SEED, "months": [m.isoformat() for m in months]})
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
