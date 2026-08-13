"""VOXMETRIKS final technical release dataset — multi-org enterprise seed.

Deterministic, idempotent, organization-isolated. Does NOT touch the personal
listener account (demo@voxmetrik.io / username demo) nor principal admin/engineer
credentials. Visible names avoid Demo / Test / Fixture / Synthetic / Sample.

Seed string: voxmetriks-final-release-2026

Run (from apps/backend, with API stopped so DuckDB is writable):

    set VOXMETRIKS_SEED_FINAL_RELEASE=1
    python scripts/seed_final_release_dataset.py
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

_BACKEND = Path(__file__).resolve().parent.parent
_ROOT = _BACKEND.parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

SEED = "voxmetriks-final-release-2026"
TAG = "fr-2026"  # internal idempotency prefix (never shown in UI)
STREAM_DAYS = 370  # ~12 months + buffer

# Principal accounts — never mutate credentials / prefs / memberships.
PROTECTED_EMAILS = frozenset({"demo@voxmetrik.io"})
PROTECTED_USERNAMES = frozenset({"demo", "admin", "engineer"})


@dataclass(frozen=True)
class OrgSpec:
    slug: str
    display_name: str
    legal_name: str
    profile: str  # mature | growth | incidents | healthy
    country: str = "EC"


ORGS: tuple[OrgSpec, ...] = (
    OrgSpec("voxmetriks-demo", "VOXMETRIKS Studio", "VOXMETRIKS Studio S.A.", "mature"),
    OrgSpec("aurora-records", "Aurora Records", "Aurora Records S.A.", "growth"),
    OrgSpec("pulse-latam", "Pulse LATAM", "Pulse LATAM SpA", "incidents", "CL"),
    OrgSpec("verde-sonora", "Verde Sonora", "Verde Sonora CIA. LTDA.", "healthy"),
    OrgSpec("costa-pacific", "Costa Pacific Music", "Costa Pacific Music S.A.S.", "medium", "CO"),
)


@dataclass
class Counts:
    organizations: int = 0
    users: int = 0
    memberships: int = 0
    campaigns: int = 0
    opportunities: int = 0
    invoices: int = 0
    payments: int = 0
    subscriptions: int = 0
    personal_subscriptions: int = 0
    releases: int = 0
    rights_contracts: int = 0
    rights_conflicts: int = 0
    support_cases: int = 0
    cs_items: int = 0
    alerts: int = 0
    jobs: int = 0
    job_executions: int = 0
    stream_days: int = 0
    artists: int = 0
    assets: int = 0
    by_org: dict[str, dict[str, int]] = field(default_factory=dict)


def _password() -> str:
    return (
        os.environ.get("RELEASE_DATASET_PASSWORD")
        or os.environ.get("DEMO_ACCOUNT_PASSWORD")
        or os.environ.get("DEMO_PASSWORD")
        or "ReleaseFinal2026!"
    )


def _prng(key: str) -> random.Random:
    digest = hashlib.sha256(f"{SEED}:{key}".encode("utf-8")).hexdigest()
    return random.Random(int(digest[:16], 16))


def _h(key: str) -> int:
    return int(hashlib.sha256(f"{SEED}:{key}".encode()).hexdigest()[:8], 16)


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
    nid = int(conn.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table}").fetchone()[0])
    # DuckDB ART / vacuum quirks can leave MAX behind real keys; probe forward.
    for _ in range(50):
        if not conn.execute(f"SELECT 1 FROM {table} WHERE id = ?", [nid]).fetchone():
            return nid
        nid += 1
    return nid


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


def _bump(counts: Counts, org_slug: str, key: str, n: int = 1) -> None:
    bucket = counts.by_org.setdefault(org_slug, {})
    bucket[key] = int(bucket.get(key, 0) or 0) + n
    if hasattr(counts, key):
        setattr(counts, key, int(getattr(counts, key) or 0) + n)


def _ensure_schemas(conn) -> None:
    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.packages.organizations.infrastructure.schema import ensure_organization_tables
    from app.packages.platform_rbac.infrastructure.schema import ensure_platform_rbac_tables

    ensure_user_tables(conn)
    ensure_organization_tables(conn)
    ensure_platform_rbac_tables(conn)

    optional = [
        ("app.packages.billing.infrastructure.schema", "ensure_billing_tables"),
        ("app.packages.subscriptions.infrastructure.schema", "ensure_subscription_tables"),
        ("app.packages.crm.infrastructure.schema", "ensure_crm_tables"),
        ("app.packages.campaigns.infrastructure.schema", "ensure_campaign_tables"),
        ("app.packages.artists.infrastructure.schema", "ensure_artist_tables"),
        ("app.packages.catalog_publishing.infrastructure.schema", "ensure_catalog_publishing_tables"),
        ("app.packages.catalog_rights.infrastructure.schema", "ensure_catalog_rights_tables"),
        ("app.packages.customer_success.infrastructure.schema", "ensure_customer_success_tables"),
        ("app.packages.business_analytics.infrastructure.schema", "ensure_business_analytics_tables"),
        ("app.packages.platform_ops.infrastructure.schema", "ensure_platform_ops_tables"),
        (
            "app.packages.personal_subscriptions.infrastructure.schema",
            "ensure_personal_subscription_tables",
        ),
    ]
    import importlib

    for mod_name, fn_name in optional:
        try:
            mod = importlib.import_module(mod_name)
            fn = getattr(mod, fn_name, None)
            if callable(fn):
                fn(conn)
        except Exception:
            continue


def _is_protected_user(username: str, email: str) -> bool:
    return email.lower() in PROTECTED_EMAILS or username.lower() in PROTECTED_USERNAMES


def _ensure_user(conn, username: str, email: str, display_role: str = "user") -> int | None:
    """Create/update synthetic user. Never mutates protected personal listener."""
    from app.core.time_util import utc_now
    from app.packages.identity.services.password_security import hash_password

    row = conn.execute(
        "SELECT id, email, username FROM app_user WHERE LOWER(email) = ? OR LOWER(username) = ?",
        [email.lower(), username.lower()],
    ).fetchone()
    if _is_protected_user(username, email):
        return int(row[0]) if row else None
    now = utc_now()
    prefs = json.dumps(
        {
            "seed": SEED,
            "synthetic": True,
            "dark_mode": False,
            "language": "es",
            "recommendations_enabled": True,
        }
    )
    pwd_hash = hash_password(_password())
    if row:
        uid = int(row[0])
        # Do not rewrite if this id somehow is the protected account
        existing_email = str(row[1] or "").lower()
        existing_user = str(row[2] or "").lower()
        if existing_email in PROTECTED_EMAILS or existing_user in PROTECTED_USERNAMES:
            return None
        conn.execute(
            """
            UPDATE app_user
            SET password_hash = ?,
                preferences_json = ?,
                email_verified = TRUE,
                auth_provider = 'local'
            WHERE id = ?
            """,
            [pwd_hash, prefs, uid],
        )
        return uid

    uid = _next_id(conn, "app_user")
    conn.execute(
        """
        INSERT INTO app_user
            (id, username, email, password_hash, role, plan, favorite_genre,
             created_at, preferences_json, email_verified, auth_provider)
        VALUES (?, ?, ?, ?, ?, 'Free', NULL, ?, ?, TRUE, 'local')
        """,
        [uid, username, email, pwd_hash, display_role, now, prefs],
    )
    return uid


def _ensure_member(conn, org_id: int, user_id: int, role_codes: list[str], actor_id: int) -> None:
    from app.core.time_util import utc_now

    now = utc_now()
    member = conn.execute(
        "SELECT id FROM app_organization_member WHERE organization_id = ? AND user_id = ?",
        [org_id, user_id],
    ).fetchone()
    if member:
        member_id = int(member[0])
        conn.execute(
            "UPDATE app_organization_member SET status = 'active', updated_at = ? WHERE id = ?",
            [now, member_id],
        )
    else:
        member_id = _next_id(conn, "app_organization_member")
        conn.execute(
            """
            INSERT INTO app_organization_member
                (id, organization_id, user_id, status, created_by, created_at, updated_at)
            VALUES (?, ?, ?, 'active', ?, ?, ?)
            """,
            [member_id, org_id, user_id, actor_id, now, now],
        )

    if not (_table_exists(conn, "app_business_role") and _table_exists(conn, "app_member_role")):
        return
    for code in role_codes:
        role = conn.execute("SELECT id FROM app_business_role WHERE code = ?", [code]).fetchone()
        if not role:
            continue
        role_id = int(role[0])
        exists = conn.execute(
            "SELECT 1 FROM app_member_role WHERE member_id = ? AND role_id = ? AND status = 'active'",
            [member_id, role_id],
        ).fetchone()
        if exists:
            continue
        mrid = _next_id(conn, "app_member_role")
        conn.execute(
            """
            INSERT INTO app_member_role
                (id, member_id, role_id, status, assigned_by, assigned_at)
            VALUES (?, ?, ?, 'active', ?, ?)
            """,
            [mrid, member_id, role_id, actor_id, now],
        )


def _ensure_org(conn, spec: OrgSpec, created_by: int, now: datetime) -> int:
    row = conn.execute(
        "SELECT id FROM app_organization WHERE slug = ?", [spec.slug]
    ).fetchone()
    if row:
        oid = int(row[0])
        sets = ["display_name = ?", "legal_name = ?", "status = 'active'", "updated_at = ?"]
        params: list[Any] = [spec.display_name, spec.legal_name, now]
        if _has_column(conn, "app_organization", "is_demo"):
            sets.append("is_demo = FALSE" if spec.slug != "voxmetriks-demo" else "is_demo = TRUE")
        if _has_column(conn, "app_organization", "is_test"):
            sets.append("is_test = FALSE")
        conn.execute(
            f"UPDATE app_organization SET {', '.join(sets)} WHERE id = ?",
            [*params, oid],
        )
        return oid

    oid = _next_id(conn, "app_organization")
    cols = (
        "id, display_name, legal_name, slug, organization_type, country_code, timezone, "
        "default_currency, status, created_by, created_at, updated_at"
    )
    vals = "?, ?, ?, ?, 'label', ?, 'America/Guayaquil', 'USD', 'active', ?, ?, ?"
    params = [
        oid,
        spec.display_name,
        spec.legal_name,
        spec.slug,
        spec.country,
        created_by,
        now,
        now,
    ]
    if _has_column(conn, "app_organization", "is_demo"):
        cols += ", is_demo"
        vals += ", FALSE"
    if _has_column(conn, "app_organization", "is_test"):
        cols += ", is_test"
        vals += ", FALSE"
    conn.execute(f"INSERT INTO app_organization ({cols}) VALUES ({vals})", params)
    return oid


def _ensure_artist(conn, org_id: int, key: str, display: str, now: datetime, created_by: int) -> int:
    existing = conn.execute(
        """
        SELECT id FROM app_artist_profile
        WHERE organization_id = ? AND (display_name = ? OR normalized_name = ?)
        LIMIT 1
        """,
        [org_id, display, display.lower().replace(" ", "")],
    ).fetchone()
    if existing:
        return int(existing[0])
    aid = _next_id(conn, "app_artist_profile")
    conn.execute(
        """
        INSERT INTO app_artist_profile
            (id, organization_id, display_name, legal_name, normalized_name,
             status, warehouse_artist_id, created_by, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, 'active', NULL, ?, ?, ?)
        """,
        [
            aid,
            org_id,
            display,
            display,
            display.lower().replace(" ", ""),
            created_by,
            now,
            now,
        ],
    )
    if _table_exists(conn, "app_artist_external_identifier"):
        try:
            eid = _next_id(conn, "app_artist_external_identifier")
            conn.execute(
                """
                INSERT INTO app_artist_external_identifier
                    (id, artist_id, system_code, external_value, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [eid, aid, TAG, key, now, now],
            )
        except Exception:
            pass
    return aid


def _ensure_asset(conn, org_id: int, artist_id: int, title: str, key: str, now: datetime, uid: int) -> int:
    if not _table_exists(conn, "app_catalog_asset"):
        return 0
    row = conn.execute(
        "SELECT id FROM app_catalog_asset WHERE organization_id = ? AND title = ? LIMIT 1",
        [org_id, title],
    ).fetchone()
    if row:
        return int(row[0])
    aid = _next_id(conn, "app_catalog_asset")
    conn.execute(
        """
        INSERT INTO app_catalog_asset
            (id, organization_id, title, status, warehouse_track_id, artist_profile_id,
             created_by, created_at, updated_at)
        VALUES (?, ?, ?, 'active', NULL, ?, ?, ?, ?)
        """,
        [aid, org_id, title, artist_id, uid, now, now],
    )
    return aid


def _seed_releases(
    conn,
    org: OrgSpec,
    org_id: int,
    artist_id: int,
    uid: int,
    now: datetime,
    months: list[date],
    counts: Counts,
) -> None:
    if not _table_exists(conn, "app_release_submission"):
        return

    # Varied status mix by profile
    base = [
        ("draft", "Borrador"),
        ("scheduled", "Programado"),
        ("under_review", "En revisión"),
        ("changes_requested", "Cambios solicitados"),
        ("published", "Publicado"),
        ("withdrawn", "Retirado"),
        ("published", "Publicado"),
        ("approved", "Aprobado"),
    ]
    if org.profile == "incidents":
        statuses = base + [("changes_requested", "Cambios solicitados"), ("under_review", "En revisión")]
    elif org.profile == "growth":
        statuses = base + [("published", "Publicado"), ("scheduled", "Programado")]
    elif org.profile == "healthy":
        statuses = [("published", "Publicado")] * 4 + [
            ("scheduled", "Programado"),
            ("draft", "Borrador"),
            ("approved", "Aprobado"),
        ]
    else:
        statuses = base + [("published", "Publicado")] * 3

    for i, (status, label) in enumerate(statuses):
        key = f"{TAG}-rel-{org.slug}-{i:02d}"
        title = f"{org.display_name} — {label} {i + 1}"
        existing = conn.execute(
            "SELECT id FROM app_release_submission WHERE idempotency_key = ?", [key]
        ).fetchone()
        m0 = months[i % len(months)]
        planned = m0 + timedelta(days=7 + (i % 18))
        if planned > date.today():
            planned = date.today() - timedelta(days=3 + i)
        published_at = now if status == "published" else None
        scheduled_at = datetime(planned.year, planned.month, planned.day, 10, 0, 0) if status == "scheduled" else None
        if existing:
            # Idempotent skip — avoid DuckDB ART UPDATE issues on indexed columns.
            _bump(counts, org.slug, "releases")
            continue
        sid = _next_id(conn, "app_release_submission")
        cols = (
            "id, organization_id, artist_profile_id, release_type, title, genre, language, "
            "planned_release_date, status, created_by, idempotency_key, created_at, updated_at"
        )
        vals: list[Any] = [
            sid,
            org_id,
            artist_id,
            "single" if i % 3 else "ep",
            title,
            ["Pop", "Latin", "Indie", "Electronic"][i % 4],
            "es",
            planned,
            status,
            uid,
            key,
            now,
            now,
        ]
        if _has_column(conn, "app_release_submission", "is_demo"):
            cols += ", is_demo"
            vals.append(False)
        if _has_column(conn, "app_release_submission", "published_at") and published_at:
            cols += ", published_at"
            vals.append(published_at)
        if _has_column(conn, "app_release_submission", "scheduled_at") and scheduled_at:
            cols += ", scheduled_at"
            vals.append(scheduled_at)
        ph = ", ".join(["?"] * len(vals))
        conn.execute(f"INSERT INTO app_release_submission ({cols}) VALUES ({ph})", vals)

        if _table_exists(conn, "app_release_submission_track"):
            tid = _next_id(conn, "app_release_submission_track")
            conn.execute(
                """
                INSERT INTO app_release_submission_track
                    (id, submission_id, title, track_number, disc_number, primary_artist_id,
                     duration_ms, validation_status, sort_order, created_at, updated_at)
                VALUES (?, ?, ?, 1, 1, ?, 210000, 'ok', 0, ?, ?)
                """,
                [tid, sid, f"{title} — Track 1", artist_id, now, now],
            )
        _bump(counts, org.slug, "releases")


def _seed_campaigns(
    conn, org: OrgSpec, org_id: int, artist_id: int, uid: int, now: datetime, counts: Counts
) -> None:
    if not _table_exists(conn, "app_campaign"):
        return
    defs = [
        (f"Lanzamiento {org.display_name} Q1", "active", 3200.0, 2100.0, "streams", 98000.0),
        (f"Playlist push {org.display_name}", "completed", 1800.0, 1650.0, "playlist_adds", 410.0),
        (f"Retarget {org.display_name}", "paused", 900.0, 220.0, "clicks", 5400.0),
    ]
    if org.profile == "growth":
        defs.append((f"Expansión {org.display_name}", "active", 4500.0, 1900.0, "streams", 142000.0))
    if org.profile == "healthy":
        defs = defs[:2]
    if org.profile == "medium":
        defs = defs[:3]

    for name, status, budget, expense, metric, metric_val in defs:
        row = conn.execute(
            "SELECT id FROM app_campaign WHERE name = ? AND organization_id = ?",
            [name, org_id],
        ).fetchone()
        if row:
            cid = int(row[0])
        else:
            cid = _next_id(conn, "app_campaign")
            end_expr = None
            start = date.today() - timedelta(days=40 + (_h(name) % 80))
            end = date.today() - timedelta(days=5) if status == "completed" else None
            conn.execute(
                """
                INSERT INTO app_campaign
                    (id, organization_id, name, status, market, segment,
                     start_date, end_date, artist_profile_id, catalog_release_id,
                     created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'LATAM', ?, ?, ?, ?, NULL, ?, ?, ?)
                """,
                [cid, org_id, name, status, TAG, start, end, artist_id, uid, now, now],
            )
        _bump(counts, org.slug, "campaigns")

        if _table_exists(conn, "app_campaign_budget"):
            if not conn.execute(
                "SELECT 1 FROM app_campaign_budget WHERE campaign_id = ?", [cid]
            ).fetchone():
                bid = _next_id(conn, "app_campaign_budget")
                conn.execute(
                    """
                    INSERT INTO app_campaign_budget
                        (id, campaign_id, organization_id, amount, currency, created_at, updated_at)
                    VALUES (?, ?, ?, ?, 'USD', ?, ?)
                    """,
                    [bid, cid, org_id, budget, now, now],
                )
        if _table_exists(conn, "app_campaign_expense"):
            cat = f"{TAG}_ads_{status}"
            if not conn.execute(
                "SELECT 1 FROM app_campaign_expense WHERE campaign_id = ? AND category = ?",
                [cid, cat],
            ).fetchone():
                eid = _next_id(conn, "app_campaign_expense")
                conn.execute(
                    """
                    INSERT INTO app_campaign_expense
                        (id, campaign_id, organization_id, amount, currency, category,
                         description, expense_date, recorded_by, created_at, updated_at)
                    VALUES (?, ?, ?, ?, 'USD', ?, ?, CURRENT_DATE, ?, ?, ?)
                    """,
                    [eid, cid, org_id, expense, cat, f"Spend {name}", uid, now, now],
                )
        if _table_exists(conn, "app_campaign_result"):
            if not conn.execute(
                "SELECT 1 FROM app_campaign_result WHERE campaign_id = ? AND metric_code = ?",
                [cid, metric],
            ).fetchone():
                rid = _next_id(conn, "app_campaign_result")
                conn.execute(
                    """
                    INSERT INTO app_campaign_result
                        (id, campaign_id, organization_id, metric_code, value, unit,
                         is_monetary, period_start, period_end, source_label,
                         recorded_at, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, 'count', FALSE,
                            CURRENT_DATE - INTERVAL 30 DAY, CURRENT_DATE, ?, ?, ?, ?)
                    """,
                    [rid, cid, org_id, metric, metric_val, TAG, now, now, now],
                )
        if _table_exists(conn, "app_campaign_roi_snapshot") and expense > 0:
            roi = round((metric_val / max(expense, 1.0)) * 0.01, 4)
            if not conn.execute(
                "SELECT 1 FROM app_campaign_roi_snapshot WHERE campaign_id = ?", [cid]
            ).fetchone():
                try:
                    rid = _next_id(conn, "app_campaign_roi_snapshot")
                    conn.execute(
                        """
                        INSERT INTO app_campaign_roi_snapshot
                            (id, campaign_id, organization_id, attribution_definition_id,
                             period_start, period_end, currency, status, roi_value,
                             unavailable_reason, cost_per_result, budget_utilization,
                             goal_attainment, engagement_lift, computed_at, computed_by,
                             created_at)
                        VALUES (?, ?, ?, NULL, CURRENT_DATE - INTERVAL 30 DAY, CURRENT_DATE,
                                'USD', 'available', ?, NULL, ?, ?, ?, NULL, ?, NULL, ?)
                        """,
                        [
                            rid,
                            cid,
                            org_id,
                            roi,
                            round(expense / max(metric_val, 1.0), 4),
                            round(min(expense / max(budget, 1.0), 1.0), 4),
                            round(min(metric_val / 100000.0, 1.2), 4),
                            now,
                            now,
                        ],
                    )
                except Exception:
                    pass


def _seed_crm(
    conn,
    org: OrgSpec,
    org_id: int,
    uid: int,
    now: datetime,
    months: list[date],
    counts: Counts,
) -> None:
    if not _table_exists(conn, "app_crm_prospect"):
        return

    prospect_names = [
        f"Distribuidora {org.display_name} Norte",
        f"Retail {org.display_name} Centro",
        f"Partner {org.display_name} Streaming",
        f"Agencia {org.display_name} Live",
    ]
    prospect_ids: list[int] = []
    for i, pname in enumerate(prospect_names):
        row = conn.execute(
            "SELECT id FROM app_crm_prospect WHERE display_name = ? AND organization_id = ?",
            [pname, org_id],
        ).fetchone()
        if row:
            pid = int(row[0])
        else:
            pid = _next_id(conn, "app_crm_prospect")
            conn.execute(
                """
                INSERT INTO app_crm_prospect
                    (id, display_name, company_name, email, phone, source, status,
                     owner_user_id, organization_id, notes, created_at, updated_at, deleted_at)
                VALUES (?, ?, ?, ?, NULL, ?, 'qualified', ?, ?, ?, ?, ?, NULL)
                """,
                [
                    pid,
                    pname,
                    pname,
                    f"contact+{org.slug}+{i}@{TAG}.local",
                    TAG,
                    uid,
                    org_id,
                    f"internal:{SEED}",
                    now,
                    now,
                ],
            )
        prospect_ids.append(pid)

    # Opportunities across months for win-rate series
    stages_cycle = [
        ("qualification", 20, None),
        ("proposal", 45, None),
        ("negotiation", 65, None),
        ("closed_won", 100, "won"),
        ("closed_lost", 0, "lost"),
        ("closed_won", 100, "won"),
        ("proposal", 50, None),
        ("negotiation", 70, None),
        ("closed_won", 100, "won"),
        ("closed_lost", 0, "lost"),
        ("qualification", 25, None),
        ("closed_won", 100, "won"),
    ]
    if org.profile == "growth":
        # more open pipeline
        stages_cycle = stages_cycle[:3] * 2 + stages_cycle[3:]
    if org.profile == "incidents":
        stages_cycle = stages_cycle[:4] + [("closed_lost", 0, "lost")] * 2 + stages_cycle[4:]

    for i, m0 in enumerate(months):
        stage, prob, outcome = stages_cycle[i % len(stages_cycle)]
        name = f"Oportunidad {org.display_name} {m0.strftime('%Y-%m')}"
        prosp = prospect_ids[i % len(prospect_ids)]
        value = 4200 + (_h(f"opp:{org.slug}:{m0}") % 9000) + i * 120
        row = conn.execute(
            "SELECT id FROM app_crm_opportunity WHERE name = ? AND organization_id = ?",
            [name, org_id],
        ).fetchone()
        close_date = m0 + timedelta(days=18) if outcome else None
        if close_date and close_date > date.today():
            close_date = date.today() - timedelta(days=2)
        if row:
            oid = int(row[0])
            conn.execute(
                """
                UPDATE app_crm_opportunity
                SET stage = ?, probability = ?, expected_value = ?, outcome = ?,
                    actual_close_date = ?, updated_at = ?, organization_id = ?
                WHERE id = ?
                """,
                [stage, prob, value, outcome, close_date, now, org_id, oid],
            )
        else:
            oid = _next_id(conn, "app_crm_opportunity")
            conn.execute(
                """
                INSERT INTO app_crm_opportunity
                    (id, prospect_id, name, description, stage, probability,
                     expected_value, currency, expected_close_date, actual_close_date,
                     outcome, owner_user_id, organization_id, created_at, updated_at, deleted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'USD', ?, ?, ?, ?, ?, ?, ?, NULL)
                """,
                [
                    oid,
                    prosp,
                    name,
                    f"internal:{SEED}",
                    stage,
                    prob,
                    value,
                    m0 + timedelta(days=25),
                    close_date,
                    outcome,
                    uid,
                    org_id,
                    datetime(m0.year, m0.month, 4, 12, 0, 0),
                    now,
                ],
            )
        _bump(counts, org.slug, "opportunities")

        # Quotation on wins
        if outcome == "won" and _table_exists(conn, "app_crm_quotation"):
            q = conn.execute(
                "SELECT id FROM app_crm_quotation WHERE opportunity_id = ?", [oid]
            ).fetchone()
            if not q:
                qid = _next_id(conn, "app_crm_quotation")
                conn.execute(
                    """
                    INSERT INTO app_crm_quotation
                        (id, opportunity_id, status, currency, notes, row_version,
                         current_version_no, created_by, created_at, updated_at, deleted_at)
                    VALUES (?, ?, 'accepted', 'USD', ?, 1, 1, ?, ?, ?, NULL)
                    """,
                    [qid, oid, f"internal:{SEED}", uid, now, now],
                )


def _seed_billing_and_subs(
    conn,
    org: OrgSpec,
    org_id: int,
    uid: int,
    now: datetime,
    months: list[date],
    counts: Counts,
) -> None:
    from app.packages.subscriptions.application.commercial_catalog import (
        ensure_commercial_catalog,
        get_active_price_id,
    )
    from app.packages.subscriptions.application.use_cases import ensure_plan_entitlements

    if not _table_exists(conn, "app_billing_profile"):
        return

    bp = conn.execute(
        "SELECT id FROM app_billing_profile WHERE organization_id = ?", [org_id]
    ).fetchone()
    if bp:
        billing_id = int(bp[0])
    else:
        billing_id = _next_id(conn, "app_billing_profile")
        conn.execute(
            """
            INSERT INTO app_billing_profile
                (id, organization_id, default_currency, legal_name, tax_id,
                 billing_address, email, status, created_at, updated_at)
            VALUES (?, ?, 'USD', ?, ?, ?, ?, 'active', ?, ?)
            """,
            [
                billing_id,
                org_id,
                org.legal_name,
                f"RF-{org.slug.upper()[:8]}",
                f"Calle Musical 10, {org.country}",
                f"billing@{org.slug}.studio.local",
                now,
                now,
            ],
        )

    plan_id = None
    price_id = None
    if _table_exists(conn, "app_plan"):
        ensure_commercial_catalog(conn)
        prow = conn.execute(
            "SELECT id FROM app_plan WHERE code = 'professional' AND status = 'active' LIMIT 1"
        ).fetchone()
        if prow:
            plan_id = int(prow[0])
            price_id = get_active_price_id(
                conn, plan_code="professional", billing_period="monthly", currency="USD"
            )

    sub_id = None
    if plan_id and _table_exists(conn, "app_subscription"):
        status = "active"
        if org.profile == "incidents":
            status = "past_due"
        elif org.profile == "growth":
            status = "active"
        srow = conn.execute(
            "SELECT id FROM app_subscription WHERE organization_id = ? AND plan_id = ?",
            [org_id, plan_id],
        ).fetchone()
        if srow:
            sub_id = int(srow[0])
            conn.execute(
                "UPDATE app_subscription SET status = ?, updated_at = ? WHERE id = ?",
                [status, now, sub_id],
            )
        else:
            sub_id = _next_id(conn, "app_subscription")
            start = months[0]
            end = months[-1] + timedelta(days=27)
            if end > date.today():
                end = date.today() + timedelta(days=14)
            conn.execute(
                """
                INSERT INTO app_subscription
                    (id, organization_id, plan_id, plan_price_id, status, billing_currency,
                     trial_ends_at, current_period_start, current_period_end,
                     cancel_at_period_end, canceled_at, activation_source, access_state,
                     created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 'USD', NULL, ?, ?, FALSE, NULL, ?, 'full', ?, ?)
                """,
                [
                    sub_id,
                    org_id,
                    plan_id,
                    price_id,
                    status,
                    start,
                    end,
                    TAG,
                    datetime(start.year, start.month, 2, 9, 0, 0),
                    now,
                ],
            )
            try:
                ensure_plan_entitlements(conn, sub_id)
            except Exception:
                pass
        _bump(counts, org.slug, "subscriptions")

        # Historical subscription changes for growth series
        if _table_exists(conn, "app_subscription_change"):
            for i, m0 in enumerate(months[::2]):
                key_note = f"{TAG}-subchg-{org.slug}-{m0}"
                exists = conn.execute(
                    """
                    SELECT 1 FROM app_subscription_change
                    WHERE subscription_id = ? AND reason = ?
                    """,
                    [sub_id, key_note],
                ).fetchone()
                if exists:
                    continue
                cid = _next_id(conn, "app_subscription_change")
                conn.execute(
                    """
                    INSERT INTO app_subscription_change
                        (id, subscription_id, change_type, from_plan_id, to_plan_id,
                         from_price_id, to_price_id, scheduled_for, applied_at, status,
                         actor_user_id, reason, created_at, updated_at)
                    VALUES (?, ?, 'renew', ?, ?, ?, ?, ?, ?, 'applied', ?, ?, ?, ?)
                    """,
                    [
                        cid,
                        sub_id,
                        plan_id,
                        plan_id,
                        price_id,
                        price_id,
                        m0,
                        datetime(m0.year, m0.month, 3, 8, 0, 0),
                        uid,
                        key_note,
                        datetime(m0.year, m0.month, 3, 8, 0, 0),
                        now,
                    ],
                )

    if not _table_exists(conn, "app_invoice"):
        return

    for i, m0 in enumerate(months):
        inv_no = f"RF-{org.slug.upper()[:6]}-{m0.strftime('%Y%m')}"
        amount = 99.0 + (i % 5) * 25.0 + (_h(f"inv:{org.slug}:{m0}") % 40)
        # Status mix
        if org.profile == "incidents" and i == len(months) - 1:
            status = "past_due"
            paid = 0.0
            due = amount
            paid_at = None
        elif org.profile == "incidents" and i == len(months) - 2:
            status = "issued"
            paid = 0.0
            due = amount
            paid_at = None
        elif i % 7 == 0 and org.profile != "healthy":
            status = "issued"
            paid = 0.0
            due = amount
            paid_at = None
        else:
            status = "paid"
            paid = amount
            due = 0.0
            paid_at = datetime(m0.year, m0.month, min(12 + (i % 10), 28), 14, 0, 0)

        due_date = m0 + timedelta(days=14)
        if due_date > date.today() and status == "past_due":
            due_date = date.today() - timedelta(days=10)

        existing = conn.execute(
            "SELECT id FROM app_invoice WHERE invoice_number = ?", [inv_no]
        ).fetchone()
        if existing:
            iid = int(existing[0])
            # Avoid updating organization_id (DuckDB ART index limitation).
            conn.execute(
                """
                UPDATE app_invoice
                SET status = ?, total = ?, subtotal = ?, amount_paid = ?, amount_due = ?,
                    due_date = ?, paid_at = ?, updated_at = ?, notes = ?
                WHERE id = ?
                """,
                [
                    status,
                    amount,
                    amount,
                    paid,
                    due,
                    due_date,
                    paid_at,
                    now,
                    f"internal:{SEED}",
                    iid,
                ],
            )
        else:
            iid = _next_id(conn, "app_invoice")
            conn.execute(
                """
                INSERT INTO app_invoice
                    (id, organization_id, billing_profile_id, subscription_id,
                     invoice_number, currency, status, subtotal, total,
                     amount_paid, amount_due, period_start, period_end, due_date,
                     issued_at, paid_at, voided_at, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 'USD', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?)
                """,
                [
                    iid,
                    org_id,
                    billing_id,
                    sub_id,
                    inv_no,
                    status,
                    amount,
                    amount,
                    paid,
                    due,
                    m0,
                    m0 + timedelta(days=27),
                    due_date,
                    datetime(m0.year, m0.month, 1, 10, 0, 0),
                    paid_at,
                    f"internal:{SEED}",
                    datetime(m0.year, m0.month, 1, 10, 0, 0),
                    now,
                ],
            )
        _bump(counts, org.slug, "invoices")

        if status == "paid" and _table_exists(conn, "app_payment_attempt"):
            ok_key = f"{TAG}-pay-ok-{inv_no}"
            att = conn.execute(
                "SELECT id FROM app_payment_attempt WHERE idempotency_key = ?", [ok_key]
            ).fetchone()
            if att:
                attempt_id = int(att[0])
            else:
                attempt_id = _next_id(conn, "app_payment_attempt")
                conn.execute(
                    """
                    INSERT INTO app_payment_attempt
                        (id, organization_id, invoice_id, payment_method_ref_id, provider_code,
                         idempotency_key, amount, currency, status, provider_attempt_id,
                         failure_reason, created_at, updated_at)
                    VALUES (?, ?, ?, NULL, 'mock', ?, ?, 'USD', 'succeeded', ?, NULL, ?, ?)
                    """,
                    [
                        attempt_id,
                        org_id,
                        iid,
                        ok_key,
                        amount,
                        f"rf-ok-{inv_no}",
                        paid_at or now,
                        now,
                    ],
                )
            if _table_exists(conn, "app_payment"):
                pay = conn.execute(
                    "SELECT id FROM app_payment WHERE payment_attempt_id = ?", [attempt_id]
                ).fetchone()
                if not pay:
                    pay_id = _next_id(conn, "app_payment")
                    conn.execute(
                        """
                        INSERT INTO app_payment
                            (id, organization_id, payment_attempt_id, provider_code, amount, currency,
                             status, provider_payment_id, settled_at, reconciled_at, created_at, updated_at)
                        VALUES (?, ?, ?, 'mock', ?, 'USD', 'reconciled', ?, ?, ?, ?, ?)
                        """,
                        [
                            pay_id,
                            org_id,
                            attempt_id,
                            amount,
                            f"rf-pay-{inv_no}",
                            paid_at or now,
                            paid_at or now,
                            paid_at or now,
                            now,
                        ],
                    )
                    if _table_exists(conn, "app_payment_allocation"):
                        if not conn.execute(
                            "SELECT 1 FROM app_payment_allocation WHERE payment_id = ? AND invoice_id = ?",
                            [pay_id, iid],
                        ).fetchone():
                            alloc = _next_id(conn, "app_payment_allocation")
                            conn.execute(
                                """
                                INSERT INTO app_payment_allocation
                                    (id, payment_id, invoice_id, organization_id, amount, created_at)
                                VALUES (?, ?, ?, ?, ?, ?)
                                """,
                                [alloc, pay_id, iid, org_id, amount, paid_at or now],
                            )
                _bump(counts, org.slug, "payments")

        if status in ("issued", "past_due") and org.profile == "incidents" and i >= len(months) - 2:
            fail_key = f"{TAG}-pay-fail-{inv_no}"
            if _table_exists(conn, "app_payment_attempt") and not conn.execute(
                "SELECT 1 FROM app_payment_attempt WHERE idempotency_key = ?", [fail_key]
            ).fetchone():
                fid = _next_id(conn, "app_payment_attempt")
                conn.execute(
                    """
                    INSERT INTO app_payment_attempt
                        (id, organization_id, invoice_id, payment_method_ref_id, provider_code,
                         idempotency_key, amount, currency, status, provider_attempt_id,
                         failure_reason, created_at, updated_at)
                    VALUES (?, ?, ?, NULL, 'mock', ?, ?, 'USD', 'failed', ?,
                            'card_declined_synthetic', ?, ?)
                    """,
                    [fid, org_id, iid, fail_key, amount, f"rf-fail-{inv_no}", now, now],
                )


def _seed_rights(
    conn, org: OrgSpec, org_id: int, asset_id: int, uid: int, now: datetime, counts: Counts
) -> None:
    if not asset_id or not _table_exists(conn, "app_rights_contract"):
        return
    contracts = [
        ("master", "active", date.today() - timedelta(days=400), date.today() + timedelta(days=400)),
        ("publishing", "active", date.today() - timedelta(days=200), date.today() + timedelta(days=90)),
        ("neighboring", "active", date.today() - timedelta(days=100), date.today() + timedelta(days=30)),
    ]
    if org.profile == "healthy":
        contracts = contracts[:2]
    for i, (rtype, status, vf, vt) in enumerate(contracts):
        evidence = f"{TAG}-rights-{org.slug}-{rtype}-{i}"
        row = conn.execute(
            "SELECT id FROM app_rights_contract WHERE evidence_ref = ?", [evidence]
        ).fetchone()
        if row:
            cid = int(row[0])
        else:
            cid = _next_id(conn, "app_rights_contract")
            conn.execute(
                """
                INSERT INTO app_rights_contract
                    (id, organization_id, asset_id, rights_type, status, exclusive,
                     valid_from, valid_to, evidence_ref, created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, FALSE, ?, ?, ?, ?, ?, ?)
                """,
                [cid, org_id, asset_id, rtype, status, vf, vt, evidence, uid, now, now],
            )
        _bump(counts, org.slug, "rights_contracts")

    if org.profile == "incidents" and _table_exists(conn, "app_rights_conflict"):
        details = f"{TAG}-conflict-{org.slug}"
        if not conn.execute(
            "SELECT 1 FROM app_rights_conflict WHERE organization_id = ? AND details = ?",
            [org_id, details],
        ).fetchone():
            cfid = _next_id(conn, "app_rights_conflict")
            conn.execute(
                """
                INSERT INTO app_rights_conflict
                    (id, organization_id, asset_id, rights_type, territory_code, status,
                     details, resolved_by, resolved_at, created_at, updated_at)
                VALUES (?, ?, ?, 'master', 'EC', 'open', ?, NULL, NULL, ?, ?)
                """,
                [cfid, org_id, asset_id, details, now, now],
            )
        _bump(counts, org.slug, "rights_conflicts")


def _seed_support_cs(
    conn, org: OrgSpec, org_id: int, uid: int, now: datetime, counts: Counts
) -> None:
    if _table_exists(conn, "app_customer_onboarding"):
        ob = conn.execute(
            "SELECT id FROM app_customer_onboarding WHERE organization_id = ?", [org_id]
        ).fetchone()
        status = "completed" if org.profile in ("mature", "healthy") else "in_progress"
        if org.profile == "incidents":
            status = "blocked"
        if not ob:
            oid = _next_id(conn, "app_customer_onboarding")
            conn.execute(
                """
                INSERT INTO app_customer_onboarding
                    (id, organization_id, status, started_at, completed_at, created_by,
                     created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    oid,
                    org_id,
                    status,
                    now - timedelta(days=60),
                    now if status == "completed" else None,
                    uid,
                    now,
                    now,
                ],
            )
        _bump(counts, org.slug, "cs_items")

    if _table_exists(conn, "app_customer_risk") and org.profile in ("incidents", "growth"):
        title = f"Riesgo retención — {org.display_name}"
        if not conn.execute(
            "SELECT 1 FROM app_customer_risk WHERE organization_id = ? AND title = ?",
            [org_id, title],
        ).fetchone():
            rid = _next_id(conn, "app_customer_risk")
            conn.execute(
                """
                INSERT INTO app_customer_risk
                    (id, organization_id, title, severity, status, description, created_by,
                     created_at, updated_at)
                VALUES (?, ?, ?, ?, 'open', ?, ?, ?, ?)
                """,
                [
                    rid,
                    org_id,
                    title,
                    "high" if org.profile == "incidents" else "medium",
                    f"internal:{SEED}",
                    uid,
                    now,
                    now,
                ],
            )
        _bump(counts, org.slug, "cs_items")

    if _table_exists(conn, "app_renewal_readiness"):
        state = {
            "mature": "ready",
            "growth": "needs_attention",
            "incidents": "at_risk",
            "healthy": "ready",
        }.get(org.profile, "ready")
        # schema uses readiness_state freeform-ish
        if not conn.execute(
            "SELECT 1 FROM app_renewal_readiness WHERE organization_id = ?", [org_id]
        ).fetchone():
            try:
                rid = _next_id(conn, "app_renewal_readiness")
                conn.execute(
                    """
                    INSERT INTO app_renewal_readiness
                        (id, organization_id, readiness_state, score, notes, evaluated_at, evaluated_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        rid,
                        org_id,
                        state,
                        0.82 if state == "ready" else 0.41,
                        f"internal:{SEED}",
                        now,
                        uid,
                    ],
                )
                _bump(counts, org.slug, "cs_items")
            except Exception:
                pass

    if _table_exists(conn, "app_support_case"):
        cases = []
        if org.profile == "incidents":
            cases = [
                (f"Facturación — {org.display_name}", "billing", "high", "open"),
                (f"Metadata release — {org.display_name}", "catalog", "normal", "resolved"),
            ]
        elif org.profile == "growth":
            cases = [(f"Onboarding seats — {org.display_name}", "general", "normal", "closed")]
        elif org.profile == "mature":
            cases = [(f"Consulta reporte — {org.display_name}", "general", "low", "closed")]
        # healthy: no support cases
        for subject, cat, pri, st in cases:
            if conn.execute(
                "SELECT 1 FROM app_support_case WHERE organization_id = ? AND subject = ?",
                [org_id, subject],
            ).fetchone():
                _bump(counts, org.slug, "support_cases")
                continue
            cid = _next_id(conn, "app_support_case")
            conn.execute(
                """
                INSERT INTO app_support_case
                    (id, organization_id, subject, category, priority, status,
                     requester_user_id, assignee_user_id, resolved_at, closed_at,
                     created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    cid,
                    org_id,
                    subject,
                    cat,
                    pri,
                    st,
                    uid,
                    uid,
                    now if st in ("resolved", "closed") else None,
                    now if st == "closed" else None,
                    now,
                    now,
                ],
            )
            _bump(counts, org.slug, "support_cases")


def _seed_alerts(conn, org: OrgSpec, org_id: int, now: datetime, counts: Counts) -> None:
    if not _table_exists(conn, "app_business_alert"):
        return
    alerts: list[tuple[str, str, str]] = []
    if org.profile == "incidents":
        alerts = [
            ("critical", f"Factura vencida — {org.display_name}", "Pago pendiente fuera de plazo."),
            ("warning", f"Conflicto de derechos — {org.display_name}", "Hay un conflicto abierto."),
            ("warning", f"Release con cambios — {org.display_name}", "Envío editorial requiere ajustes."),
        ]
    elif org.profile == "growth":
        alerts = [
            ("info", f"Pipeline comercial — {org.display_name}", "Oportunidades abiertas en negociación."),
        ]
    elif org.profile == "mature":
        alerts = [
            ("info", f"Renovación próxima — {org.display_name}", "Revisar readiness de renovación."),
        ]
    elif org.profile == "medium":
        alerts = [
            ("warning", f"Seguimiento comercial — {org.display_name}", "Una oportunidad requiere seguimiento."),
        ]
    # healthy: zero alerts

    for sev, title, body in alerts:
        if conn.execute(
            "SELECT 1 FROM app_business_alert WHERE organization_id = ? AND title = ?",
            [org_id, title],
        ).fetchone():
            _bump(counts, org.slug, "alerts")
            continue
        aid = _next_id(conn, "app_business_alert")
        conn.execute(
            """
            INSERT INTO app_business_alert
                (id, organization_id, severity, title, body, status, kpi_code, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'open', NULL, ?, ?)
            """,
            [aid, org_id, sev, title, body, now, now],
        )
        _bump(counts, org.slug, "alerts")


def _seed_jobs(conn, now: datetime, counts: Counts) -> None:
    if not _table_exists(conn, "app_background_job"):
        return
    jobs = [
        (f"{TAG}-etl-daily", "ETL diario warehouse", "active"),
        (f"{TAG}-agg-streams", "Agregación streams", "active"),
        (f"{TAG}-billing-reconcile", "Reconciliación facturación", "active"),
        (f"{TAG}-rights-scan", "Escaneo conflictos derechos", "active"),
    ]
    job_ids: list[int] = []
    for code, name, status in jobs:
        row = conn.execute(
            "SELECT id FROM app_background_job WHERE job_code = ?", [code]
        ).fetchone()
        if row:
            jid = int(row[0])
        else:
            jid = _next_id(conn, "app_background_job")
            conn.execute(
                """
                INSERT INTO app_background_job
                    (id, job_code, display_name, status, max_retries, created_at, updated_at)
                VALUES (?, ?, ?, ?, 3, ?, ?)
                """,
                [jid, code, name, status, now, now],
            )
        job_ids.append(jid)
        counts.jobs += 1

    if not _table_exists(conn, "app_job_execution"):
        return
    # Majority success + a couple failures (historical, not permanent red)
    for i, jid in enumerate(job_ids):
        for attempt in range(1, 4):
            st = "completed"
            err = None
            if i == 3 and attempt == 1:
                st = "failed"
                err = "timeout transitorio"
            elif i == 2 and attempt == 2:
                st = "failed"
                err = "proveedor no disponible"
            marker = f"{TAG}-exec-{jid}-{attempt}"
            if conn.execute(
                "SELECT 1 FROM app_job_execution WHERE result_json = ?", [marker]
            ).fetchone():
                counts.job_executions += 1
                continue
            eid = _next_id(conn, "app_job_execution")
            started = now - timedelta(days=attempt * 3, hours=i)
            finished = started + timedelta(minutes=4 + i)
            conn.execute(
                """
                INSERT INTO app_job_execution
                    (id, job_id, status, attempt_number, result_json, error_message,
                     dead_letter, started_at, finished_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, FALSE, ?, ?, ?)
                """,
                [eid, jid, st, attempt, marker, err, started, finished if st != "running" else None, now],
            )
            counts.job_executions += 1


def _seed_streams(conn, counts: Counts) -> None:
    """Fill missing daily rows only — never overwrite warehouse gold."""
    if not _table_exists(conn, "agg_daily_streams"):
        return
    end_day = date.today()
    start_day = end_day - timedelta(days=STREAM_DAYS - 1)
    has_synthetic = _has_column(conn, "agg_daily_streams", "is_synthetic")
    has_skip = _has_column(conn, "agg_daily_streams", "skip_rate")

    existing_n = int(
        conn.execute(
            "SELECT COUNT(*) FROM agg_daily_streams WHERE fecha BETWEEN ? AND ?",
            [start_day, end_day],
        ).fetchone()[0]
    )
    if existing_n >= 300:
        counts.stream_days = existing_n
        return

    d = start_day
    n = 0
    while d <= end_day:
        exists = conn.execute("SELECT 1 FROM agg_daily_streams WHERE fecha = ?", [d]).fetchone()
        if exists:
            n += 1
            d += timedelta(days=1)
            continue
        day_rng = _prng(f"streams:{d.isoformat()}")
        weekend = 1 if d.weekday() >= 5 else 0
        bucket = day_rng.randrange(10)
        if bucket <= 2:
            base = 4100 + day_rng.randrange(1000)
        elif bucket <= 7:
            base = 5600 + day_rng.randrange(1600)
        else:
            base = 7600 + day_rng.randrange(2400)
        month_boost = 1.0 + 0.08 * ((d.month % 6) - 2.5) / 2.5
        streams = max(0, int((base + weekend * (250 + day_rng.randrange(200))) * month_boost))
        users = max(60, streams // 48)
        tracks = max(30, streams // 95)
        skip_rate = round(0.07 + day_rng.random() * 0.13, 4)
        cols = "fecha, total_streams, unique_users, unique_tracks"
        vals: list[Any] = [d, streams, users, tracks]
        if has_skip:
            cols += ", skip_rate"
            vals.append(skip_rate)
        if has_synthetic:
            cols += ", is_synthetic"
            vals.append(True)
        ph = ", ".join(["?"] * len(vals))
        conn.execute(f"INSERT INTO agg_daily_streams ({cols}) VALUES ({ph})", vals)
        n += 1
        d += timedelta(days=1)
    counts.stream_days = n


def _seed_personal_subs(conn, listener_ids: list[int], now: datetime, counts: Counts) -> None:
    if not listener_ids or not _table_exists(conn, "personal_subscription"):
        return
    if not _table_exists(conn, "personal_plan"):
        return
    plan = conn.execute(
        "SELECT id FROM personal_plan WHERE status = 'active' ORDER BY id LIMIT 1"
    ).fetchone()
    if not plan:
        return
    plan_id = int(plan[0])
    price_id = None
    if _table_exists(conn, "personal_plan_price"):
        pr = conn.execute(
            "SELECT id FROM personal_plan_price WHERE plan_id = ? AND status = 'active' LIMIT 1",
            [plan_id],
        ).fetchone()
        price_id = int(pr[0]) if pr else None

    statuses = ["active", "active", "past_due", "canceled"]
    for i, uid in enumerate(listener_ids):
        if conn.execute(
            "SELECT 1 FROM personal_subscription WHERE user_id = ?", [uid]
        ).fetchone():
            counts.personal_subscriptions += 1
            continue
        st = statuses[i % len(statuses)]
        sid = _next_id(conn, "personal_subscription")
        start = date.today() - timedelta(days=30 * (i + 2))
        end = start + timedelta(days=30)
        conn.execute(
            """
            INSERT INTO personal_subscription
                (id, user_id, plan_id, plan_price_id, household_id, owner_type, status,
                 billing_currency, current_period_start, current_period_end,
                 cancel_at_period_end, canceled_at, grace_until, access_state,
                 created_at, updated_at)
            VALUES (?, ?, ?, ?, NULL, 'user', ?, 'USD', ?, ?, ?, ?, NULL, 'full', ?, ?)
            """,
            [
                sid,
                uid,
                plan_id,
                price_id,
                st,
                start,
                end,
                st == "canceled",
                now if st == "canceled" else None,
                now,
                now,
            ],
        )
        counts.personal_subscriptions += 1


def _rename_canonical_demo_org_display(conn, now: datetime) -> None:
    """If legacy demo org exists, refresh visible display_name only (slug stays)."""
    if not _table_exists(conn, "app_organization"):
        return
    row = conn.execute(
        "SELECT id, display_name FROM app_organization WHERE slug = 'voxmetriks-demo'"
    ).fetchone()
    if not row:
        return
    if str(row[1]).strip().lower() in {"voxmetriks demo", "voxmetriks-demo"}:
        conn.execute(
            "UPDATE app_organization SET display_name = ?, updated_at = ? WHERE id = ?",
            ["VOXMETRIKS Studio", now, int(row[0])],
        )


def _verify_isolation(conn, org_ids: dict[str, int]) -> dict[str, Any]:
    leaks: list[str] = []
    tables = [
        ("app_invoice", "organization_id"),
        ("app_campaign", "organization_id"),
        ("app_crm_opportunity", "organization_id"),
        ("app_rights_contract", "organization_id"),
        ("app_support_case", "organization_id"),
        ("app_business_alert", "organization_id"),
        ("app_release_submission", "organization_id"),
        ("app_subscription", "organization_id"),
    ]
    for slug, oid in org_ids.items():
        for table, col in tables:
            if not _table_exists(conn, table):
                continue
            # rows tagged to this org via our invoice/campaign naming should match org
            if table == "app_invoice":
                bad = conn.execute(
                    f"""
                    SELECT COUNT(*) FROM {table}
                    WHERE invoice_number LIKE ? AND {col} <> ?
                    """,
                    [f"RF-{slug.upper()[:6]}-%", oid],
                ).fetchone()
                if bad and int(bad[0]) > 0:
                    leaks.append(f"invoice_leak:{slug}:{bad[0]}")
            if table == "app_campaign":
                bad = conn.execute(
                    f"""
                    SELECT COUNT(*) FROM {table}
                    WHERE name LIKE ? AND {col} <> ?
                    """,
                    [f"%{slug.replace('-', ' ').title()}%", oid],
                ).fetchone()
                # softer check: campaigns we inserted include display_name
            if table == "app_release_submission":
                bad = conn.execute(
                    f"""
                    SELECT COUNT(*) FROM {table}
                    WHERE idempotency_key LIKE ? AND {col} <> ?
                    """,
                    [f"{TAG}-rel-{slug}-%", oid],
                ).fetchone()
                if bad and int(bad[0]) > 0:
                    leaks.append(f"release_leak:{slug}:{bad[0]}")
    return {"ok": len(leaks) == 0, "leaks": leaks}


def _verify_personal_untouched(conn) -> bool:
    row = conn.execute(
        """
        SELECT id, preferences_json FROM app_user
        WHERE LOWER(email) = 'demo@voxmetrik.io' OR LOWER(username) = 'demo'
        LIMIT 1
        """
    ).fetchone()
    if not row:
        return True
    prefs = str(row[1] or "")
    # Our seed writes "voxmetriks-release-final-2026" into prefs — must NOT be on demo
    if SEED in prefs:
        return False
    # demo must not be member of newly created orgs
    for spec in ORGS:
        if spec.slug == "voxmetriks-demo":
            continue
        org = conn.execute(
            "SELECT id FROM app_organization WHERE slug = ?", [spec.slug]
        ).fetchone()
        if not org:
            continue
        mem = conn.execute(
            """
            SELECT 1 FROM app_organization_member
            WHERE organization_id = ? AND user_id = ?
            """,
            [int(org[0]), int(row[0])],
        ).fetchone()
        if mem:
            return False
    return True


def seed_final_release_dataset() -> dict[str, Any]:
    from app.core.database import using_write_conn
    from app.core.time_util import utc_now

    counts = Counts()
    soft_fails: list[str] = []
    org_ids: dict[str, int] = {}

    with using_write_conn() as conn:
        now = utc_now()
        _ensure_schemas(conn)
        _rename_canonical_demo_org_display(conn, now)

        # Anchor actor (synthetic platform ops) — never the personal demo user
        ops_id = _ensure_user(
            conn, "rf.platform.ops", "rf.platform.ops@voxmetriks.studio.local", "engineer"
        )
        if ops_id is None:
            raise RuntimeError("Failed to create platform ops user")
        counts.users += 1

        try:
            from app.packages.platform_rbac.infrastructure.schema import (
                _assign_platform_role_if_missing,
            )

            _assign_platform_role_if_missing(
                conn, user_id=ops_id, role_code="platform_admin", now=now
            )
        except Exception:
            soft_fails.append("platform_admin_role")

        months = _month_starts(date.today().replace(day=1), 12)

        # Extra listeners for B2C (not demo)
        listener_ids: list[int] = []
        for uname, email in (
            ("rf.listener.marina", "rf.listener.marina@voxmetriks.studio.local"),
            ("rf.listener.diego", "rf.listener.diego@voxmetriks.studio.local"),
            ("rf.listener.sofia", "rf.listener.sofia@voxmetriks.studio.local"),
        ):
            lid = _ensure_user(conn, uname, email, "user")
            if lid:
                listener_ids.append(lid)
                counts.users += 1

        for spec in ORGS:
            if spec.slug == "voxmetriks-demo":
                owner = _ensure_user(conn, "admin", "admin@local.invalid", "admin")
                admin = owner
            else:
                owner = _ensure_user(
                    conn,
                    f"rf.owner.{spec.slug.split('-')[0]}",
                    f"rf.owner.{spec.slug}@voxmetriks.studio.local",
                    "user",
                )
                admin = _ensure_user(
                    conn,
                    f"rf.admin.{spec.slug.split('-')[0]}",
                    f"rf.admin.{spec.slug}@voxmetriks.studio.local",
                    "user",
                )
            finance = _ensure_user(
                conn,
                f"rf.finance.{spec.slug.split('-')[0]}",
                f"rf.finance.{spec.slug}@voxmetriks.studio.local",
                "user",
            )
            analyst = _ensure_user(
                conn,
                f"rf.analyst.{spec.slug.split('-')[0]}",
                f"rf.analyst.{spec.slug}@voxmetriks.studio.local",
                "engineer",
            )
            marketing = _ensure_user(
                conn,
                f"rf.mkt.{spec.slug.split('-')[0]}",
                f"rf.mkt.{spec.slug}@voxmetriks.studio.local",
                "user",
            )
            for u in (owner, admin, finance, analyst, marketing):
                if u:
                    counts.users += 1
            if not owner or not admin:
                soft_fails.append(f"users:{spec.slug}")
                continue

            org_id = _ensure_org(conn, spec, owner, now)
            org_ids[spec.slug] = org_id
            _bump(counts, spec.slug, "organizations")

            _ensure_member(conn, org_id, owner, ["owner"], owner)
            _ensure_member(conn, org_id, admin, ["administrator"], owner)
            if finance:
                _ensure_member(conn, org_id, finance, ["finance", "billing_manager"], owner)
            if analyst:
                _ensure_member(conn, org_id, analyst, ["analyst"], owner)
            if marketing:
                _ensure_member(conn, org_id, marketing, ["marketing_manager"], owner)
            if spec.profile == "incidents":
                support = _ensure_user(
                    conn,
                    f"rf.support.{spec.slug.split('-')[0]}",
                    f"rf.support.{spec.slug}@voxmetriks.studio.local",
                    "user",
                )
                if support:
                    counts.users += 1
                    _ensure_member(
                        conn,
                        org_id,
                        support,
                        ["support_agent", "customer_success_manager"],
                        owner,
                    )
            counts.memberships += 4
            _bump(counts, spec.slug, "memberships", 4)

            # Artists / assets
            artists = []
            if _table_exists(conn, "app_artist_profile"):
                for i, aname in enumerate(
                    (
                        f"Artista {spec.display_name} Uno",
                        f"Artista {spec.display_name} Dos",
                    )
                ):
                    aid = _ensure_artist(
                        conn,
                        org_id,
                        f"{TAG}-artist-{spec.slug}-{i}",
                        aname,
                        now,
                        owner,
                    )
                    artists.append(aid)
                    _bump(counts, spec.slug, "artists")
            primary_artist = artists[0] if artists else 0
            asset_id = 0
            if primary_artist:
                asset_id = _ensure_asset(
                    conn,
                    org_id,
                    primary_artist,
                    f"Master {spec.display_name} 01",
                    f"{TAG}-asset-{spec.slug}",
                    now,
                    owner,
                )
                if asset_id:
                    _bump(counts, spec.slug, "assets")

            try:
                _seed_releases(conn, spec, org_id, primary_artist or 1, owner, now, months, counts)
            except Exception as exc:
                soft_fails.append(f"releases:{spec.slug}:{exc}")
            try:
                _seed_campaigns(conn, spec, org_id, primary_artist or 1, admin, now, counts)
            except Exception as exc:
                soft_fails.append(f"campaigns:{spec.slug}:{exc}")
            try:
                _seed_crm(conn, spec, org_id, admin, now, months, counts)
            except Exception as exc:
                soft_fails.append(f"crm:{spec.slug}:{exc}")
            try:
                _seed_billing_and_subs(conn, spec, org_id, finance or owner, now, months, counts)
            except Exception as exc:
                soft_fails.append(f"billing:{spec.slug}:{exc}")
            try:
                _seed_rights(conn, spec, org_id, asset_id, owner, now, counts)
            except Exception as exc:
                soft_fails.append(f"rights:{spec.slug}:{exc}")
            try:
                _seed_support_cs(conn, spec, org_id, admin, now, counts)
            except Exception as exc:
                soft_fails.append(f"support:{spec.slug}:{exc}")
            try:
                _seed_alerts(conn, spec, org_id, now, counts)
            except Exception as exc:
                soft_fails.append(f"alerts:{spec.slug}:{exc}")

        try:
            _seed_jobs(conn, now, counts)
        except Exception as exc:
            soft_fails.append(f"jobs:{exc}")
        try:
            _seed_streams(conn, counts)
        except Exception as exc:
            soft_fails.append(f"streams:{exc}")
        try:
            _seed_personal_subs(conn, listener_ids, now, counts)
        except Exception as exc:
            soft_fails.append(f"personal_subs:{exc}")

        isolation = _verify_isolation(conn, org_ids)
        personal_ok = _verify_personal_untouched(conn)

        try:
            from app.packages.business_analytics.application.strategic_agg import (
                default_period,
                refresh_strategic_kpi_period,
            )
            from app.packages.business_analytics.infrastructure.schema import (
                ensure_business_analytics_tables,
            )

            ensure_business_analytics_tables(conn)
            p_start, p_end = default_period()
            for oid in org_ids.values():
                refresh_strategic_kpi_period(
                    conn,
                    organization_id=oid,
                    period_start=p_start,
                    period_end=p_end,
                    include_global=False,
                )
            refresh_strategic_kpi_period(
                conn,
                organization_id=None,
                period_start=p_start,
                period_end=p_end,
                include_global=True,
            )
        except Exception as exc:
            soft_fails.append(f"strategic_agg:{exc}")

        # Idempotency spot-check: recount RF releases
        rf_releases = 0
        if _table_exists(conn, "app_release_submission"):
            rf_releases = int(
                conn.execute(
                    "SELECT COUNT(*) FROM app_release_submission WHERE idempotency_key LIKE ?",
                    [f"{TAG}-rel-%"],
                ).fetchone()[0]
            )

        summary = {
            "seed": SEED,
            "seeded": True,
            "organizations": len(org_ids),
            "org_ids": org_ids,
            "counts": {
                "organizations": counts.organizations,
                "users": counts.users,
                "memberships": counts.memberships,
                "campaigns": counts.campaigns,
                "opportunities": counts.opportunities,
                "invoices": counts.invoices,
                "payments": counts.payments,
                "subscriptions": counts.subscriptions,
                "personal_subscriptions": counts.personal_subscriptions,
                "releases": counts.releases,
                "rights_contracts": counts.rights_contracts,
                "rights_conflicts": counts.rights_conflicts,
                "support_cases": counts.support_cases,
                "cs_items": counts.cs_items,
                "alerts": counts.alerts,
                "jobs": counts.jobs,
                "job_executions": counts.job_executions,
                "stream_days": counts.stream_days,
                "artists": counts.artists,
                "assets": counts.assets,
                "rf_releases_in_db": rf_releases,
            },
            "by_org": counts.by_org,
            "isolation": isolation,
            "personal_account_untouched": personal_ok,
            "soft_fails": soft_fails,
            "analytics_months": 12,
        }
        return summary


def main() -> int:
    if os.environ.get("VOXMETRIKS_SEED_FINAL_RELEASE", "").strip() not in {"1", "true", "yes"}:
        print("Set VOXMETRIKS_SEED_FINAL_RELEASE=1 to run this seed.")
        return 2

    print("=" * 64)
    print(" VOXMETRIKS FINAL TECHNICAL RELEASE DATASET")
    print(f" seed={SEED}")
    print("=" * 64)

    try:
        summary = seed_final_release_dataset()
    except Exception as exc:
        print(f"FAILED: {exc}")
        return 1

    print(json.dumps(summary, indent=2, default=str))
    print("DONE")
    return 0 if summary.get("personal_account_untouched") and summary.get("isolation", {}).get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
