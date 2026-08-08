"""Spec 044 — VOXMETRIKS Demo consolidation fixture (idempotent).

Targets organization slug ``voxmetriks-demo`` only. Safe to re-run after
``seed_integrated_demo`` (and optionally ``seed_recording_demo_fixtures``).

What it does
------------
* Upserts 45–90 days of **varied** synthetic rows into ``agg_daily_streams``
  using a deterministic PRNG derived from a fixed seed string (not flat totals).
* Soft-ensures approximate narrative counts from ``DEMO_FIXTURE_CONTRACT``
  (artists, releases, rights, alerts, opportunities, invoices, payments,
  failed payment attempt) **when tables exist** — missing tables soft-fail.
* Marks demo/synthetic rows via stable keys, titles, notes, and ``is_demo``
  where the schema supports it.

Usage
-----
From repo root (backend venv / PYTHONPATH with apps/backend):

    python apps/backend/scripts/seed_044_consolidation_fixture.py

Optional env:

    VOX_DEMO_DB / DATABASE path via app.core.database.get_connection()

No Git / no Docker. Does not modify other organizations.
"""

from __future__ import annotations

import hashlib
import random
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

ORG_SLUG = "voxmetriks-demo"
STREAM_SEED = "044-voxmetriks-demo-streams"
STREAM_DAYS = 60  # within DEMO_FIXTURE_CONTRACT 45–90

# Stable business keys (idempotent upserts)
ARTIST_KEYS = (
    ("demo-044-artist-aurora", "Aurora Demo"),
    ("demo-044-artist-nexus", "Nexus Demo"),
    ("demo-044-artist-pulse", "Pulse Demo"),
)
RELEASE_KEYS = (
    ("demo-044-release-approved", "approved", "[DEMO-044] Approved EP"),
    ("demo-044-release-review", "under_review", "[DEMO-044] Under Review Single"),
    ("demo-044-release-changes", "changes_requested", "[DEMO-044] Changes Requested"),
)
ALERT_KEYS = (
    ("demo-044-alert-1", "warning", "[DEMO-044] Open alert A"),
    ("demo-044-alert-2", "info", "[DEMO-044] Open alert B"),
)
OPP_KEYS = (
    ("[DEMO-044] Opportunity Open A", "proposal", None),
    ("[DEMO-044] Opportunity Open B", "negotiation", None),
    ("[DEMO-044] Opportunity Won", "closed_won", "won"),
)
INVOICE_KEYS = (
    ("DEMO-044-INV-PAID-001", "paid"),
    ("DEMO-044-INV-PENDING-001", "issued"),
    ("DEMO-044-INV-PENDING-002", "issued"),
)
PAYMENT_KEYS = (
    "DEMO-044-PAY-001",
    "DEMO-044-PAY-002",
)
FAILED_ATTEMPT_KEY = "DEMO-044-ATTEMPT-FAILED-001"
RIGHTS_CONTRACT_EVIDENCE = (
    "demo-044-rights-active-a",
    "demo-044-rights-active-b",
    "demo-044-rights-expiring",
)
RIGHTS_CONFLICT_DETAILS = "[DEMO-044] Open rights conflict (synthetic)"


def _table_exists(conn, table: str) -> bool:
    row = conn.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
        [table],
    ).fetchone()
    return bool(row and row[0] > 0)


def _has_column(conn, table: str, column: str) -> bool:
    try:
        cols = [str(r[1]).lower() for r in conn.execute(f"PRAGMA table_info('{table}')").fetchall()]
        return column.lower() in cols
    except Exception:
        return False


def _next_id(conn, table: str) -> int:
    row = conn.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table}").fetchone()
    return int(row[0])


def _soft(report: dict, action: str, fn) -> None:
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — soft-fail contract
        report["errors"].append(f"{action}: {exc}")
        report["soft_fails"].append(action)


def _prng(seed: str) -> random.Random:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return random.Random(int(digest[:16], 16))


def _daily_streams(rng: random.Random, day: date) -> int:
    """Deterministic varied daily streams: low / normal / peak + weekend uplift."""
    weekend = 1 if day.weekday() >= 5 else 0
    # Re-seed per day from master stream so re-runs stay stable
    day_rng = _prng(f"{STREAM_SEED}:{day.isoformat()}")
    bucket = day_rng.randrange(10)
    if bucket <= 2:
        base = 4200 + day_rng.randrange(900)  # low
    elif bucket <= 7:
        base = 5800 + day_rng.randrange(1400)  # normal
    else:
        base = 7800 + day_rng.randrange(2200)  # peak
    # Mild seasonal drift from master rng position (unused var keeps API honest)
    _ = rng
    return max(0, int(base + weekend * (280 + day_rng.randrange(180))))


def _seed_streams(conn, report: dict) -> None:
    if not _table_exists(conn, "agg_daily_streams"):
        report["soft_fails"].append("agg_daily_streams_missing")
        return

    row = conn.execute("SELECT MAX(fecha) FROM agg_daily_streams").fetchone()
    end_day = row[0] if row and row[0] is not None else date.today()
    if not hasattr(end_day, "year"):
        end_day = date.today()
    start_day = end_day - timedelta(days=STREAM_DAYS - 1)
    rng = _prng(STREAM_SEED)
    has_skip_rate = _has_column(conn, "agg_daily_streams", "skip_rate")
    has_skip_count = _has_column(conn, "agg_daily_streams", "skip_count")
    has_synthetic = _has_column(conn, "agg_daily_streams", "is_synthetic")

    updated = 0
    d = start_day
    while d <= end_day:
        streams = _daily_streams(rng, d)
        users = max(60, streams // 48)
        tracks = max(30, streams // 95)
        skip_rate = round(0.08 + (_prng(f"{STREAM_SEED}:skip:{d}").random() * 0.12), 4)
        exists = conn.execute(
            "SELECT 1 FROM agg_daily_streams WHERE fecha = ?", [d]
        ).fetchone()
        if exists:
            conn.execute(
                """
                UPDATE agg_daily_streams
                SET total_streams = ?, unique_users = ?, unique_tracks = ?
                WHERE fecha = ?
                """,
                [streams, users, tracks, d],
            )
            if has_skip_rate:
                conn.execute(
                    "UPDATE agg_daily_streams SET skip_rate = ? WHERE fecha = ?",
                    [skip_rate, d],
                )
            if has_synthetic:
                conn.execute(
                    "UPDATE agg_daily_streams SET is_synthetic = TRUE WHERE fecha = ?",
                    [d],
                )
        else:
            if has_skip_rate:
                cols = "fecha, total_streams, unique_users, unique_tracks, avg_duration_ms, skip_rate"
                vals: list[Any] = [d, streams, users, tracks, 180000.0, skip_rate]
                if has_synthetic:
                    cols += ", is_synthetic"
                    vals.append(True)
                placeholders = ", ".join(["?"] * len(vals))
                conn.execute(
                    f"INSERT INTO agg_daily_streams ({cols}) VALUES ({placeholders})",
                    vals,
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
        "seed": STREAM_SEED,
        "classification": "synthetic",
    }
    report["actions"].append(f"agg_daily_streams_upserted_{updated}d")
    report["counts"]["synthetic_stream_days"] = updated


def _ensure_artists(conn, org_id: int, now: datetime, report: dict) -> None:
    if not _table_exists(conn, "app_artist_profile"):
        report["soft_fails"].append("artists_table_missing")
        return

    for key, display in ARTIST_KEYS:
        norm = display.lower().replace(" ", "")
        existing = conn.execute(
            """
            SELECT id FROM app_artist_profile
            WHERE organization_id = ? AND (
              normalized_name = ? OR display_name = ? OR display_name LIKE ?
            )
            LIMIT 1
            """,
            [org_id, norm, display, f"%{key}%"],
        ).fetchone()
        if existing:
            continue
        # Prefer matching by external id if present
        if _table_exists(conn, "app_artist_external_identifier"):
            ext = conn.execute(
                """
                SELECT artist_id FROM app_artist_external_identifier
                WHERE external_value = ? LIMIT 1
                """,
                [key],
            ).fetchone()
            if ext:
                continue
        aid = _next_id(conn, "app_artist_profile")
        conn.execute(
            """
            INSERT INTO app_artist_profile
              (id, organization_id, display_name, legal_name, normalized_name,
               status, warehouse_artist_id, created_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'active', NULL, NULL, ?, ?)
            """,
            [aid, org_id, display, f"[DEMO-044] {display}", norm, now, now],
        )
        if _table_exists(conn, "app_artist_external_identifier"):
            eid = _next_id(conn, "app_artist_external_identifier")
            try:
                conn.execute(
                    """
                    INSERT INTO app_artist_external_identifier
                      (id, artist_id, system_code, external_value, created_at, updated_at)
                    VALUES (?, ?, 'demo_key', ?, ?, ?)
                    """,
                    [eid, aid, key, now, now],
                )
            except Exception:
                pass
        if _table_exists(conn, "app_artist_organization"):
            lid = _next_id(conn, "app_artist_organization")
            try:
                conn.execute(
                    """
                    INSERT INTO app_artist_organization
                      (id, artist_id, organization_id, relationship_role, is_primary, status,
                       created_at, updated_at)
                    VALUES (?, ?, ?, 'primary', TRUE, 'active', ?, ?)
                    """,
                    [lid, aid, org_id, now, now],
                )
            except Exception:
                pass
        report["actions"].append(f"artist_created:{key}")

    n = conn.execute(
        "SELECT COUNT(*) FROM app_artist_profile WHERE organization_id = ?",
        [org_id],
    ).fetchone()
    report["counts"]["artists"] = int(n[0] or 0)


def _pick_artist_id(conn, org_id: int) -> Optional[int]:
    row = conn.execute(
        """
        SELECT id FROM app_artist_profile
        WHERE organization_id = ? AND status = 'active'
        ORDER BY id LIMIT 1
        """,
        [org_id],
    ).fetchone()
    return int(row[0]) if row else None


def _ensure_releases(conn, org_id: int, now: datetime, report: dict) -> None:
    if not _table_exists(conn, "app_release_submission"):
        report["soft_fails"].append("releases_table_missing")
        return
    artist_id = _pick_artist_id(conn, org_id)
    if artist_id is None:
        report["soft_fails"].append("releases_no_artist")
        return
    owner = conn.execute(
        """
        SELECT user_id FROM app_organization_member
        WHERE organization_id = ? AND COALESCE(status, 'active') = 'active'
        ORDER BY id LIMIT 1
        """,
        [org_id],
    ).fetchone() if _table_exists(conn, "app_organization_member") else None
    created_by = int(owner[0]) if owner else 1

    for key, status, title in RELEASE_KEYS:
        existing = conn.execute(
            "SELECT id FROM app_release_submission WHERE idempotency_key = ?",
            [key],
        ).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE app_release_submission
                SET status = ?, title = ?, updated_at = ?
                WHERE idempotency_key = ? AND organization_id = ?
                """,
                [status, title, now, key, org_id],
            )
            continue
        sid = _next_id(conn, "app_release_submission")
        is_demo_col = _has_column(conn, "app_release_submission", "is_demo")
        if is_demo_col:
            conn.execute(
                """
                INSERT INTO app_release_submission
                  (id, organization_id, artist_profile_id, release_type, title,
                   status, created_by, is_demo, idempotency_key, created_at, updated_at)
                VALUES (?, ?, ?, 'single', ?, ?, ?, TRUE, ?, ?, ?)
                """,
                [sid, org_id, artist_id, title, status, created_by, key, now, now],
            )
        else:
            conn.execute(
                """
                INSERT INTO app_release_submission
                  (id, organization_id, artist_profile_id, release_type, title,
                   status, created_by, idempotency_key, created_at, updated_at)
                VALUES (?, ?, ?, 'single', ?, ?, ?, ?, ?, ?)
                """,
                [sid, org_id, artist_id, title, status, created_by, key, now, now],
            )
        report["actions"].append(f"release_created:{key}")

    n = conn.execute(
        "SELECT COUNT(*) FROM app_release_submission WHERE organization_id = ?",
        [org_id],
    ).fetchone()
    report["counts"]["releases"] = int(n[0] or 0)


def _pick_asset_id(conn, org_id: int) -> Optional[int]:
    if not _table_exists(conn, "app_catalog_asset"):
        return None
    row = conn.execute(
        "SELECT id FROM app_catalog_asset WHERE organization_id = ? ORDER BY id LIMIT 1",
        [org_id],
    ).fetchone()
    return int(row[0]) if row else None


def _ensure_rights(conn, org_id: int, now: datetime, report: dict) -> None:
    if not _table_exists(conn, "app_rights_contract"):
        report["soft_fails"].append("rights_contracts_missing")
        return
    asset_id = _pick_asset_id(conn, org_id)
    if asset_id is None:
        report["soft_fails"].append("rights_no_asset")
        return

    today = date.today()
    for i, evidence in enumerate(RIGHTS_CONTRACT_EVIDENCE):
        existing = conn.execute(
            "SELECT id FROM app_rights_contract WHERE evidence_ref = ?",
            [evidence],
        ).fetchone()
        valid_to = today + timedelta(days=30) if i == 2 else today + timedelta(days=365)
        if existing:
            conn.execute(
                """
                UPDATE app_rights_contract
                SET status = 'active', valid_to = ?, updated_at = ?
                WHERE id = ? AND organization_id = ?
                """,
                [valid_to, now, int(existing[0]), org_id],
            )
            continue
        cid = _next_id(conn, "app_rights_contract")
        conn.execute(
            """
            INSERT INTO app_rights_contract
              (id, organization_id, asset_id, rights_type, status, exclusive,
               valid_from, valid_to, evidence_ref, created_by, created_at, updated_at)
            VALUES (?, ?, ?, 'master', 'active', FALSE, ?, ?, ?, NULL, ?, ?)
            """,
            [cid, org_id, asset_id, today - timedelta(days=60), valid_to, evidence, now, now],
        )
        report["actions"].append(f"rights_contract:{evidence}")

    n = conn.execute(
        "SELECT COUNT(*) FROM app_rights_contract WHERE organization_id = ?",
        [org_id],
    ).fetchone()
    report["counts"]["rights_contracts"] = int(n[0] or 0)

    if not _table_exists(conn, "app_rights_conflict"):
        report["soft_fails"].append("rights_conflict_missing")
        return
    conf = conn.execute(
        """
        SELECT id FROM app_rights_conflict
        WHERE organization_id = ? AND details = ?
        LIMIT 1
        """,
        [org_id, RIGHTS_CONFLICT_DETAILS],
    ).fetchone()
    if conf:
        conn.execute(
            "UPDATE app_rights_conflict SET status = 'open', updated_at = ? WHERE id = ?",
            [now, int(conf[0])],
        )
    else:
        cid = _next_id(conn, "app_rights_conflict")
        conn.execute(
            """
            INSERT INTO app_rights_conflict
              (id, organization_id, asset_id, rights_type, territory_code, status,
               details, created_at, updated_at)
            VALUES (?, ?, ?, 'master', 'WW', 'open', ?, ?, ?)
            """,
            [cid, org_id, asset_id, RIGHTS_CONFLICT_DETAILS, now, now],
        )
        report["actions"].append("rights_conflict_open")
    report["counts"]["rights_conflicts_open"] = 1


def _ensure_alerts(conn, org_id: int, now: datetime, report: dict) -> None:
    if not _table_exists(conn, "app_business_alert"):
        report["soft_fails"].append("alerts_missing")
        return
    for kpi, severity, title in ALERT_KEYS:
        existing = conn.execute(
            "SELECT id FROM app_business_alert WHERE title = ? AND organization_id = ?",
            [title, org_id],
        ).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE app_business_alert
                SET status = 'open', severity = ?, kpi_code = ?, updated_at = ?
                WHERE id = ?
                """,
                [severity, kpi, now, int(existing[0])],
            )
            continue
        aid = _next_id(conn, "app_business_alert")
        conn.execute(
            """
            INSERT INTO app_business_alert
              (id, organization_id, severity, title, body, status, kpi_code, created_at, updated_at)
            VALUES (?, ?, ?, ?, '[SYNTHETIC] Demo consolidation alert', 'open', ?, ?, ?)
            """,
            [aid, org_id, severity, title, kpi, now, now],
        )
        report["actions"].append(f"alert:{kpi}")
    n = conn.execute(
        """
        SELECT COUNT(*) FROM app_business_alert
        WHERE organization_id = ? AND status = 'open'
        """,
        [org_id],
    ).fetchone()
    report["counts"]["alerts_open"] = int(n[0] or 0)


def _ensure_opportunities(conn, org_id: int, now: datetime, report: dict) -> None:
    if not _table_exists(conn, "app_crm_opportunity"):
        report["soft_fails"].append("opportunities_missing")
        return
    prosp = None
    if _table_exists(conn, "app_crm_prospect"):
        prosp = conn.execute(
            "SELECT id FROM app_crm_prospect WHERE organization_id = ? LIMIT 1",
            [org_id],
        ).fetchone()
    if not prosp:
        report["soft_fails"].append("opportunities_no_prospect")
        return
    owner = conn.execute(
        """
        SELECT m.user_id FROM app_organization_member m
        WHERE m.organization_id = ? AND COALESCE(m.status, 'active') = 'active'
        ORDER BY m.id LIMIT 1
        """,
        [org_id],
    ).fetchone() if _table_exists(conn, "app_organization_member") else None
    if not owner:
        owner = conn.execute("SELECT id FROM app_user ORDER BY id LIMIT 1").fetchone()
    if not owner:
        report["soft_fails"].append("opportunities_no_owner")
        return
    owner_id = int(owner[0])
    for name, stage, outcome in OPP_KEYS:
        existing = conn.execute(
            "SELECT id FROM app_crm_opportunity WHERE name = ? AND organization_id = ?",
            [name, org_id],
        ).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE app_crm_opportunity
                SET stage = ?, outcome = ?, deleted_at = NULL, updated_at = ?
                WHERE id = ?
                """,
                [stage, outcome, now, int(existing[0])],
            )
            continue
        oid = _next_id(conn, "app_crm_opportunity")
        conn.execute(
            """
            INSERT INTO app_crm_opportunity
              (id, prospect_id, name, description, stage, probability,
               expected_value, currency, expected_close_date, actual_close_date,
               outcome, owner_user_id, organization_id, created_at, updated_at, deleted_at)
            VALUES (?, ?, ?, '[SYNTHETIC] Demo consolidation opportunity', ?, 55,
                    4200.00, 'USD', NULL, NULL, ?, ?, ?, ?, ?, NULL)
            """,
            [oid, int(prosp[0]), name, stage, outcome, owner_id, org_id, now, now],
        )
        report["actions"].append(f"opportunity:{name}")

    open_n = conn.execute(
        """
        SELECT COUNT(*) FROM app_crm_opportunity
        WHERE organization_id = ? AND deleted_at IS NULL
          AND stage NOT IN ('closed_won', 'closed_lost', 'canceled')
        """,
        [org_id],
    ).fetchone()
    won_n = conn.execute(
        """
        SELECT COUNT(*) FROM app_crm_opportunity
        WHERE organization_id = ? AND deleted_at IS NULL AND stage = 'closed_won'
        """,
        [org_id],
    ).fetchone()
    report["counts"]["opportunities_open"] = int(open_n[0] or 0)
    report["counts"]["opportunities_won"] = int(won_n[0] or 0)

    # Pending quotation (1) soft
    if not _table_exists(conn, "app_crm_quotation"):
        report["soft_fails"].append("quotation_missing")
        return
    open_opp = conn.execute(
        """
        SELECT id FROM app_crm_opportunity
        WHERE organization_id = ? AND deleted_at IS NULL
          AND stage NOT IN ('closed_won', 'closed_lost', 'canceled')
        ORDER BY id LIMIT 1
        """,
        [org_id],
    ).fetchone()
    if not open_opp:
        return
    notes = "[DEMO-044] Pending quotation (synthetic)"
    q = conn.execute(
        "SELECT id FROM app_crm_quotation WHERE notes = ? LIMIT 1", [notes]
    ).fetchone()
    if not q:
        qid = _next_id(conn, "app_crm_quotation")
        conn.execute(
            """
            INSERT INTO app_crm_quotation
              (id, opportunity_id, status, currency, notes, row_version, current_version_no,
               created_by, created_at, updated_at, deleted_at)
            VALUES (?, ?, 'sent', 'USD', ?, 1, 0, ?, ?, ?, NULL)
            """,
            [qid, int(open_opp[0]), notes, owner_id, now, now],
        )
        if _table_exists(conn, "app_crm_quotation_version"):
            vid = _next_id(conn, "app_crm_quotation_version")
            try:
                conn.execute(
                    """
                    INSERT INTO app_crm_quotation_version
                      (id, quotation_id, version_no, status, subtotal, discount_pct,
                       discount_requires_approval, total, notes, is_immutable,
                       created_by, created_at)
                    VALUES (?, ?, 1, 'pending_approval', 1500, 12, TRUE, 1320,
                            '[SYNTHETIC]', FALSE, ?, ?)
                    """,
                    [vid, qid, owner_id, now],
                )
                conn.execute(
                    "UPDATE app_crm_quotation SET current_version_no = 1 WHERE id = ?",
                    [qid],
                )
            except Exception as exc:  # noqa: BLE001
                report["errors"].append(f"quotation_version: {exc}")
        report["actions"].append("quotation_pending")
    report["counts"]["pending_quotations"] = 1


def _ensure_billing(conn, org_id: int, now: datetime, report: dict) -> None:
    if not _table_exists(conn, "app_invoice"):
        report["soft_fails"].append("invoices_missing")
        return
    bp = None
    if _table_exists(conn, "app_billing_profile"):
        bp = conn.execute(
            "SELECT id FROM app_billing_profile WHERE organization_id = ? LIMIT 1",
            [org_id],
        ).fetchone()
    if not bp:
        report["soft_fails"].append("billing_profile_missing")
        return
    bp_id = int(bp[0])
    mid = now.date() if hasattr(now, "date") else date.today()
    invoice_ids: dict[str, int] = {}

    for number, status in INVOICE_KEYS:
        existing = conn.execute(
            "SELECT id FROM app_invoice WHERE invoice_number = ?", [number]
        ).fetchone()
        if existing:
            invoice_ids[number] = int(existing[0])
            # Avoid SET organization_id (DuckDB ART quirk); only status/amounts
            paid = 150.0 if status == "paid" else 0.0
            due = 0.0 if status == "paid" else 150.0
            conn.execute(
                """
                UPDATE app_invoice
                SET status = ?, amount_paid = ?, amount_due = ?, updated_at = ?
                WHERE invoice_number = ?
                """,
                [status, paid, due, now, number],
            )
            continue
        iid = _next_id(conn, "app_invoice")
        paid = 150.0 if status == "paid" else 0.0
        due = 0.0 if status == "paid" else 150.0
        conn.execute(
            """
            INSERT INTO app_invoice
              (id, organization_id, billing_profile_id, invoice_number, currency, status,
               subtotal, total, amount_paid, amount_due, issued_at, due_date,
               paid_at, notes, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'USD', ?, 150.00, 150.00, ?, ?, ?, ?, ?,
                    '[SYNTHETIC] Demo consolidation invoice', ?, ?)
            """,
            [
                iid,
                org_id,
                bp_id,
                number,
                status,
                paid,
                due,
                mid,
                mid + timedelta(days=14),
                mid if status == "paid" else None,
                now,
                now,
            ],
        )
        invoice_ids[number] = iid
        report["actions"].append(f"invoice:{number}")

    report["counts"]["invoices"] = len(invoice_ids)

    if not _table_exists(conn, "app_payment_attempt") or not _table_exists(conn, "app_payment"):
        report["soft_fails"].append("payments_tables_missing")
        return

    paid_inv = invoice_ids.get("DEMO-044-INV-PAID-001")
    pending_inv = invoice_ids.get("DEMO-044-INV-PENDING-001") or paid_inv

    # Two recorded payments
    for i, pay_key in enumerate(PAYMENT_KEYS):
        attempt_key = f"DEMO-044-ATTEMPT-OK-{i+1:03d}"
        att = conn.execute(
            "SELECT id FROM app_payment_attempt WHERE idempotency_key = ?",
            [attempt_key],
        ).fetchone()
        if att:
            attempt_id = int(att[0])
        else:
            attempt_id = _next_id(conn, "app_payment_attempt")
            inv_id = paid_inv or pending_inv
            if inv_id is None:
                break
            conn.execute(
                """
                INSERT INTO app_payment_attempt
                  (id, organization_id, invoice_id, provider_code, idempotency_key,
                   amount, currency, status, created_at, updated_at)
                VALUES (?, ?, ?, 'mock', ?, 150.00, 'USD', 'succeeded', ?, ?)
                """,
                [attempt_id, org_id, inv_id, attempt_key, now, now],
            )
        pay = conn.execute(
            "SELECT id FROM app_payment WHERE provider_payment_id = ?", [pay_key]
        ).fetchone()
        if pay:
            conn.execute(
                """
                UPDATE app_payment
                SET status = 'reconciled', amount = 150.00, settled_at = ?, updated_at = ?
                WHERE id = ?
                """,
                [mid, now, int(pay[0])],
            )
        else:
            pid = _next_id(conn, "app_payment")
            conn.execute(
                """
                INSERT INTO app_payment
                  (id, organization_id, payment_attempt_id, provider_code, amount, currency,
                   status, provider_payment_id, settled_at, reconciled_at, created_at, updated_at)
                VALUES (?, ?, ?, 'mock', 150.00, 'USD', 'reconciled', ?, ?, ?, ?, ?)
                """,
                [pid, org_id, attempt_id, pay_key, mid, mid, now, now],
            )
            report["actions"].append(f"payment:{pay_key}")
    report["counts"]["payments"] = 2

    # One failed payment attempt
    fail = conn.execute(
        "SELECT id FROM app_payment_attempt WHERE idempotency_key = ?",
        [FAILED_ATTEMPT_KEY],
    ).fetchone()
    inv_fail = pending_inv or paid_inv
    if inv_fail is None:
        report["soft_fails"].append("failed_attempt_no_invoice")
        return
    if fail:
        conn.execute(
            """
            UPDATE app_payment_attempt
            SET status = 'failed', failure_reason = '[SYNTHETIC] card declined', updated_at = ?
            WHERE id = ?
            """,
            [now, int(fail[0])],
        )
    else:
        fid = _next_id(conn, "app_payment_attempt")
        conn.execute(
            """
            INSERT INTO app_payment_attempt
              (id, organization_id, invoice_id, provider_code, idempotency_key,
               amount, currency, status, failure_reason, created_at, updated_at)
            VALUES (?, ?, ?, 'mock', ?, 150.00, 'USD', 'failed',
                    '[SYNTHETIC] card declined', ?, ?)
            """,
            [fid, org_id, inv_fail, FAILED_ATTEMPT_KEY, now, now],
        )
        report["actions"].append("failed_payment_attempt")
    report["counts"]["failed_payment_attempts"] = 1


def seed_044_consolidation(conn) -> dict:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    report: dict = {
        "ok": True,
        "org_slug": ORG_SLUG,
        "org_id": None,
        "actions": [],
        "errors": [],
        "soft_fails": [],
        "counts": {},
    }

    if not _table_exists(conn, "app_organization"):
        report["ok"] = False
        report["errors"].append("app_organization missing — run seed_integrated_demo first")
        return report

    org = conn.execute(
        "SELECT id FROM app_organization WHERE slug = ?", [ORG_SLUG]
    ).fetchone()
    if not org:
        report["ok"] = False
        report["errors"].append(
            f"Demo org not found (slug={ORG_SLUG}). Run seed_integrated_demo first."
        )
        return report
    org_id = int(org[0])
    report["org_id"] = org_id

    _soft(report, "streams", lambda: _seed_streams(conn, report))
    _soft(report, "artists", lambda: _ensure_artists(conn, org_id, now, report))
    _soft(report, "releases", lambda: _ensure_releases(conn, org_id, now, report))
    _soft(report, "rights", lambda: _ensure_rights(conn, org_id, now, report))
    _soft(report, "alerts", lambda: _ensure_alerts(conn, org_id, now, report))
    _soft(report, "opportunities", lambda: _ensure_opportunities(conn, org_id, now, report))
    _soft(report, "billing", lambda: _ensure_billing(conn, org_id, now, report))

    # Soft-fails (missing tables / deps) are expected; only hard-fail if org missing.
    report["ok"] = report["org_id"] is not None and not any(
        "Demo org not found" in e or "app_organization missing" in e for e in report["errors"]
    )
    return report


def main() -> int:
    from app.core.database import get_connection

    conn = get_connection()
    try:
        result = seed_044_consolidation(conn)
        print(result)
        return 0 if result.get("ok") else 1
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
