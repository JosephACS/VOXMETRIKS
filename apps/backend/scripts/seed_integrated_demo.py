"""Integrated VOXMETRIKS demo accounts — final closure after Spec 029.

Creates the seven local demo identities used for B2C + B2B demonstrations.
Opt-in only. Idempotent. Never prints the password.

Password (hash only stored):
  DEMO_ACCOUNT_PASSWORD  (preferred)
  DEMO_PASSWORD / VOXMETRIKS_DEMO_PASSWORD  (legacy fallback)

Run (from apps/backend):

    set VOXMETRIKS_SEED_DEMO_ACCOUNTS=1
    set DEMO_ACCOUNT_PASSWORD=your-local-secret
    python scripts/seed_integrated_demo.py

Optional cleanup of pytest / Golden Path pollution first:

    python scripts/seed_integrated_demo.py --cleanup-first

Does not touch music warehouse tables (dim_*/fact_*).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

ORG_SLUG = "voxmetriks-demo"
ORG_DISPLAY = "VOXMETRIKS Demo"

# username -> email
DEMO_USERS: tuple[tuple[str, str], ...] = (
    ("listener.free", "listener.free@demo.voxmetriks.local"),
    ("listener.premium", "listener.premium@demo.voxmetriks.local"),
    ("household.owner", "household.owner@demo.voxmetriks.local"),
    ("household.member", "household.member@demo.voxmetriks.local"),
    ("household.member2", "household.member2@demo.voxmetriks.local"),
    ("platform.admin", "platform.admin@demo.voxmetriks.local"),
    ("sales.manager", "sales.manager@demo.voxmetriks.local"),
    ("organization.owner", "organization.owner@demo.voxmetriks.local"),
    ("finance.manager", "finance.manager@demo.voxmetriks.local"),
    # Presentation account — reduced nav in frontend (preferences.presentation_nav)
    ("demo.business", "demo.business@demo.voxmetriks.local"),
    ("demo.artist", "demo.artist@demo.voxmetriks.local"),
)


def _demo_password() -> str:
    return (
        os.environ.get("DEMO_ACCOUNT_PASSWORD")
        or os.environ.get("DEMO_PASSWORD")
        or os.environ.get("VOXMETRIKS_DEMO_PASSWORD")
        or "demo-change-me"
    )


def _table_exists(conn, table: str) -> bool:
    row = conn.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
        [table],
    ).fetchone()
    return bool(row and row[0])


def _has_column(conn, table: str, column: str) -> bool:
    try:
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info('{table}')").fetchall()]
        return column in cols
    except Exception:
        return False


def _next_id(conn, table: str) -> int:
    return int(conn.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table}").fetchone()[0])


def _ensure_user(conn, username: str, email: str) -> int:
    from app.packages.identity.services.password_security import hash_password
    from app.packages.identity.services.user_storage import ensure_user_tables
    from app.core.time_util import utc_now

    ensure_user_tables(conn)
    row = conn.execute(
        "SELECT id FROM app_user WHERE LOWER(email) = ? OR LOWER(username) = ?",
        [email.lower(), username.lower()],
    ).fetchone()
    prefs = json.dumps(
        {
            "demo": True,
            "dark_mode": True,
            "language": "es",
            "recommendations_enabled": True,
            **(
                {"presentation_nav": True, "presentation_role": "business_demo"}
                if username == "demo.business"
                else {}
            ),
            **(
                {
                    "presentation_nav": True,
                    "presentation_role": "artist",
                    "artist_portal": True,
                }
                if username == "demo.artist"
                else {}
            ),
        }
    )
    pwd_hash = hash_password(_demo_password())
    now = utc_now()
    if row:
        uid = int(row[0])
        # Avoid rewriting unique username/email (DuckDB UPDATE quirks on unique idxs).
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
    cols = (
        "id, username, email, password_hash, role, plan, favorite_genre, "
        "created_at, preferences_json, email_verified, auth_provider"
    )
    conn.execute(
        f"""
        INSERT INTO app_user ({cols})
        VALUES (?, ?, ?, ?, 'user', 'Free', NULL, ?, ?, TRUE, 'local')
        """,
        [uid, username, email, pwd_hash, now, prefs],
    )
    return uid


def _assign_platform_role(conn, user_id: int, role_code: str) -> None:
    from app.packages.platform_rbac.infrastructure.schema import (
        _assign_platform_role_if_missing,
        ensure_platform_rbac_tables,
    )
    from app.core.time_util import utc_now

    ensure_platform_rbac_tables(conn)
    _assign_platform_role_if_missing(
        conn, user_id=user_id, role_code=role_code, now=utc_now()
    )


def _ensure_org_member(conn, org_id: int, user_id: int, role_codes: list[str]) -> None:
    from app.core.time_util import utc_now
    from app.packages.organizations.infrastructure.schema import ensure_organization_tables

    ensure_organization_tables(conn)
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
            [member_id, org_id, user_id, user_id, now, now],
        )

    if not (
        _table_exists(conn, "app_business_role") and _table_exists(conn, "app_member_role")
    ):
        return
    for code in role_codes:
        role = conn.execute(
            "SELECT id FROM app_business_role WHERE code = ?", [code]
        ).fetchone()
        if not role:
            continue
        role_id = int(role[0])
        exists = conn.execute(
            """
            SELECT 1 FROM app_member_role
            WHERE member_id = ? AND role_id = ? AND status = 'active'
            """,
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
            [mrid, member_id, role_id, user_id, now],
        )


def _ensure_canonical_org(conn, created_by: int) -> int:
    from app.core.time_util import utc_now
    from app.packages.organizations.infrastructure.schema import ensure_organization_tables

    ensure_organization_tables(conn)
    now = utc_now()
    row = conn.execute(
        "SELECT id FROM app_organization WHERE slug = ?", [ORG_SLUG]
    ).fetchone()
    if row:
        org_id = int(row[0])
        sets = [
            "display_name = ?",
            "status = 'active'",
            "updated_at = ?",
            "timezone = 'America/Guayaquil'",
            "default_currency = 'USD'",
        ]
        params: list[Any] = [ORG_DISPLAY, now]
        if _has_column(conn, "app_organization", "is_demo"):
            sets.append("is_demo = TRUE")
        if _has_column(conn, "app_organization", "is_test"):
            sets.append("is_test = FALSE")
        if _has_column(conn, "app_organization", "country_code"):
            sets.append("country_code = 'EC'")
        conn.execute(
            f"UPDATE app_organization SET {', '.join(sets)} WHERE id = ?",
            [*params, org_id],
        )
        return org_id

    org_id = _next_id(conn, "app_organization")
    cols = (
        "id, display_name, slug, organization_type, country_code, timezone, "
        "default_currency, status, created_by, created_at, updated_at"
    )
    vals = "?, ?, ?, 'label', 'EC', 'America/Guayaquil', 'USD', 'active', ?, ?, ?"
    params = [org_id, ORG_DISPLAY, ORG_SLUG, created_by, now, now]
    if _has_column(conn, "app_organization", "is_demo"):
        cols += ", is_demo"
        vals += ", TRUE"
    if _has_column(conn, "app_organization", "is_test"):
        cols += ", is_test"
        vals += ", FALSE"
    conn.execute(f"INSERT INTO app_organization ({cols}) VALUES ({vals})", params)
    return org_id


def _seed_personal_line(conn, ids: dict[str, int]) -> dict[str, Any]:
    from app.packages.personal_subscriptions.application.use_cases import (
        accept_invitation,
        ensure_free_subscription,
        invite_member,
        simulate_payment,
        start_checkout,
    )
    from app.packages.personal_subscriptions.infrastructure.schema import (
        ensure_personal_subscription_tables,
    )

    ensure_personal_subscription_tables(conn)
    for uname in (
        "listener.free",
        "listener.premium",
        "household.owner",
        "household.member",
        "household.member2",
        "demo.business",
    ):
        if uname in ids:
            ensure_free_subscription(conn, ids[uname])

    # Premium Individual
    for uname in ("listener.premium", "demo.business"):
        if uname not in ids:
            continue
        prem = ids[uname]
        active = conn.execute(
            """
            SELECT s.id FROM personal_subscription s
            JOIN personal_plan p ON p.id = s.plan_id
            WHERE s.user_id = ? AND p.code = 'premium_individual' AND s.status = 'active'
            """,
            [prem],
        ).fetchone()
        if not active:
            checkout = start_checkout(
                conn, prem, plan_code="premium_individual", billing_period="monthly"
            )
            simulate_payment(
                conn, prem, attempt_id=checkout["attempt_id"], scenario="succeeded"
            )

    # Familiar titular + members (Spec closure: household.owner = Familiar)
    owner = ids["household.owner"]
    fam = conn.execute(
        """
        SELECT s.id FROM personal_subscription s
        JOIN personal_plan p ON p.id = s.plan_id
        WHERE s.user_id = ? AND p.code = 'premium_family' AND s.status = 'active'
        """,
        [owner],
    ).fetchone()
    if not fam:
        # If previously seeded as Duo, still allow family checkout path once
        duo = conn.execute(
            """
            SELECT s.id FROM personal_subscription s
            JOIN personal_plan p ON p.id = s.plan_id
            WHERE s.user_id = ? AND p.code IN ('premium_duo', 'premium_family')
              AND s.status IN ('active', 'past_due', 'canceled')
            """,
            [owner],
        ).fetchone()
        if not duo:
            checkout = start_checkout(
                conn, owner, plan_code="premium_family", billing_period="monthly"
            )
            simulate_payment(
                conn, owner, attempt_id=checkout["attempt_id"], scenario="succeeded"
            )
        else:
            # Upgrade via new checkout when only duo exists
            still_family = conn.execute(
                """
                SELECT s.id FROM personal_subscription s
                JOIN personal_plan p ON p.id = s.plan_id
                WHERE s.user_id = ? AND p.code = 'premium_family' AND s.status = 'active'
                """,
                [owner],
            ).fetchone()
            if not still_family:
                checkout = start_checkout(
                    conn, owner, plan_code="premium_family", billing_period="monthly"
                )
                simulate_payment(
                    conn, owner, attempt_id=checkout["attempt_id"], scenario="succeeded"
                )

    email_map = {u: e for u, e in DEMO_USERS}
    for member_key in ("household.member", "household.member2"):
        mid = ids[member_key]
        already = conn.execute(
            """
            SELECT 1 FROM household_member hm
            JOIN household h ON h.id = hm.household_id
            WHERE hm.user_id = ? AND hm.status = 'active' AND h.owner_user_id = ?
            """,
            [mid, owner],
        ).fetchone()
        if not already:
            try:
                inv = invite_member(conn, owner, email_map[member_key])
                accept_invitation(conn, mid, inv["token"])
            except Exception:
                pass

    return {"personal_ok": True}


def _ensure_professional_subscription(conn, org_id: int, actor_id: int) -> None:
    """Attach Professional plan to canonical demo org when missing; always repair entitlements."""
    from app.core.time_util import utc_now
    from app.packages.subscriptions.application.commercial_catalog import ensure_commercial_catalog
    from app.packages.subscriptions.application.use_cases import ensure_plan_entitlements
    from app.packages.subscriptions.infrastructure.schema import ensure_subscription_tables

    ensure_subscription_tables(conn)
    if not _table_exists(conn, "app_plan") or not _table_exists(conn, "app_subscription"):
        return
    try:
        ensure_commercial_catalog(conn)
    except Exception:
        pass
    plan = conn.execute(
        "SELECT id FROM app_plan WHERE code = 'professional' AND status != 'archived' LIMIT 1"
    ).fetchone()
    if not plan:
        return
    plan_id = int(plan[0])
    existing = conn.execute(
        """
        SELECT id FROM app_subscription
        WHERE organization_id = ? AND status IN ('active', 'trialing', 'past_due')
        LIMIT 1
        """,
        [org_id],
    ).fetchone()
    if existing:
        ensure_plan_entitlements(conn, int(existing[0]))
        return
    price = conn.execute(
        """
        SELECT id FROM app_plan_price
        WHERE plan_id = ? AND billing_period = 'monthly' AND status = 'active'
        LIMIT 1
        """,
        [plan_id],
    ).fetchone()
    price_id = int(price[0]) if price else None
    now = utc_now()
    sid = _next_id(conn, "app_subscription")
    cols = "id, organization_id, plan_id, status, created_at, updated_at"
    vals = "?, ?, ?, 'active', ?, ?"
    params: list[Any] = [sid, org_id, plan_id, now, now]
    if price_id is not None and _has_column(conn, "app_subscription", "plan_price_id"):
        cols += ", plan_price_id"
        vals += ", ?"
        params.append(price_id)
    if _has_column(conn, "app_subscription", "billing_currency"):
        cols += ", billing_currency"
        vals += ", ?"
        params.append("USD")
    if _has_column(conn, "app_subscription", "access_state"):
        cols += ", access_state"
        vals += ", ?"
        params.append("full")
    if _has_column(conn, "app_subscription", "created_by"):
        cols += ", created_by"
        vals += ", ?"
        params.append(actor_id)
    try:
        conn.execute(f"INSERT INTO app_subscription ({cols}) VALUES ({vals})", params)
        ensure_plan_entitlements(conn, sid)
    except Exception:
        pass


def _seed_demo_royalties(conn, org_id: int, actor_user_id: int) -> dict[str, Any]:
    """Light demo pool/settlement/payout labeled synthetic — no real money."""
    out: dict[str, Any] = {"demo": True, "seeded": False}
    if not _table_exists(conn, "app_royalty_revenue_pool"):
        return out
    try:
        from datetime import date
        from decimal import Decimal

        from app.packages.royalties.application.use_cases import RoyaltiesUseCases
        from app.packages.royalties.infrastructure.schema import ensure_royalty_tables

        ensure_royalty_tables(conn)
        uc = RoyaltiesUseCases(conn)
        existing = conn.execute(
            "SELECT id FROM app_royalty_revenue_pool WHERE idempotency_key = ?",
            ["demo-royalty-pool-s030"],
        ).fetchone()
        if existing:
            out["pool_id"] = int(existing[0])
            out["seeded"] = True
            out["idempotent"] = True
            return out

        # Minimal rights contract (60/40) if catalog tables exist
        asset_id = 9001
        contract_id = None
        if _table_exists(conn, "app_catalog_asset") and _table_exists(
            conn, "app_rights_contract"
        ):
            from app.core.time_util import utc_now

            now = utc_now()
            arow = conn.execute(
                "SELECT id FROM app_catalog_asset WHERE id = ?", [asset_id]
            ).fetchone()
            if not arow:
                conn.execute(
                    """
                    INSERT INTO app_catalog_asset
                        (id, organization_id, title, status, warehouse_track_id,
                         artist_profile_id, created_by, created_at, updated_at)
                    VALUES (?, ?, 'Demo Royalty Track', 'active', 1, NULL, ?, ?, ?)
                    """,
                    [asset_id, org_id, actor_user_id, now, now],
                )
            crow = conn.execute(
                """
                SELECT id FROM app_rights_contract
                WHERE asset_id = ? AND organization_id = ? LIMIT 1
                """,
                [asset_id, org_id],
            ).fetchone()
            if crow:
                contract_id = int(crow[0])
            else:
                contract_id = _next_id(conn, "app_rights_contract")
                conn.execute(
                    """
                    INSERT INTO app_rights_contract
                        (id, organization_id, asset_id, rights_type, status, exclusive,
                         valid_from, valid_to, evidence_ref, created_by, created_at, updated_at)
                    VALUES (?, ?, ?, 'master', 'active', FALSE, DATE '2020-01-01', NULL,
                            'demo-synthetic', ?, ?, ?)
                    """,
                    [contract_id, org_id, asset_id, actor_user_id, now, now],
                )
                for pname, pct in (("Demo Artist A", 60), ("Demo Label B", 40)):
                    pid = _next_id(conn, "app_rights_contract_party")
                    conn.execute(
                        """
                        INSERT INTO app_rights_contract_party
                            (id, contract_id, party_name, party_type, ownership_percentage,
                             organization_id, artist_profile_id, created_at, updated_at)
                        VALUES (?, ?, ?, 'external', ?, NULL, NULL, ?, ?)
                        """,
                        [pid, contract_id, pname, pct, now, now],
                    )

        pool = uc.create_pool(
            actor_user_id=actor_user_id,
            organization_id=org_id,
            currency="USD",
            period_start=date(2026, 1, 1),
            period_end=date(2026, 1, 31),
            idempotency_key="demo-royalty-pool-s030",
            total_amount=Decimal("100.0000"),
            label="[DEMO] Synthetic royalty pool — not real money",
            is_demo=True,
        )
        uc.add_b2c_source(
            pool_id=pool["id"],
            actor_user_id=actor_user_id,
            amount=Decimal("100.0000"),
            currency="USD",
            reason="demo synthetic B2C candidate",
            evidence_ref="demo-synthetic",
            organization_id=org_id,
            approve=True,
        )
        uc.approve_pool(pool_id=pool["id"], actor_user_id=actor_user_id)
        uc.seed_demo_stream_weights(pool_id=pool["id"], weights={1: 70, 2: 30})
        if contract_id:
            run = uc.calculate_pro_rata_settlement(
                pool_id=pool["id"],
                actor_user_id=actor_user_id,
                idempotency_key="demo-royalty-settle-s030",
                asset_scopes=[
                    {
                        "asset_id": asset_id,
                        "warehouse_track_id": 1,
                        "rights_contract_id": contract_id,
                    },
                    {
                        "asset_id": asset_id,
                        "warehouse_track_id": 2,
                        "rights_contract_id": contract_id,
                    },
                ],
                synthetic_event_counts={1: 70, 2: 30},
            )
            try:
                uc.calculate_contract_splits(
                    settlement_run_id=run["id"], actor_user_id=actor_user_id
                )
                uc.generate_statements(
                    settlement_run_id=run["id"], actor_user_id=actor_user_id
                )
                uc.approve_settlement(
                    settlement_run_id=run["id"], actor_user_id=actor_user_id
                )
                batch = uc.create_payout_batch(
                    settlement_run_id=run["id"],
                    actor_user_id=actor_user_id,
                    idempotency_key="demo-royalty-payout-s030",
                    destination_type="demo_wallet",
                    destination_ref_prefix="demo_wallet",
                )
                uc.simulate_payouts(
                    batch_id=batch["id"], actor_user_id=actor_user_id, scenario="succeed"
                )
                out["settlement_id"] = run["id"]
                out["payout_batch_id"] = batch["id"]
            except Exception as exc:
                out["settlement_note"] = str(exc)
        out["pool_id"] = pool["id"]
        out["seeded"] = True
        out["label"] = "demo/synthetic"
    except Exception as exc:
        out["error"] = str(exc)
    return out


def _seed_demo_catalog_publishing(conn, org_id: int, artist_user_id: int, owner_user_id: int) -> dict[str, Any]:
    """Spec 031 demo submissions — idempotent; no analytics mass-insert; reserved warehouse ids only."""
    out: dict[str, Any] = {"demo": True, "seeded": False}
    try:
        from pathlib import Path

        from app.core.config import get_settings
        from app.core.time_util import utc_now
        from app.packages.artists.infrastructure.schema import ensure_artist_tables
        from app.packages.catalog_publishing.application.use_cases import (
            CatalogPublishingUseCases,
        )
        from app.packages.catalog_publishing.infrastructure.local_media_storage import (
            LocalMediaStorageProvider,
            make_minimal_png,
            make_minimal_wav,
        )
        from app.packages.catalog_publishing.infrastructure.schema import (
            DEMO_WAREHOUSE_TRACK_ID_MIN,
            ensure_catalog_publishing_tables,
        )
        from app.packages.catalog_rights.infrastructure.schema import (
            ensure_catalog_rights_tables,
        )
        from app.packages.engagement.services.app_storage import ensure_app_tables
        from app.packages.organizations.infrastructure.schema import (
            ensure_organization_tables,
        )

        ensure_organization_tables(conn)
        try:
            ensure_artist_tables(conn)
        except Exception:
            pass
        ensure_catalog_rights_tables(conn)
        ensure_catalog_publishing_tables(conn)
        try:
            ensure_app_tables(conn)
        except Exception:
            pass

        if _table_exists(conn, "app_catalog_duplicate_candidate"):
            conn.execute(
                """
                DELETE FROM app_catalog_duplicate_candidate
                WHERE submission_id IN (
                    SELECT id FROM app_release_submission
                    WHERE idempotency_key LIKE 'demo-s031%'
                )
                """
            )

        now = utc_now()
        # Artist profile
        profile_id = None
        if _table_exists(conn, "app_artist_profile"):
            prow = conn.execute(
                """
                SELECT id FROM app_artist_profile
                WHERE organization_id = ? AND normalized_name = 'demo artist s031'
                LIMIT 1
                """,
                [org_id],
            ).fetchone()
            if prow:
                profile_id = int(prow[0])
            else:
                profile_id = _next_id(conn, "app_artist_profile")
                conn.execute(
                    """
                    INSERT INTO app_artist_profile
                        (id, organization_id, display_name, legal_name, normalized_name,
                         status, warehouse_artist_id, created_by, created_at, updated_at)
                    VALUES (?, ?, 'Demo Artist', 'Demo Artist LLC', 'demo artist s031',
                            'active', NULL, ?, ?, ?)
                    """,
                    [profile_id, org_id, artist_user_id, now, now],
                )

        # Org membership artist_manager + portal access
        _ensure_org_member(conn, org_id, artist_user_id, ["artist_manager", "artist"])
        if profile_id:
            existing_portal = conn.execute(
                """
                SELECT id FROM app_artist_portal_access
                WHERE user_id = ? AND artist_profile_id = ? AND organization_id = ?
                LIMIT 1
                """,
                [artist_user_id, profile_id, org_id],
            ).fetchone()
            if not existing_portal:
                pid = _next_id(conn, "app_artist_portal_access")
                conn.execute(
                    """
                    INSERT INTO app_artist_portal_access
                        (id, user_id, artist_profile_id, organization_id, status, created_at)
                    VALUES (?, ?, ?, ?, 'active', ?)
                    """,
                    [pid, artist_user_id, profile_id, org_id, now],
                )

        # Catalog reviewer (owner) already has publish perms via owner role
        settings = get_settings()
        media_root = Path(settings.media_storage_root)
        if not media_root.is_absolute():
            media_root = Path.cwd() / media_root
        media = LocalMediaStorageProvider(root=media_root)
        uc = CatalogPublishingUseCases(conn, media=media)

        # Distinct durations/sizes so each demo upload has a unique sha256
        # (duplicate hash conflicts otherwise leave later submissions stuck in draft).
        wav = make_minimal_wav()
        png = make_minimal_png(512, 512)

        def _wav(ms: int) -> bytes:
            return make_minimal_wav(duration_ms=ms)

        def _png(w: int, h: int) -> bytes:
            return make_minimal_png(w, h)

        # Shared 60/40 rights contract + asset for published demo
        asset_id = 9101
        contract_id = None
        if _table_exists(conn, "app_catalog_asset"):
            arow = conn.execute(
                "SELECT id FROM app_catalog_asset WHERE id = ?", [asset_id]
            ).fetchone()
            if not arow:
                conn.execute(
                    """
                    INSERT INTO app_catalog_asset
                        (id, organization_id, title, status, warehouse_track_id,
                         artist_profile_id, created_by, created_at, updated_at)
                    VALUES (?, ?, '[DEMO-SUBMIT] Published Single', 'active', ?,
                            ?, ?, ?, ?)
                    """,
                    [
                        asset_id,
                        org_id,
                        DEMO_WAREHOUSE_TRACK_ID_MIN,
                        profile_id,
                        owner_user_id,
                        now,
                        now,
                    ],
                )
            crow = conn.execute(
                """
                SELECT id FROM app_rights_contract
                WHERE asset_id = ? AND organization_id = ? AND evidence_ref = 'demo-s031'
                LIMIT 1
                """,
                [asset_id, org_id],
            ).fetchone()
            if crow:
                contract_id = int(crow[0])
            else:
                contract_id = _next_id(conn, "app_rights_contract")
                conn.execute(
                    """
                    INSERT INTO app_rights_contract
                        (id, organization_id, asset_id, rights_type, status, exclusive,
                         valid_from, valid_to, evidence_ref, created_by, created_at, updated_at)
                    VALUES (?, ?, ?, 'master', 'active', FALSE, DATE '2020-01-01', NULL,
                            'demo-s031', ?, ?, ?)
                    """,
                    [contract_id, org_id, asset_id, owner_user_id, now, now],
                )
                for pname, pct in (("Demo Artist S031", 60), ("Demo Label S031", 40)):
                    pid = _next_id(conn, "app_rights_contract_party")
                    conn.execute(
                        """
                        INSERT INTO app_rights_contract_party
                            (id, contract_id, party_name, party_type, ownership_percentage,
                             organization_id, artist_profile_id, created_at, updated_at)
                        VALUES (?, ?, ?, 'external', ?, NULL, NULL, ?, ?)
                        """,
                        [pid, contract_id, pname, pct, now, now],
                    )

        # Blocked rights contract 90%
        bad_asset = 9102
        bad_contract = None
        if _table_exists(conn, "app_catalog_asset"):
            if not conn.execute(
                "SELECT 1 FROM app_catalog_asset WHERE id = ?", [bad_asset]
            ).fetchone():
                conn.execute(
                    """
                    INSERT INTO app_catalog_asset
                        (id, organization_id, title, status, warehouse_track_id,
                         artist_profile_id, created_by, created_at, updated_at)
                    VALUES (?, ?, '[DEMO-SUBMIT] Blocked Rights', 'active', NULL,
                            ?, ?, ?, ?)
                    """,
                    [bad_asset, org_id, profile_id, owner_user_id, now, now],
                )
            brow = conn.execute(
                """
                SELECT id FROM app_rights_contract
                WHERE asset_id = ? AND evidence_ref = 'demo-s031-bad'
                LIMIT 1
                """,
                [bad_asset],
            ).fetchone()
            if brow:
                bad_contract = int(brow[0])
            else:
                bad_contract = _next_id(conn, "app_rights_contract")
                conn.execute(
                    """
                    INSERT INTO app_rights_contract
                        (id, organization_id, asset_id, rights_type, status, exclusive,
                         valid_from, valid_to, evidence_ref, created_by, created_at, updated_at)
                    VALUES (?, ?, ?, 'master', 'active', FALSE, DATE '2020-01-01', NULL,
                            'demo-s031-bad', ?, ?, ?)
                    """,
                    [bad_contract, org_id, bad_asset, owner_user_id, now, now],
                )
                pid = _next_id(conn, "app_rights_contract_party")
                conn.execute(
                    """
                    INSERT INTO app_rights_contract_party
                        (id, contract_id, party_name, party_type, ownership_percentage,
                         organization_id, artist_profile_id, created_at, updated_at)
                    VALUES (?, ?, 'Solo 90', 'external', 90, NULL, NULL, ?, ?)
                    """,
                    [pid, bad_contract, now, now],
                )

        def _ensure_submission(key: str, title: str, **kwargs):
            row = conn.execute(
                "SELECT id, status FROM app_release_submission WHERE idempotency_key = ?",
                [key],
            ).fetchone()
            if row:
                return int(row[0]), str(row[1]), True
            draft = uc.create_draft(
                actor_user_id=artist_user_id,
                organization_id=org_id,
                artist_profile_id=profile_id or 1,
                title=title,
                release_type="single",
                idempotency_key=key,
                is_demo=True,
                rights_contract_id=kwargs.get("rights_contract_id"),
                planned_release_date=kwargs.get("planned_release_date"),
            )
            return int(draft["id"]), "draft", False

        from datetime import date

        created = {}

        # 1) draft
        sid, _, _ = _ensure_submission("demo-s031-draft", "[DEMO] Draft Single")
        created["draft"] = sid

        # 2) changes_requested
        sid, st, existed = _ensure_submission(
            "demo-s031-changes", "[DEMO] Changes Requested"
        )
        if not existed:
            tr = uc.add_track(
                submission_id=sid, organization_id=org_id, title="Changes Track"
            )
            uc.upload_audio(
                submission_id=sid,
                track_id=tr["id"],
                organization_id=org_id,
                actor_user_id=artist_user_id,
                filename="demo.wav",
                content_type="audio/wav",
                data=_wav(210),
            )
            uc.upload_cover(
                submission_id=sid,
                organization_id=org_id,
                actor_user_id=artist_user_id,
                filename="cover.png",
                content_type="image/png",
                data=png,
            )
            uc.submit(
                submission_id=sid,
                organization_id=org_id,
                actor_user_id=artist_user_id,
            )
            uc.request_changes(
                submission_id=sid,
                organization_id=org_id,
                actor_user_id=owner_user_id,
                notes="Please fix metadata",
            )
        created["changes_requested"] = sid

        # 3) scheduled — unique sha256 (222ms wav / 514px cover). Re-drive pipeline
        # if a prior seed left this in draft after duplicate-hash or partial failure.
        sid, st, _existed = _ensure_submission(
            "demo-s031-scheduled",
            "[DEMO] Scheduled Single",
            rights_contract_id=contract_id,
            planned_release_date=date(2026, 8, 1),
        )
        if contract_id and st != "scheduled":
            trow = conn.execute(
                """
                SELECT id, audio_media_id, warehouse_track_id
                FROM app_release_submission_track
                WHERE submission_id = ? ORDER BY id LIMIT 1
                """,
                [sid],
            ).fetchone()
            if not trow:
                tr = uc.add_track(
                    submission_id=sid,
                    organization_id=org_id,
                    title="Scheduled Track",
                    warehouse_track_id=DEMO_WAREHOUSE_TRACK_ID_MIN + 1,
                )
                tid = int(tr["id"])
                has_audio = False
            else:
                tid = int(trow[0])
                has_audio = trow[1] is not None
                if trow[2] is None or int(trow[2] or 0) == DEMO_WAREHOUSE_TRACK_ID_MIN:
                    conn.execute(
                        """
                        UPDATE app_release_submission_track
                        SET warehouse_track_id = ?
                        WHERE id = ?
                        """,
                        [DEMO_WAREHOUSE_TRACK_ID_MIN + 1, tid],
                    )
            if not has_audio:
                uc.upload_audio(
                    submission_id=sid,
                    track_id=tid,
                    organization_id=org_id,
                    actor_user_id=artist_user_id,
                    filename="sched.wav",
                    content_type="audio/wav",
                    data=_wav(222),
                )
            crow = conn.execute(
                "SELECT cover_media_id FROM app_release_submission WHERE id = ?",
                [sid],
            ).fetchone()
            if not crow or crow[0] is None:
                uc.upload_cover(
                    submission_id=sid,
                    organization_id=org_id,
                    actor_user_id=artist_user_id,
                    filename="sched.png",
                    content_type="image/png",
                    data=_png(514, 514),
                )
            uc.update_metadata(
                submission_id=sid,
                organization_id=org_id,
                actor_user_id=artist_user_id,
                rights_contract_id=contract_id,
            )
            if st in ("draft", "changes_requested"):
                uc.submit(
                    submission_id=sid,
                    organization_id=org_id,
                    actor_user_id=artist_user_id,
                )
            cur = conn.execute(
                "SELECT status FROM app_release_submission WHERE id = ?", [sid]
            ).fetchone()[0]
            if cur in ("submitted", "under_review"):
                uc.approve(
                    submission_id=sid,
                    organization_id=org_id,
                    actor_user_id=owner_user_id,
                    notes="ok",
                )
            cur = conn.execute(
                "SELECT status FROM app_release_submission WHERE id = ?", [sid]
            ).fetchone()[0]
            if cur == "approved":
                uc.schedule(
                    submission_id=sid,
                    organization_id=org_id,
                    actor_user_id=owner_user_id,
                )
        created["scheduled"] = sid

        # 4) published (60/40 contract)
        # Unique sha256 (401ms wav / 513px cover). If a prior seed left this in draft
        # after a duplicate-hash failure, re-drive the pipeline until published.
        sid, st, existed = _ensure_submission(
            "demo-s031-published",
            "[DEMO] Published Single",
            rights_contract_id=contract_id,
            planned_release_date=date(2026, 7, 1),
        )
        if contract_id and st != "published":
            trow = conn.execute(
                """
                SELECT id, audio_media_id FROM app_release_submission_track
                WHERE submission_id = ? ORDER BY id LIMIT 1
                """,
                [sid],
            ).fetchone()
            if not trow:
                tr = uc.add_track(
                    submission_id=sid,
                    organization_id=org_id,
                    title="Published Track",
                    warehouse_track_id=DEMO_WAREHOUSE_TRACK_ID_MIN,
                )
                tid = int(tr["id"])
                has_audio = False
            else:
                tid = int(trow[0])
                has_audio = trow[1] is not None
            if not has_audio:
                uc.upload_audio(
                    submission_id=sid,
                    track_id=tid,
                    organization_id=org_id,
                    actor_user_id=artist_user_id,
                    filename="pub.wav",
                    content_type="audio/wav",
                    data=_wav(401),
                )
            crow = conn.execute(
                "SELECT cover_media_id FROM app_release_submission WHERE id = ?",
                [sid],
            ).fetchone()
            if not crow or crow[0] is None:
                uc.upload_cover(
                    submission_id=sid,
                    organization_id=org_id,
                    actor_user_id=artist_user_id,
                    filename="pub.png",
                    content_type="image/png",
                    data=_png(513, 513),
                )
            # Link catalog asset to track for rights gate conflict check
            conn.execute(
                """
                UPDATE app_release_submission_track
                SET catalog_asset_id = ?, rights_contract_id = ?
                WHERE id = ?
                """,
                [asset_id, contract_id, tid],
            )
            uc.update_metadata(
                submission_id=sid,
                organization_id=org_id,
                actor_user_id=artist_user_id,
                rights_contract_id=contract_id,
            )
            if st in ("draft", "changes_requested"):
                uc.submit(
                    submission_id=sid,
                    organization_id=org_id,
                    actor_user_id=artist_user_id,
                )
            cur = conn.execute(
                "SELECT status FROM app_release_submission WHERE id = ?", [sid]
            ).fetchone()[0]
            if cur in ("submitted", "under_review"):
                uc.approve(
                    submission_id=sid,
                    organization_id=org_id,
                    actor_user_id=owner_user_id,
                )
            cur = conn.execute(
                "SELECT status FROM app_release_submission WHERE id = ?", [sid]
            ).fetchone()[0]
            if cur in ("approved", "scheduled"):
                uc.publish(
                    submission_id=sid,
                    organization_id=org_id,
                    actor_user_id=owner_user_id,
                    idempotency_key="demo-s031-publish",
                )
        created["published"] = sid
        pub_row = conn.execute(
            "SELECT status FROM app_release_submission WHERE id = ?", [sid]
        ).fetchone()
        if pub_row and pub_row[0] == "published" and _table_exists(
            conn, "app_track_audio_source"
        ):
            conn.execute(
                """
                UPDATE app_track_audio_source
                SET status = 'ok'
                WHERE track_id = ? AND provider = 'local_published'
                """,
                [DEMO_WAREHOUSE_TRACK_ID_MIN],
            )

        # 5) blocked rights (90%) — stays draft with bad contract attached
        sid, _, existed = _ensure_submission(
            "demo-s031-blocked-rights",
            "[DEMO] Blocked Rights",
            rights_contract_id=bad_contract,
        )
        if not existed:
            tr = uc.add_track(
                submission_id=sid, organization_id=org_id, title="Blocked Track"
            )
            uc.upload_audio(
                submission_id=sid,
                track_id=tr["id"],
                organization_id=org_id,
                actor_user_id=artist_user_id,
                filename="block.wav",
                content_type="audio/wav",
                data=_wav(230),
            )
            uc.upload_cover(
                submission_id=sid,
                organization_id=org_id,
                actor_user_id=artist_user_id,
                filename="block.png",
                content_type="image/png",
                data=png,
            )
            if bad_contract:
                conn.execute(
                    """
                    UPDATE app_release_submission_track
                    SET catalog_asset_id = ?, rights_contract_id = ?
                    WHERE id = ?
                    """,
                    [bad_asset, bad_contract, tr["id"]],
                )
                uc.update_metadata(
                    submission_id=sid,
                    organization_id=org_id,
                    actor_user_id=artist_user_id,
                    rights_contract_id=bad_contract,
                )
        created["blocked_rights"] = sid

        # 6) withdrawn — isolated warehouse id so withdraw cannot disable published audio
        sid, st, _existed = _ensure_submission(
            "demo-s031-withdrawn",
            "[DEMO] Withdrawn Single",
            rights_contract_id=contract_id,
            planned_release_date=date(2026, 6, 1),
        )
        withdrawn_wh = DEMO_WAREHOUSE_TRACK_ID_MIN + 2
        if contract_id and st != "withdrawn":
            trow = conn.execute(
                """
                SELECT id, audio_media_id, warehouse_track_id
                FROM app_release_submission_track
                WHERE submission_id = ? ORDER BY id LIMIT 1
                """,
                [sid],
            ).fetchone()
            if not trow:
                tr = uc.add_track(
                    submission_id=sid,
                    organization_id=org_id,
                    title="Withdrawn Track",
                    warehouse_track_id=withdrawn_wh,
                )
                tid = int(tr["id"])
                has_audio = False
            else:
                tid = int(trow[0])
                has_audio = trow[1] is not None
                if trow[2] is None or int(trow[2] or 0) == DEMO_WAREHOUSE_TRACK_ID_MIN:
                    conn.execute(
                        """
                        UPDATE app_release_submission_track
                        SET warehouse_track_id = ?
                        WHERE id = ?
                        """,
                        [withdrawn_wh, tid],
                    )
            if not has_audio:
                uc.upload_audio(
                    submission_id=sid,
                    track_id=tid,
                    organization_id=org_id,
                    actor_user_id=artist_user_id,
                    filename="wd.wav",
                    content_type="audio/wav",
                    data=_wav(240),
                )
            crow = conn.execute(
                "SELECT cover_media_id FROM app_release_submission WHERE id = ?", [sid]
            ).fetchone()
            if not crow or crow[0] is None:
                uc.upload_cover(
                    submission_id=sid,
                    organization_id=org_id,
                    actor_user_id=artist_user_id,
                    filename="wd.png",
                    content_type="image/png",
                    data=_png(516, 516),
                )
            uc.update_metadata(
                submission_id=sid,
                organization_id=org_id,
                actor_user_id=artist_user_id,
                rights_contract_id=contract_id,
            )
            if st in ("draft", "changes_requested"):
                uc.submit(
                    submission_id=sid,
                    organization_id=org_id,
                    actor_user_id=artist_user_id,
                )
            cur = conn.execute(
                "SELECT status FROM app_release_submission WHERE id = ?", [sid]
            ).fetchone()[0]
            if cur in ("submitted", "under_review"):
                uc.approve(
                    submission_id=sid,
                    organization_id=org_id,
                    actor_user_id=owner_user_id,
                )
            cur = conn.execute(
                "SELECT status FROM app_release_submission WHERE id = ?", [sid]
            ).fetchone()[0]
            if cur in ("approved", "scheduled"):
                uc.publish(
                    submission_id=sid,
                    organization_id=org_id,
                    actor_user_id=owner_user_id,
                    idempotency_key="demo-s031-withdrawn-pub",
                )
            cur = conn.execute(
                "SELECT status FROM app_release_submission WHERE id = ?", [sid]
            ).fetchone()[0]
            if cur == "published":
                uc.withdraw(
                    submission_id=sid,
                    organization_id=org_id,
                    actor_user_id=owner_user_id,
                    reason="Artist request",
                )
        created["withdrawn"] = sid

        # Guard: withdrawn demo must never leave canonical published audio disabled
        if _table_exists(conn, "app_track_audio_source"):
            pub_ok = conn.execute(
                """
                SELECT status FROM app_release_submission
                WHERE idempotency_key = 'demo-s031-published'
                """,
            ).fetchone()
            if pub_ok and pub_ok[0] == "published":
                conn.execute(
                    """
                    UPDATE app_track_audio_source
                    SET status = 'ok'
                    WHERE track_id = ? AND provider = 'local_published'
                    """,
                    [DEMO_WAREHOUSE_TRACK_ID_MIN],
                )

        out["seeded"] = True
        out["submissions"] = created
        out["artist_profile_id"] = profile_id
        out["contract_id"] = contract_id
    except Exception as exc:
        out["error"] = str(exc)
    return out


def seed_integrated_demo() -> dict[str, Any]:
    from app.core.database import using_write_conn
    from app.core.time_util import utc_now
    from app.packages.platform_rbac.infrastructure.schema import ensure_platform_rbac_tables
    from app.packages.subscriptions.infrastructure.schema import ensure_subscription_tables

    report: dict[str, Any] = {
        "ok": False,
        "demo": True,
        "accounts": [],
        "organization_slug": ORG_SLUG,
        "password_env": "DEMO_ACCOUNT_PASSWORD",
        "seeded_at": None,
    }

    with using_write_conn() as conn:
        ensure_platform_rbac_tables(conn)
        ensure_subscription_tables(conn)
        try:
            from app.packages.royalties.infrastructure.schema import ensure_royalty_tables
            from app.packages.catalog_rights.infrastructure.schema import (
                ensure_catalog_rights_tables,
            )
            from app.packages.catalog_publishing.infrastructure.schema import (
                ensure_catalog_publishing_tables,
            )

            ensure_catalog_rights_tables(conn)
            ensure_royalty_tables(conn)
            ensure_catalog_publishing_tables(conn)
        except Exception:
            pass
        ids: dict[str, int] = {}
        for username, email in DEMO_USERS:
            ids[username] = _ensure_user(conn, username, email)

        _assign_platform_role(conn, ids["platform.admin"], "platform_admin")
        _assign_platform_role(conn, ids["sales.manager"], "sales_manager")
        # Presentation demo: CRM (sales_manager) + cobros (billing_manager) — no owner/admin
        _assign_platform_role(conn, ids["demo.business"], "sales_manager")

        org_id = _ensure_canonical_org(conn, ids["organization.owner"])
        _ensure_org_member(conn, org_id, ids["organization.owner"], ["owner"])
        # billing_manager: invoices, payments, refunds, credit notes — not global plans
        _ensure_org_member(
            conn, org_id, ids["finance.manager"], ["billing_manager", "finance"]
        )
        _ensure_org_member(
            conn, org_id, ids["demo.business"], ["billing_manager"]
        )
        _ensure_professional_subscription(conn, org_id, ids["organization.owner"])
        personal = _seed_personal_line(conn, ids)
        royalties = _seed_demo_royalties(conn, org_id, ids["finance.manager"])
        publishing = _seed_demo_catalog_publishing(
            conn,
            org_id,
            ids["demo.artist"],
            ids["organization.owner"],
        )

        report["ok"] = True
        report["organization_id"] = org_id
        report["personal"] = personal
        report["royalties"] = royalties
        report["catalog_publishing"] = publishing
        report["accounts"] = [
            {
                "username": u,
                "email": e,
                "user_id": ids[u],
                "demo": True,
                "email_verified": True,
            }
            for u, e in DEMO_USERS
        ]
        report["seeded_at"] = utc_now().isoformat()
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed integrated VOXMETRIKS demo accounts")
    parser.add_argument(
        "--cleanup-first",
        action="store_true",
        help="Run cleanup_test_organizations.py --apply --retire-test-plans first",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if os.environ.get("VOXMETRIKS_SEED_DEMO_ACCOUNTS", "").strip() not in (
        "1",
        "true",
        "yes",
        "on",
    ):
        msg = (
            "Refusing to seed: set VOXMETRIKS_SEED_DEMO_ACCOUNTS=1 "
            "and DEMO_ACCOUNT_PASSWORD before running."
        )
        print(msg)
        return 2

    if args.cleanup_first:
        import subprocess

        cleanup = _BACKEND / "scripts" / "cleanup_test_organizations.py"
        subprocess.run(
            [
                sys.executable,
                str(cleanup),
                "--apply",
                "--retire-test-plans",
                "--json",
            ],
            cwd=str(_BACKEND),
            check=False,
        )

    report = seed_integrated_demo()
    # Never include password
    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        print("Integrated demo seed complete.")
        print(f"  organization: {report.get('organization_slug')}")
        print(f"  accounts: {len(report.get('accounts') or [])}")
        print("  password: from DEMO_ACCOUNT_PASSWORD (not printed)")
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
