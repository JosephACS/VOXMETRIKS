"""Optional enterprise demo seed — Spec 028 polish / VOXMETRIKS Demo org.

Canonical organization:
  display_name=Voxmetriks Studio, slug=voxmetriks-studio, country=EC,
  timezone=America/Guayaquil, currency=USD, type=label,
  is_demo=TRUE, is_test=FALSE

Run explicitly only when ``VOXMETRIKS_SEED_ENTERPRISE_DEMO=1``:

    VOXMETRIKS_SEED_ENTERPRISE_DEMO=1 python scripts/seed_enterprise_demo.py

Never executes on import. All records are synthetic / demo (markers:
``(Synthetic)``, ``(Demo)``, ``[SYNTHETIC]``, ``demo_seed``).
Safe when tables/columns are missing (skips gracefully).
Does not touch warehouse music / fact tables. No real email delivery
(``@example.invalid`` only).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

_DEMO_BANNER = """
====================================================================
  VOXMETRIKS DEMO SEED - SYNTHETIC / ACADEMIC DATA
  Org: voxmetriks-studio - Opt-in only. Not for production.
====================================================================
"""

ORG_SLUG = "voxmetriks-studio"
ORG_DISPLAY = "Voxmetriks Studio"
LEGACY_SLUG = "enterprise-demo-s028"
DEMO_PLAN_CODE = "enterprise"
DEMO_MONTHLY_AMOUNT = 499.00


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


def _count(entities: dict, key: str, n: int = 1) -> None:
    entities[key] = int(entities.get(key, 0) or 0) + n


def _assign_role(conn, member_id: int, role_code: str, admin_id: int, now, skipped: list) -> bool:
    """Assign an active member role if catalogs exist. Returns True if role present."""
    if not (
        _table_exists(conn, "app_business_role") and _table_exists(conn, "app_member_role")
    ):
        return False
    role = conn.execute(
        "SELECT id FROM app_business_role WHERE code = ?", [role_code]
    ).fetchone()
    if not role:
        skipped.append(f"role_{role_code}_missing")
        return False
    role_id = int(role[0])
    existing = conn.execute(
        "SELECT 1 FROM app_member_role WHERE member_id = ? AND role_id = ? AND status = 'active'",
        [member_id, role_id],
    ).fetchone()
    if existing:
        return True
    try:
        mrid = _next_id(conn, "app_member_role")
        conn.execute(
            """
            INSERT INTO app_member_role
                (id, member_id, role_id, status, assigned_by, assigned_at)
            VALUES (?, ?, ?, 'active', ?, ?)
            """,
            [mrid, member_id, role_id, admin_id, now],
        )
        return True
    except Exception:
        skipped.append(f"app_member_role_{role_code}")
        return False


def seed_enterprise_demo() -> dict[str, object]:
    from app.core.database import using_write_conn
    from app.core.time_util import utc_now

    result: dict[str, object] = {
        "seeded": False,
        "organization_id": None,
        "organization_slug": ORG_SLUG,
        "plan_id": None,
        "plan_price_id": None,
        "subscription_id": None,
        "entities": {},
        "skipped": [],
    }
    entities: dict = result["entities"]  # type: ignore[assignment]
    skipped: list = result["skipped"]  # type: ignore[assignment]

    with using_write_conn() as conn:
        now = utc_now()

        if not _table_exists(conn, "app_user"):
            skipped.append("app_user")
            return result

        admin = conn.execute(
            "SELECT id FROM app_user WHERE username = 'admin' OR email LIKE '%admin%' LIMIT 1"
        ).fetchone()
        if not admin:
            skipped.append("admin_user")
            return result
        admin_id = int(admin[0])

        # ── Organization (canonical + legacy migrate) ─────────────────────
        org_id: int | None = None
        if not _table_exists(conn, "app_organization"):
            skipped.append("app_organization")
            return result

        existing = conn.execute(
            "SELECT id FROM app_organization WHERE slug = ?", [ORG_SLUG]
        ).fetchone()
        legacy = None
        if not existing:
            legacy = conn.execute(
                "SELECT id FROM app_organization WHERE slug = ?", [LEGACY_SLUG]
            ).fetchone()

        if existing:
            org_id = int(existing[0])
        elif legacy:
            org_id = int(legacy[0])
            try:
                sets = [
                    "display_name = ?",
                    "slug = ?",
                    "status = 'active'",
                    "timezone = 'America/Guayaquil'",
                    "default_currency = 'USD'",
                    "organization_type = 'label'",
                    "updated_at = ?",
                ]
                params: list = [ORG_DISPLAY, ORG_SLUG, now]
                if _has_column(conn, "app_organization", "country_code"):
                    sets.insert(2, "country_code = 'EC'")
                if _has_column(conn, "app_organization", "is_demo"):
                    # Keep the seeded enterprise workspace visible to the demo
                    # account without requiring SHOW_DEMO_ORGANIZATIONS=true.
                    sets.append("is_demo = FALSE")
                if _has_column(conn, "app_organization", "is_test"):
                    sets.append("is_test = FALSE")
                conn.execute(
                    f"UPDATE app_organization SET {', '.join(sets)} WHERE id = ?",
                    [*params, org_id],
                )
                entities["organization_migrated_from_legacy"] = LEGACY_SLUG
            except Exception:
                skipped.append("legacy_org_migrate")
        else:
            org_id = _next_id(conn, "app_organization")
            cols = (
                "id, display_name, slug, organization_type, country_code, timezone, "
                "default_currency, status, created_by, created_at, updated_at"
            )
            vals = (
                "?, ?, ?, 'label', 'EC', 'America/Guayaquil', 'USD', 'active', ?, ?, ?"
            )
            params = [org_id, ORG_DISPLAY, ORG_SLUG, admin_id, now, now]
            if _has_column(conn, "app_organization", "is_demo"):
                cols += ", is_demo"
                vals += ", FALSE"
            if _has_column(conn, "app_organization", "is_test"):
                cols += ", is_test"
                vals += ", FALSE"
            conn.execute(f"INSERT INTO app_organization ({cols}) VALUES ({vals})", params)

        # Refresh demo flags on existing canonical org
        if org_id is not None:
            try:
                flag_sets = ["updated_at = ?"]
                flag_params: list = [now]
                if _has_column(conn, "app_organization", "is_demo"):
                    flag_sets.append("is_demo = FALSE")
                if _has_column(conn, "app_organization", "is_test"):
                    flag_sets.append("is_test = FALSE")
                if _has_column(conn, "app_organization", "country_code"):
                    flag_sets.append("country_code = 'EC'")
                flag_sets.append("timezone = 'America/Guayaquil'")
                flag_sets.append("default_currency = 'USD'")
                flag_sets.append("display_name = ?")
                flag_params.append(ORG_DISPLAY)
                flag_sets.append("status = 'active'")
                conn.execute(
                    f"UPDATE app_organization SET {', '.join(flag_sets)} WHERE id = ?",
                    [*flag_params, org_id],
                )
            except Exception:
                skipped.append("org_flag_refresh")

            result["organization_id"] = org_id
        assert org_id is not None

        # Membership + owner (+ administrator)
        member_id: int | None = None
        if _table_exists(conn, "app_organization_member"):
            member = conn.execute(
                    "SELECT id FROM app_organization_member WHERE organization_id = ? AND user_id = ?",
                    [org_id, admin_id],
            ).fetchone()
            if not member:
                member_id = _next_id(conn, "app_organization_member")
                conn.execute(
                        """
                        INSERT INTO app_organization_member
                            (id, organization_id, user_id, status, created_by, created_at, updated_at)
                        VALUES (?, ?, ?, 'active', ?, ?, ?)
                        """,
                    [member_id, org_id, admin_id, admin_id, now, now],
                )
            else:
                member_id = int(member[0])
            entities["membership"] = 1
            if member_id is not None:
                if _assign_role(conn, member_id, "owner", admin_id, now, skipped):
                    _count(entities, "member_roles")
                if _assign_role(conn, member_id, "administrator", admin_id, now, skipped):
                    _count(entities, "member_roles")
        else:
            skipped.append("app_organization_member")

        # Admin active organization preference
        if _table_exists(conn, "app_user_organization_preference"):
            try:
                pref = conn.execute(
                    "SELECT user_id FROM app_user_organization_preference WHERE user_id = ?",
                    [admin_id],
                ).fetchone()
                if pref:
                    conn.execute(
                        """
                        UPDATE app_user_organization_preference
                        SET active_organization_id = ?, updated_at = ?, updated_by = ?
                        WHERE user_id = ?
                        """,
                        [org_id, now, admin_id, admin_id],
                    )
                else:
                    conn.execute(
                        """
                        INSERT INTO app_user_organization_preference
                            (user_id, active_organization_id, updated_at, updated_by)
                        VALUES (?, ?, ?, ?)
                        """,
                        [admin_id, org_id, now, admin_id],
                    )
                entities["active_organization_preference"] = 1
            except Exception:
                skipped.append("app_user_organization_preference")
        else:
            skipped.append("app_user_organization_preference")

        # ── Plan + subscription (Enterprise monthly USD 499) ──────────────
        plan_id: int | None = None
        price_id: int | None = None
        if _table_exists(conn, "app_plan"):
            from app.packages.subscriptions.application.commercial_catalog import (
                ensure_commercial_catalog,
                get_active_price_id,
            )

            ensure_commercial_catalog(conn)
            plan_row = conn.execute(
                f"SELECT id FROM app_plan WHERE code = '{DEMO_PLAN_CODE}' AND status = 'active'"
            ).fetchone()
            if plan_row:
                plan_id = int(plan_row[0])
            result["plan_id"] = plan_id
            if plan_id and _table_exists(conn, "app_plan_price"):
                price_id = get_active_price_id(
                    conn, plan_code=DEMO_PLAN_CODE, billing_period="monthly", currency="USD"
                )
                if price_id is None:
                    price_id = _next_id(conn, "app_plan_price")
                    conn.execute(
                        """
                        INSERT INTO app_plan_price
                            (id, plan_id, currency, billing_period, amount, status, created_at, updated_at)
                        VALUES (?, ?, 'USD', 'monthly', ?, 'active', ?, ?)
                        """,
                        [price_id, plan_id, DEMO_MONTHLY_AMOUNT, now, now],
                    )
                result["plan_price_id"] = price_id
        else:
            skipped.append("app_plan")

        sub_id: int | None = None
        if org_id and plan_id and _table_exists(conn, "app_subscription"):
            sub_row = conn.execute(
                "SELECT id FROM app_subscription WHERE organization_id = ? AND plan_id = ?",
                [org_id, plan_id],
            ).fetchone()
            if sub_row:
                sub_id = int(sub_row[0])
            else:
                sub_id = _next_id(conn, "app_subscription")
                price_id = result.get("plan_price_id")  # type: ignore[assignment]
                try:
                    conn.execute(
                        """
                        INSERT INTO app_subscription
                            (id, organization_id, plan_id, plan_price_id, status, billing_currency,
                             activation_source, access_state, created_at, updated_at)
                        VALUES (?, ?, ?, ?, 'active', 'USD', 'demo_seed_synthetic', 'full', ?, ?)
                        """,
                        [sub_id, org_id, plan_id, price_id, now, now],
                    )
                except Exception:
                    skipped.append("app_subscription_insert")
                    sub_id = None
            if sub_id and result.get("plan_price_id"):
                try:
                    conn.execute(
                        """
                        UPDATE app_subscription
                        SET plan_price_id = COALESCE(plan_price_id, ?),
                            status = 'active',
                            access_state = 'full',
                            updated_at = ?
                        WHERE id = ? AND organization_id = ?
                        """,
                        [result["plan_price_id"], now, sub_id, org_id],
                    )
                except Exception:
                    skipped.append("app_subscription_update")
                result["subscription_id"] = sub_id
            if sub_id:
                entities["subscription"] = 1
                try:
                    from app.packages.subscriptions.application.use_cases import (
                        ensure_plan_entitlements,
                    )

                    ensure_plan_entitlements(conn, int(sub_id))
                except Exception:
                    skipped.append("subscription_entitlements")
        else:
            skipped.append("app_subscription")

        # ── CRM: 5 prospects + contacts; 3 opportunities; quotation chain ─
        prospect_ids: list[int] = []
        contact_ids: list[int] = []
        opportunity_ids: list[int] = []

        prospect_defs = [
            ("Andes Records Label (Synthetic)", "Andes Records", "andes.records@example.invalid", "qualified"),
            ("Costa Pacific Management (Demo)", "Costa Pacific", "costa.pacific@example.invalid", "contacted"),
            ("Sierra Sound Collective (Synthetic)", "Sierra Sound", "sierra.sound@example.invalid", "new"),
            ("Galapagos Media Group (Demo)", "Galapagos Media", "galapagos.media@example.invalid", "qualified"),
            ("Quito Indie House (Synthetic)", "Quito Indie", "quito.indie@example.invalid", "converted"),
        ]
        if _table_exists(conn, "app_crm_prospect"):
            for display, company, email, status in prospect_defs:
                try:
                    row = conn.execute(
                        "SELECT id FROM app_crm_prospect WHERE display_name = ? AND organization_id = ?",
                        [display, org_id],
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
                            VALUES (?, ?, ?, ?, NULL, 'demo_seed', ?, ?, ?,
                                    '[SYNTHETIC] demo_seed prospect', ?, ?, NULL)
                            """,
                            [pid, display, company, email, status, admin_id, org_id, now, now],
                        )
                        _count(entities, "prospects")
                    prospect_ids.append(pid)

                    if _table_exists(conn, "app_crm_contact"):
                        local, _, domain = email.partition("@")
                        cemail = f"{local}.contact@{domain}"
                        ct = conn.execute(
                            "SELECT id FROM app_crm_contact WHERE email = ?", [cemail]
                        ).fetchone()
                        if ct:
                            cid = int(ct[0])
                        else:
                            cid = _next_id(conn, "app_crm_contact")
                            conn.execute(
                                """
                                INSERT INTO app_crm_contact
                                    (id, full_name, email, email_normalized, phone, company_name,
                                     linked_user_id, created_by, created_at, updated_at, deleted_at)
                                VALUES (?, ?, ?, ?, NULL, ?, NULL, ?, ?, ?, NULL)
                                """,
                                [
                                    cid,
                                    f"{company} Contact (Synthetic)",
                                    cemail,
                                    cemail.lower(),
                                    company,
                                    admin_id,
                                    now,
                                    now,
                                ],
                            )
                            _count(entities, "contacts")
                        contact_ids.append(cid)
                        if _table_exists(conn, "app_crm_prospect_contact"):
                            if not conn.execute(
                                "SELECT 1 FROM app_crm_prospect_contact WHERE prospect_id = ? AND contact_id = ?",
                                [pid, cid],
                            ).fetchone():
                                conn.execute(
                                    """
                                    INSERT INTO app_crm_prospect_contact
                                        (prospect_id, contact_id, is_primary, is_decision_maker, is_signatory, added_at)
                                    VALUES (?, ?, TRUE, TRUE, TRUE, ?)
                                    """,
                                    [pid, cid, now],
                                )
                                _count(entities, "prospect_contacts")
                except Exception:
                    skipped.append(f"crm_prospect:{display[:24]}")
        else:
            skipped.append("app_crm_prospect")

        # Opportunities in different stages (use first three prospects)
        opp_defs = [
            ("Andes Professional Expansion (Synthetic)", "proposal", 60, 9900.00),
            ("Costa Pacific Onboarding Deal (Demo)", "negotiation", 75, 11880.00),
            ("Galapagos Closed Win (Synthetic)", "closed_won", 100, 9900.00),
        ]
        if prospect_ids and _table_exists(conn, "app_crm_opportunity"):
            for i, (name, stage, prob, value) in enumerate(opp_defs):
                prosp_id = prospect_ids[min(i, len(prospect_ids) - 1)]
                try:
                    opp = conn.execute(
                        "SELECT id FROM app_crm_opportunity WHERE name = ? AND organization_id = ?",
                        [name, org_id],
                    ).fetchone()
                    if opp:
                        oid = int(opp[0])
                    else:
                        oid = _next_id(conn, "app_crm_opportunity")
                        close_date = None
                        outcome = None
                        if stage == "closed_won":
                            outcome = "won"
                        conn.execute(
                            """
                            INSERT INTO app_crm_opportunity
                                (id, prospect_id, name, description, stage, probability,
                                 expected_value, currency, expected_close_date, actual_close_date,
                                 outcome, owner_user_id, organization_id, created_at, updated_at, deleted_at)
                            VALUES (?, ?, ?, '[SYNTHETIC] demo_seed opportunity', ?, ?,
                                    ?, 'USD', NULL, ?, ?, ?, ?, ?, ?, NULL)
                            """,
                            [
                                oid,
                                prosp_id,
                                name,
                                stage,
                                prob,
                                value,
                                now if stage == "closed_won" else None,
                                outcome,
                                admin_id,
                                org_id,
                                now,
                                now,
                            ],
                        )
                        _count(entities, "opportunities")
                    opportunity_ids.append(oid)
                except Exception:
                    skipped.append(f"crm_opportunity:{stage}")
        elif not prospect_ids:
            skipped.append("app_crm_opportunity_no_prospects")
        else:
            skipped.append("app_crm_opportunity")

        # Accepted quotation + contract + conversion on closed_won opportunity
        quotation_id = None
        version_id = None
        if opportunity_ids and _table_exists(conn, "app_crm_quotation"):
            won_opp = opportunity_ids[-1] if opportunity_ids else None
            if won_opp:
                try:
                    quot = conn.execute(
                        "SELECT id FROM app_crm_quotation WHERE opportunity_id = ?",
                        [won_opp],
                    ).fetchone()
                    if quot:
                        quotation_id = int(quot[0])
                    else:
                        quotation_id = _next_id(conn, "app_crm_quotation")
                        conn.execute(
                            """
                            INSERT INTO app_crm_quotation
                                (id, opportunity_id, status, currency, notes, row_version,
                                 current_version_no, created_by, created_at, updated_at, deleted_at)
                            VALUES (?, ?, 'accepted', 'USD', '[SYNTHETIC] demo_seed accepted quotation',
                                    1, 1, ?, ?, ?, NULL)
                            """,
                            [quotation_id, won_opp, admin_id, now, now],
                        )
                        _count(entities, "quotations")

                    if quotation_id and _table_exists(conn, "app_crm_quotation_version"):
                        ver = conn.execute(
                            "SELECT id FROM app_crm_quotation_version WHERE quotation_id = ?",
                            [quotation_id],
                        ).fetchone()
                        if ver:
                            version_id = int(ver[0])
                        else:
                            version_id = _next_id(conn, "app_crm_quotation_version")
                            conn.execute(
                                """
                                INSERT INTO app_crm_quotation_version
                                    (id, quotation_id, version_no, status, subtotal, discount_pct,
                                     discount_requires_approval, total, notes, is_immutable,
                                     sent_at, accepted_at, rejected_at, created_by, created_at)
                                VALUES (?, ?, 1, 'accepted', 9900.00, 0, FALSE, 9900.00,
                                        '[SYNTHETIC] demo_seed quotation version', TRUE, ?, ?, NULL, ?, ?)
                                """,
                                [version_id, quotation_id, now, now, admin_id, now],
                            )
                            _count(entities, "quotation_versions")
                        if version_id and _table_exists(conn, "app_crm_quotation_item"):
                            if not conn.execute(
                                "SELECT 1 FROM app_crm_quotation_item WHERE quotation_version_id = ?",
                                [version_id],
                            ).fetchone():
                                item_id = _next_id(conn, "app_crm_quotation_item")
                                conn.execute(
                                    """
                                    INSERT INTO app_crm_quotation_item
                                        (id, quotation_version_id, description, quantity, unit_price,
                                         discount_pct, line_total, plan_code, sort_order, created_at)
                                    VALUES (?, ?, '[SYNTHETIC] Professional seats (Demo)', 1, 9900.00,
                                            0, 9900.00, 'professional', 1, ?)
                                    """,
                                    [item_id, version_id, now],
                                )
                                _count(entities, "quotation_items")

                        if version_id and _table_exists(conn, "app_commercial_contract"):
                            cc = conn.execute(
                                "SELECT id FROM app_commercial_contract WHERE quotation_version_id = ?",
                                [version_id],
                            ).fetchone()
                            if not cc:
                                contract_id = _next_id(conn, "app_commercial_contract")
                                conn.execute(
                                    """
                                    INSERT INTO app_commercial_contract
                                        (id, quotation_version_id, opportunity_id, organization_id,
                                         legal_name, status, acceptance_evidence, accepted_at,
                                         created_by, created_at, updated_at)
                                    VALUES (?, ?, ?, ?, 'Galapagos Media Group (Synthetic)', 'accepted',
                                            '[SYNTHETIC] demo_seed acceptance evidence', ?, ?, ?, ?)
                                    """,
                                    [
                                        contract_id,
                                        version_id,
                                        won_opp,
                                        org_id,
                                        now,
                                        admin_id,
                                        now,
                                        now,
                                    ],
                                )
                                _count(entities, "commercial_contracts")
                            else:
                                _count(entities, "commercial_contracts")

                    if _table_exists(conn, "app_crm_customer_conversion"):
                        conv = conn.execute(
                            "SELECT id FROM app_crm_customer_conversion WHERE opportunity_id = ?",
                            [won_opp],
                        ).fetchone()
                        if not conv:
                            conv_id = _next_id(conn, "app_crm_customer_conversion")
                            contact_for_conv = contact_ids[-1] if contact_ids else None
                            conn.execute(
                                """
                                INSERT INTO app_crm_customer_conversion
                                    (id, opportunity_id, mode, status, organization_id, contact_id,
                                     signatory_user_id, claim_token_hash, claim_token_expires_at,
                                     claim_consumed_at, idempotency_key, requested_by,
                                     completed_at, failure_reason, created_at, updated_at)
                                VALUES (?, ?, 'link_existing', 'completed', ?, ?, ?,
                                        NULL, NULL, NULL, ?, ?, ?, NULL, ?, ?)
                                """,
                                [
                                    conv_id,
                                    won_opp,
                                    org_id,
                                    contact_for_conv,
                                    admin_id,
                                    f"demo_seed_conversion_{won_opp}",
                                    admin_id,
                                    now,
                                    now,
                                    now,
                                ],
                            )
                            _count(entities, "customer_conversions")
                        else:
                            _count(entities, "customer_conversions")
                except Exception:
                    skipped.append("crm_quotation_chain")

        # ── Billing: paid + pending invoices, failed attempt, reconciled pay ─
        billing_profile_id: int | None = None
        paid_invoice_id: int | None = None
        pending_invoice_id: int | None = None

        if _table_exists(conn, "app_billing_profile"):
            try:
                bp = conn.execute(
                    "SELECT id FROM app_billing_profile WHERE organization_id = ?", [org_id]
                ).fetchone()
                if bp:
                    billing_profile_id = int(bp[0])
                else:
                    billing_profile_id = _next_id(conn, "app_billing_profile")
                    conn.execute(
                        """
                        INSERT INTO app_billing_profile
                            (id, organization_id, default_currency, legal_name, tax_id,
                             billing_address, email, status, created_at, updated_at)
                        VALUES (?, ?, 'USD', 'VOXMETRIKS Demo (Synthetic)', 'DEMO-EC-TAX',
                                'Guayaquil, EC — demo address', 'billing.demo@example.invalid',
                                'active', ?, ?)
                        """,
                        [billing_profile_id, org_id, now, now],
                    )
                entities["billing_profile"] = 1
            except Exception:
                skipped.append("app_billing_profile")
                billing_profile_id = None
        else:
            skipped.append("app_billing_profile")

        if billing_profile_id and _table_exists(conn, "app_invoice"):
            # Paid invoice
            try:
                inv = conn.execute(
                    "SELECT id FROM app_invoice WHERE invoice_number = 'DEMO-STUDIO-INV-PAID-001' AND organization_id = ?",
                    [org_id],
                ).fetchone()
                if inv:
                    paid_invoice_id = int(inv[0])
                else:
                    paid_invoice_id = _next_id(conn, "app_invoice")
                    conn.execute(
                        """
                        INSERT INTO app_invoice
                            (id, organization_id, billing_profile_id, subscription_id,
                             invoice_number, currency, status, subtotal, total,
                             amount_paid, amount_due, period_start, period_end, due_date,
                             issued_at, paid_at, voided_at, notes, created_at, updated_at)
                        VALUES (?, ?, ?, ?, 'DEMO-STUDIO-INV-PAID-001', 'USD', 'paid',
                                99.00, 99.00, 99.00, 0, CURRENT_DATE - INTERVAL 30 DAY,
                                CURRENT_DATE, CURRENT_DATE - INTERVAL 20 DAY,
                                ?, ?, NULL,
                                '[SYNTHETIC] demo_seed paid invoice — MOCK payment', ?, ?)
                        """,
                        [paid_invoice_id, org_id, billing_profile_id, sub_id, now, now, now, now],
                    )
                _count(entities, "invoices")
                if _table_exists(conn, "app_invoice_item") and paid_invoice_id:
                    if not conn.execute(
                        "SELECT 1 FROM app_invoice_item WHERE invoice_id = ?", [paid_invoice_id]
                    ).fetchone():
                        iid = _next_id(conn, "app_invoice_item")
                        conn.execute(
                            """
                            INSERT INTO app_invoice_item
                                (id, invoice_id, description, quantity, unit_price, amount, created_at)
                            VALUES (?, ?, '[SYNTHETIC] Professional monthly (Demo)', 1, 99.00, 99.00, ?)
                            """,
                            [iid, paid_invoice_id, now],
                        )
                        _count(entities, "invoice_items")
            except Exception:
                skipped.append("invoice_paid")

            # Pending / issued invoice
            try:
                inv2 = conn.execute(
                    "SELECT id FROM app_invoice WHERE invoice_number = 'DEMO-STUDIO-INV-PENDING-002' AND organization_id = ?",
                    [org_id],
                ).fetchone()
                if inv2:
                    pending_invoice_id = int(inv2[0])
                else:
                    pending_invoice_id = _next_id(conn, "app_invoice")
                    conn.execute(
                        """
                        INSERT INTO app_invoice
                            (id, organization_id, billing_profile_id, subscription_id,
                             invoice_number, currency, status, subtotal, total,
                             amount_paid, amount_due, period_start, period_end, due_date,
                             issued_at, paid_at, voided_at, notes, created_at, updated_at)
                        VALUES (?, ?, ?, ?, 'DEMO-STUDIO-INV-PENDING-002', 'USD', 'issued',
                                99.00, 99.00, 0, 99.00, CURRENT_DATE, CURRENT_DATE + INTERVAL 30 DAY,
                                CURRENT_DATE + INTERVAL 14 DAY, ?, NULL, NULL,
                                '[SYNTHETIC] demo_seed pending invoice', ?, ?)
                        """,
                        [pending_invoice_id, org_id, billing_profile_id, sub_id, now, now, now],
                    )
                _count(entities, "invoices")
            except Exception:
                skipped.append("invoice_pending")

            # Failed payment attempt (against pending invoice)
            if pending_invoice_id and _table_exists(conn, "app_payment_attempt"):
                try:
                    fail_key = f"demo-seed-fail-{pending_invoice_id}"
                    att = conn.execute(
                        "SELECT id FROM app_payment_attempt WHERE idempotency_key = ?",
                        [fail_key],
                    ).fetchone()
                    if not att:
                        fail_id = _next_id(conn, "app_payment_attempt")
                        conn.execute(
                            """
                            INSERT INTO app_payment_attempt
                                (id, organization_id, invoice_id, payment_method_ref_id, provider_code,
                                 idempotency_key, amount, currency, status, provider_attempt_id,
                                 failure_reason, created_at, updated_at)
                            VALUES (?, ?, ?, NULL, 'mock', ?, 99.00, 'USD', 'failed', 'demo-fail-attempt',
                                    '[SYNTHETIC] mock card declined — demo_seed', ?, ?)
                            """,
                            [fail_id, org_id, pending_invoice_id, fail_key, now, now],
                        )
                    _count(entities, "payment_attempts_failed")
                except Exception:
                    skipped.append("payment_attempt_failed")

            # Succeeded + reconciled mock payment (paid invoice)
            if paid_invoice_id and _table_exists(conn, "app_payment_attempt"):
                try:
                    ok_key = f"demo-seed-ok-{paid_invoice_id}"
                    att = conn.execute(
                        "SELECT id FROM app_payment_attempt WHERE idempotency_key = ?",
                        [ok_key],
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
                            VALUES (?, ?, ?, NULL, 'mock', ?, 99.00, 'USD', 'succeeded', 'demo-ok-attempt',
                                    NULL, ?, ?)
                            """,
                            [attempt_id, org_id, paid_invoice_id, ok_key, now, now],
                        )
                    _count(entities, "payment_attempts_succeeded")

                    if _table_exists(conn, "app_payment"):
                        pay = conn.execute(
                            "SELECT id FROM app_payment WHERE payment_attempt_id = ?",
                            [attempt_id],
                        ).fetchone()
                        if pay:
                            payment_id = int(pay[0])
                        else:
                            payment_id = _next_id(conn, "app_payment")
                            conn.execute(
                                """
                                INSERT INTO app_payment
                                    (id, organization_id, payment_attempt_id, provider_code, amount, currency,
                                     status, provider_payment_id, settled_at, reconciled_at, created_at, updated_at)
                                VALUES (?, ?, ?, 'mock', 99.00, 'USD', 'reconciled', 'demo-pay-ok', ?, ?, ?, ?)
                                """,
                                [payment_id, org_id, attempt_id, now, now, now, now],
                            )
                        _count(entities, "payments")

                        if _table_exists(conn, "app_payment_allocation"):
                            if not conn.execute(
                                "SELECT 1 FROM app_payment_allocation WHERE payment_id = ? AND invoice_id = ?",
                                [payment_id, paid_invoice_id],
                            ).fetchone():
                                alloc_id = _next_id(conn, "app_payment_allocation")
                                conn.execute(
                                    """
                                    INSERT INTO app_payment_allocation
                                        (id, payment_id, invoice_id, organization_id, amount, created_at)
                                    VALUES (?, ?, ?, ?, 99.00, ?)
                                    """,
                                    [alloc_id, payment_id, paid_invoice_id, org_id, now],
                                )
                                _count(entities, "payment_allocations")
                except Exception:
                    skipped.append("payment_succeeded")

            # Ledger entries
            if _table_exists(conn, "app_billing_ledger_entry") and paid_invoice_id:
                try:
                    for entry_type, ref_type, ref_id, amount, desc in [
                        (
                            "invoice_issued",
                            "invoice",
                            paid_invoice_id,
                            99.00,
                            "[SYNTHETIC] demo_seed invoice issued",
                        ),
                        (
                            "payment_received",
                            "invoice",
                            paid_invoice_id,
                            99.00,
                            "[SYNTHETIC] demo_seed payment received",
                        ),
                    ]:
                        exists = conn.execute(
                            """
                            SELECT 1 FROM app_billing_ledger_entry
                            WHERE organization_id = ? AND entry_type = ? AND reference_id = ?
                              AND description LIKE '%demo_seed%'
                            """,
                            [org_id, entry_type, ref_id],
                        ).fetchone()
                        if not exists:
                            lid = _next_id(conn, "app_billing_ledger_entry")
                            conn.execute(
                                """
                                INSERT INTO app_billing_ledger_entry
                                    (id, organization_id, entry_type, reference_type, reference_id,
                                     amount, currency, description, created_at)
                                VALUES (?, ?, ?, ?, ?, ?, 'USD', ?, ?)
                                """,
                                [lid, org_id, entry_type, ref_type, ref_id, amount, desc, now],
                            )
                        _count(entities, "ledger_entries")
                except Exception:
                    skipped.append("billing_ledger")
        elif billing_profile_id:
            skipped.append("app_invoice")

        # ── Artists (3) + catalog (4 assets, 2 releases) + rights ────────
        artist_ids: list[int] = []
        asset_ids: list[int] = []
        release_ids: list[int] = []

        artist_defs = [
            ("Luna del Pacífico (Synthetic)", "luna del pacifico synthetic"),
            ("Andes Beat Project (Demo)", "andes beat project demo"),
            ("Equinox Voices (Synthetic)", "equinox voices synthetic"),
        ]
        if _table_exists(conn, "app_artist_profile"):
            for display, normalized in artist_defs:
                try:
                    art = conn.execute(
                        "SELECT id FROM app_artist_profile WHERE display_name = ? AND organization_id = ?",
                        [display, org_id],
                    ).fetchone()
                    if art:
                        aid = int(art[0])
                    else:
                        aid = _next_id(conn, "app_artist_profile")
                        conn.execute(
                            """
                            INSERT INTO app_artist_profile
                                (id, organization_id, display_name, legal_name, normalized_name,
                                 status, warehouse_artist_id, created_by, created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, 'active', NULL, ?, ?, ?)
                            """,
                            [aid, org_id, display, display, normalized, admin_id, now, now],
                        )
                        _count(entities, "artists")
                    artist_ids.append(aid)
                except Exception:
                    skipped.append(f"artist:{normalized[:20]}")
        else:
            skipped.append("app_artist_profile")

        asset_defs = [
            ("Mar de Guayas Track (Synthetic)", 0),
            ("Sierra Pulse Single (Demo)", 0),
            ("Equinox Intro Asset (Synthetic)", 2),
            ("Andes Radio Edit (Demo)", 1),
        ]
        if artist_ids and _table_exists(conn, "app_catalog_asset"):
            for title, artist_idx in asset_defs:
                try:
                    asset = conn.execute(
                        "SELECT id FROM app_catalog_asset WHERE title = ? AND organization_id = ?",
                        [title, org_id],
                    ).fetchone()
                    artist_ref = artist_ids[min(artist_idx, len(artist_ids) - 1)]
                    if asset:
                        asid = int(asset[0])
                    else:
                        asid = _next_id(conn, "app_catalog_asset")
                        conn.execute(
                            """
                            INSERT INTO app_catalog_asset
                                (id, organization_id, title, status, warehouse_track_id,
                                 artist_profile_id, created_by, created_at, updated_at)
                            VALUES (?, ?, ?, 'active', NULL, ?, ?, ?, ?)
                            """,
                            [asid, org_id, title, artist_ref, admin_id, now, now],
                        )
                        _count(entities, "catalog_assets")
                    asset_ids.append(asid)
                except Exception:
                    skipped.append(f"catalog_asset:{title[:20]}")
        elif not artist_ids:
            skipped.append("app_catalog_asset_no_artists")
        else:
            skipped.append("app_catalog_asset")

        release_defs = [
            "VOXMETRIKS Demo EP Vol.1 (Synthetic)",
            "Equinoccio Singles Bundle (Demo)",
        ]
        if _table_exists(conn, "app_catalog_release"):
            for title in release_defs:
                try:
                    rel = conn.execute(
                        "SELECT id FROM app_catalog_release WHERE title = ? AND organization_id = ?",
                        [title, org_id],
                    ).fetchone()
                    if rel:
                        rid = int(rel[0])
                    else:
                        rid = _next_id(conn, "app_catalog_release")
                        conn.execute(
                            """
                            INSERT INTO app_catalog_release
                                (id, organization_id, title, warehouse_album_id, created_by, created_at, updated_at)
                            VALUES (?, ?, ?, NULL, ?, ?, ?)
                            """,
                            [rid, org_id, title, admin_id, now, now],
                        )
                        _count(entities, "catalog_releases")
                    release_ids.append(rid)
                except Exception:
                    skipped.append(f"catalog_release:{title[:20]}")
        else:
            skipped.append("app_catalog_release")

        # Rights contracts for first two assets + one resolved conflict
        if asset_ids and _table_exists(conn, "app_rights_contract"):
            for asid in asset_ids[:2]:
                try:
                    rc = conn.execute(
                        "SELECT id FROM app_rights_contract WHERE asset_id = ? AND organization_id = ?",
                        [asid, org_id],
                    ).fetchone()
                    if not rc:
                        rc_id = _next_id(conn, "app_rights_contract")
                        conn.execute(
                            """
                            INSERT INTO app_rights_contract
                                (id, organization_id, asset_id, rights_type, status, exclusive,
                                 valid_from, valid_to, evidence_ref, created_by, created_at, updated_at)
                            VALUES (?, ?, ?, 'master', 'active', FALSE, CURRENT_DATE, NULL,
                                    '[SYNTHETIC] demo_seed rights — not a legal license', ?, ?, ?)
                            """,
                            [rc_id, org_id, asid, admin_id, now, now],
                        )
                    _count(entities, "rights_contracts")
                except Exception:
                    skipped.append("rights_contract")

            if _table_exists(conn, "app_rights_conflict"):
                try:
                    conflict_asset = asset_ids[0]
                    cf = conn.execute(
                        """
                        SELECT id FROM app_rights_conflict
                        WHERE organization_id = ? AND asset_id = ?
                          AND details LIKE '%demo_seed%'
                        """,
                        [org_id, conflict_asset],
                    ).fetchone()
                    if not cf:
                        cf_id = _next_id(conn, "app_rights_conflict")
                        conn.execute(
                            """
                            INSERT INTO app_rights_conflict
                                (id, organization_id, asset_id, rights_type, territory_code, status,
                                 details, resolved_by, resolved_at, created_at, updated_at)
                            VALUES (?, ?, ?, 'master', 'EC', 'resolved',
                                    '[SYNTHETIC] demo_seed overlapping claim resolved academically',
                                    ?, ?, ?, ?)
                            """,
                            [cf_id, org_id, conflict_asset, admin_id, now, now, now],
                        )
                    _count(entities, "rights_conflicts")
                except Exception:
                    skipped.append("rights_conflict")
        elif not asset_ids:
            skipped.append("app_rights_contract_no_assets")
        else:
            skipped.append("app_rights_contract")

        # ── Campaigns: 1 active + 1 completed with budget/expense/results ─
        primary_artist = artist_ids[0] if artist_ids else None
        primary_release = release_ids[0] if release_ids else None
        campaign_defs = [
            (
                "LatAm Streaming Push (Synthetic)",
                "active",
                2500.00,
                800.00,
                "streams",
                120000.0,
            ),
            (
                "Equinoccio Launch Completed (Demo)",
                "completed",
                1800.00,
                1750.00,
                "playlist_adds",
                420.0,
            ),
        ]
        if _table_exists(conn, "app_campaign"):
            for name, status, budget_amt, expense_amt, metric, metric_val in campaign_defs:
                try:
                    camp = conn.execute(
                        "SELECT id FROM app_campaign WHERE name = ? AND organization_id = ?",
                        [name, org_id],
                    ).fetchone()
                    if camp:
                        campaign_id = int(camp[0])
                    else:
                        campaign_id = _next_id(conn, "app_campaign")
                        conn.execute(
                            """
                            INSERT INTO app_campaign
                                (id, organization_id, name, status, market, segment,
                                 start_date, end_date, artist_profile_id, catalog_release_id,
                                 created_by, created_at, updated_at)
                            VALUES (?, ?, ?, ?, 'EC/LATAM', 'demo_seed',
                                    CURRENT_DATE - INTERVAL 45 DAY,
                                    CASE WHEN ? = 'completed' THEN CURRENT_DATE - INTERVAL 5 DAY ELSE NULL END,
                                    ?, ?, ?, ?, ?)
                            """,
                            [
                                campaign_id,
                                org_id,
                                name,
                                status,
                                status,
                                primary_artist,
                                primary_release,
                                admin_id,
                                now,
                                now,
                            ],
                        )
                    _count(entities, "campaigns")

                    if _table_exists(conn, "app_campaign_budget"):
                        if not conn.execute(
                            "SELECT 1 FROM app_campaign_budget WHERE campaign_id = ?",
                            [campaign_id],
                        ).fetchone():
                            bid = _next_id(conn, "app_campaign_budget")
                            conn.execute(
                                """
                                INSERT INTO app_campaign_budget
                                    (id, campaign_id, organization_id, amount, currency, created_at, updated_at)
                                VALUES (?, ?, ?, ?, 'USD', ?, ?)
                                """,
                                [bid, campaign_id, org_id, budget_amt, now, now],
                            )
                        _count(entities, "campaign_budgets")

                    if _table_exists(conn, "app_campaign_expense"):
                        cat = f"demo_ads_{status}"
                        if not conn.execute(
                            "SELECT 1 FROM app_campaign_expense WHERE campaign_id = ? AND category = ?",
                            [campaign_id, cat],
                        ).fetchone():
                            eid = _next_id(conn, "app_campaign_expense")
                            conn.execute(
                                """
                                INSERT INTO app_campaign_expense
                                    (id, campaign_id, organization_id, amount, currency, category,
                                     description, expense_date, recorded_by, created_at, updated_at)
                                VALUES (?, ?, ?, ?, 'USD', ?,
                                        '[SYNTHETIC] demo_seed campaign spend', CURRENT_DATE, ?, ?, ?)
                                """,
                                [eid, campaign_id, org_id, expense_amt, cat, admin_id, now, now],
                            )
                        _count(entities, "campaign_expenses")

                    if _table_exists(conn, "app_campaign_result"):
                        if not conn.execute(
                            "SELECT 1 FROM app_campaign_result WHERE campaign_id = ? AND metric_code = ?",
                            [campaign_id, metric],
                        ).fetchone():
                            rid = _next_id(conn, "app_campaign_result")
                            conn.execute(
                                """
                                INSERT INTO app_campaign_result
                                    (id, campaign_id, organization_id, metric_code, value, unit,
                                     is_monetary, period_start, period_end, source_label,
                                     recorded_at, created_at, updated_at)
                                VALUES (?, ?, ?, ?, ?, 'count', FALSE, CURRENT_DATE - INTERVAL 30 DAY,
                                        CURRENT_DATE, 'demo_seed', ?, ?, ?)
                                """,
                                [rid, campaign_id, org_id, metric, metric_val, now, now, now],
                            )
                        _count(entities, "campaign_results")
                except Exception:
                    skipped.append(f"campaign:{status}")
        else:
            skipped.append("app_campaign")

        # ── Customer success ──────────────────────────────────────────────
        if _table_exists(conn, "app_customer_onboarding"):
            try:
                ob = conn.execute(
                    "SELECT id FROM app_customer_onboarding WHERE organization_id = ?", [org_id]
                ).fetchone()
                if not ob:
                    oid = _next_id(conn, "app_customer_onboarding")
                    conn.execute(
                        """
                        INSERT INTO app_customer_onboarding
                            (id, organization_id, status, started_at, completed_at, created_by, created_at, updated_at)
                        VALUES (?, ?, 'in_progress', ?, NULL, ?, ?, ?)
                        """,
                        [oid, org_id, now, admin_id, now, now],
                    )
                    if _table_exists(conn, "app_customer_onboarding_step"):
                        for i, (code, title) in enumerate(
                            [
                                ("kickoff", "Kickoff call (Synthetic)"),
                                ("training", "User training (Demo)"),
                                ("data_connect", "Data connectors (Synthetic)"),
                            ]
                        ):
                            sid = _next_id(conn, "app_customer_onboarding_step")
                            conn.execute(
                                """
                                INSERT INTO app_customer_onboarding_step
                                    (id, onboarding_id, step_code, title, status, blocked_reason, completed_at, sort_order)
                                VALUES (?, ?, ?, ?, ?, NULL, ?, ?)
                                """,
                                [
                                    sid,
                                    oid,
                                    code,
                                    title,
                                    "completed" if i == 0 else "pending",
                                    now if i == 0 else None,
                                    i,
                                ],
                            )
                            _count(entities, "onboarding_steps")
                    entities["onboarding"] = 1
                else:
                    entities["onboarding"] = 1
            except Exception:
                skipped.append("customer_onboarding")
        else:
            skipped.append("app_customer_onboarding")

        if _table_exists(conn, "app_customer_health_snapshot"):
            try:
                defn = None
                if _table_exists(conn, "app_customer_health_definition"):
                    defn = conn.execute(
                        "SELECT id FROM app_customer_health_definition WHERE status = 'active' ORDER BY version DESC LIMIT 1"
                    ).fetchone()
                if defn:
                    hs = conn.execute(
                        "SELECT id FROM app_customer_health_snapshot WHERE organization_id = ?",
                        [org_id],
                    ).fetchone()
                    if not hs:
                        hid = _next_id(conn, "app_customer_health_snapshot")
                        conn.execute(
                            """
                            INSERT INTO app_customer_health_snapshot
                                (id, organization_id, definition_id, score, score_state, confidence,
                                 components_json, limitations, generated_at, generated_by)
                            VALUES (?, ?, ?, 0.82, 'healthy', 0.75,
                                    '{"subscription_active":{"value":1.0},"open_risks":{"value":0.7}}',
                                    '[SYNTHETIC] Rule-based demo_seed health — not AI.', ?, ?)
                            """,
                            [hid, org_id, int(defn[0]), now, admin_id],
                        )
                    entities["health_snapshot"] = 1
                else:
                    skipped.append("health_definition_missing")
            except Exception:
                skipped.append("customer_health_snapshot")
        else:
            skipped.append("app_customer_health_snapshot")

        risk_id: int | None = None
        if _table_exists(conn, "app_customer_risk"):
            try:
                risk = conn.execute(
                    "SELECT id FROM app_customer_risk WHERE organization_id = ? AND title = ?",
                    [org_id, "Adoption Lag Risk (Synthetic)"],
                ).fetchone()
                if risk:
                    risk_id = int(risk[0])
                else:
                    risk_id = _next_id(conn, "app_customer_risk")
                    conn.execute(
                        """
                        INSERT INTO app_customer_risk
                            (id, organization_id, title, status, severity, description, created_by, created_at, updated_at)
                        VALUES (?, ?, 'Adoption Lag Risk (Synthetic)', 'intervention_required', 'medium',
                                '[SYNTHETIC] demo_seed churn risk for walkthrough', ?, ?, ?)
                        """,
                        [risk_id, org_id, admin_id, now, now],
                    )
                entities["customer_risk"] = 1
            except Exception:
                skipped.append("customer_risk")
                risk_id = None
        else:
            skipped.append("app_customer_risk")

        if risk_id and _table_exists(conn, "app_customer_intervention"):
            try:
                if not conn.execute(
                    "SELECT 1 FROM app_customer_intervention WHERE organization_id = ? AND risk_id = ?",
                    [org_id, risk_id],
                ).fetchone():
                    iid = _next_id(conn, "app_customer_intervention")
                    conn.execute(
                        """
                        INSERT INTO app_customer_intervention
                            (id, organization_id, risk_id, title, status, assignee_user_id,
                             completed_at, created_at, updated_at)
                        VALUES (?, ?, ?, 'Success Check-in (Demo)', 'in_progress', ?, NULL, ?, ?)
                        """,
                        [iid, org_id, risk_id, admin_id, now, now],
                    )
                entities["customer_intervention"] = 1
            except Exception:
                skipped.append("customer_intervention")
        elif risk_id:
            skipped.append("app_customer_intervention")

        if _table_exists(conn, "app_renewal_readiness"):
            try:
                rr = conn.execute(
                    "SELECT id FROM app_renewal_readiness WHERE organization_id = ?", [org_id]
                ).fetchone()
                if not rr:
                    rid = _next_id(conn, "app_renewal_readiness")
                    conn.execute(
                        """
                        INSERT INTO app_renewal_readiness
                            (id, organization_id, readiness_state, score, notes, evaluated_at, evaluated_by)
                        VALUES (?, ?, 'ready', 0.78, '[SYNTHETIC] demo_seed renewal readiness', ?, ?)
                        """,
                        [rid, org_id, now, admin_id],
                    )
                entities["renewal_readiness"] = 1
            except Exception:
                skipped.append("renewal_readiness")
        else:
            skipped.append("app_renewal_readiness")

        if _table_exists(conn, "app_expansion_opportunity"):
            try:
                eo = conn.execute(
                    """
                    SELECT id FROM app_expansion_opportunity
                    WHERE organization_id = ? AND title = ?
                    """,
                    [org_id, "Enterprise seats expansion (Synthetic)"],
                ).fetchone()
                if not eo:
                    eid = _next_id(conn, "app_expansion_opportunity")
                    conn.execute(
                        """
                        INSERT INTO app_expansion_opportunity
                            (id, organization_id, title, status, estimated_value, notes, created_by, created_at, updated_at)
                        VALUES (?, ?, 'Enterprise seats expansion (Synthetic)', 'identified', 297.00,
                                '[SYNTHETIC] demo_seed expansion opportunity', ?, ?, ?)
                        """,
                        [eid, org_id, admin_id, now, now],
                    )
                entities["expansion_opportunity"] = 1
            except Exception:
                skipped.append("expansion_opportunity")
        else:
            skipped.append("app_expansion_opportunity")

        # ── Support: 1 open + 1 resolved with messages ────────────────────
        if _table_exists(conn, "app_support_case"):
            support_defs = [
                ("Billing clarification (Synthetic)", "open", "billing", "normal", False),
                ("Onboarding connector resolved (Demo)", "resolved", "onboarding", "high", True),
            ]
            for subject, status, category, priority, with_messages in support_defs:
                try:
                    sc = conn.execute(
                        "SELECT id FROM app_support_case WHERE subject = ? AND organization_id = ?",
                        [subject, org_id],
                    ).fetchone()
                    if sc:
                        cid = int(sc[0])
                    else:
                        cid = _next_id(conn, "app_support_case")
                        resolved_at = now if status == "resolved" else None
                        conn.execute(
                            """
                            INSERT INTO app_support_case
                                (id, organization_id, subject, category, priority, status,
                                 requester_user_id, assignee_user_id, resolved_at, closed_at,
                                 created_at, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?)
                            """,
                            [
                                cid,
                                org_id,
                                subject,
                                category,
                                priority,
                                status,
                                admin_id,
                                admin_id,
                                resolved_at,
                                now,
                                now,
                            ],
                        )
                    _count(entities, "support_cases")

                    if with_messages and _table_exists(conn, "app_support_message"):
                        if not conn.execute(
                            "SELECT 1 FROM app_support_message WHERE case_id = ?", [cid]
                        ).fetchone():
                            mid = _next_id(conn, "app_support_message")
                            conn.execute(
                                """
                                INSERT INTO app_support_message
                                    (id, case_id, author_user_id, body, is_internal, created_at)
                                VALUES (?, ?, ?, '[SYNTHETIC] Customer-visible demo_seed message', FALSE, ?)
                                """,
                                [mid, cid, admin_id, now],
                            )
                            mid2 = _next_id(conn, "app_support_message")
                            conn.execute(
                                """
                                INSERT INTO app_support_message
                                    (id, case_id, author_user_id, body, is_internal, created_at)
                                VALUES (?, ?, ?, '[SYNTHETIC] Internal note — staff only (demo_seed)', TRUE, ?)
                                """,
                                [mid2, cid, admin_id, now],
                            )
                            mid3 = _next_id(conn, "app_support_message")
                            conn.execute(
                                """
                                INSERT INTO app_support_message
                                    (id, case_id, author_user_id, body, is_internal, created_at)
                                VALUES (?, ?, ?, '[SYNTHETIC] Resolution confirmation for customer', FALSE, ?)
                                """,
                                [mid3, cid, admin_id, now],
                            )
                        _count(entities, "support_messages", 3)
                except Exception:
                    skipped.append(f"support_case:{status}")
        else:
            skipped.append("app_support_case")

        # ── Reporting + business decision + action ────────────────────────
        if _table_exists(conn, "app_report_definition"):
            try:
                rd = conn.execute(
                    "SELECT id FROM app_report_definition WHERE code = 'demo-exec' AND organization_id = ?",
                    [org_id],
                ).fetchone()
                if rd:
                    def_id = int(rd[0])
                else:
                    def_id = _next_id(conn, "app_report_definition")
                    conn.execute(
                        """
                        INSERT INTO app_report_definition
                            (id, organization_id, code, title, description, status, default_period,
                             created_by, created_at, updated_at)
                        VALUES (?, ?, 'demo-exec', 'VOXMETRIKS Demo Executive Report (Synthetic)',
                                '[SYNTHETIC] demo_seed report definition', 'active', 'last_30d', ?, ?, ?)
                        """,
                        [def_id, org_id, admin_id, now, now],
                    )
                entities["report_definition"] = 1

                gen_id = None
                snap_id = None
                if _table_exists(conn, "app_report_generation") and _table_exists(
                    conn, "app_report_snapshot"
                ):
                    gen = conn.execute(
                        "SELECT id, snapshot_id FROM app_report_generation WHERE definition_id = ? AND organization_id = ?",
                        [def_id, org_id],
                    ).fetchone()
                    if gen:
                        gen_id, snap_id = int(gen[0]), gen[1]
                    else:
                        gen_id = _next_id(conn, "app_report_generation")
                        snap_id = _next_id(conn, "app_report_snapshot")
                        payload = {
                            "organization_id": org_id,
                            "definition_code": "demo-exec",
                            "kpis": [{"code": "streams", "label": "Streams (Demo)", "value": 120000}],
                            "campaigns": {"count": 2, "roi_status": "No disponible"},
                            "generated_label": "synthetic_demo_seed",
                        }
                        limitations = (
                            "[SYNTHETIC] Immutable demo_seed snapshot. Not certified. ROI may be unavailable."
                        )
                        conn.execute(
                            """
                            INSERT INTO app_report_snapshot
                                (id, organization_id, generation_id, definition_id, payload_json,
                                 kpi_versions_json, unavailable_sources_json, limitations,
                                 generated_at, generated_by)
                            VALUES (?, ?, ?, ?, ?, '[]', '["roi"]', ?, ?, ?)
                            """,
                            [
                                snap_id,
                                org_id,
                                gen_id,
                                def_id,
                                json.dumps(payload),
                                limitations,
                                now,
                                admin_id,
                            ],
                        )
                        conn.execute(
                            """
                            INSERT INTO app_report_generation
                                (id, organization_id, definition_id, status, period_start, period_end,
                                 filters_json, requested_by, requested_at, completed_at, error_message, snapshot_id)
                            VALUES (?, ?, ?, 'ready', NULL, NULL, '{}', ?, ?, ?, NULL, ?)
                            """,
                            [gen_id, org_id, def_id, admin_id, now, now, snap_id],
                        )
                    entities["report_generation"] = 1
                    entities["report_snapshot"] = 1

                    if (
                        gen_id
                        and snap_id
                        and _table_exists(conn, "app_executive_report")
                    ):
                        er = conn.execute(
                            "SELECT id FROM app_executive_report WHERE definition_id = ? AND organization_id = ?",
                            [def_id, org_id],
                        ).fetchone()
                        if er:
                            exec_id = int(er[0])
                        else:
                            exec_id = _next_id(conn, "app_executive_report")
                            conn.execute(
                                """
                                INSERT INTO app_executive_report
                                    (id, organization_id, definition_id, generation_id, snapshot_id,
                                     title, status, period_start, period_end, published_at, archived_at,
                                     created_by, created_at, updated_at)
                                VALUES (?, ?, ?, ?, ?, 'VOXMETRIKS Demo Executive Report (Synthetic)',
                                        'published', NULL, NULL, ?, NULL, ?, ?, ?)
                                """,
                                [
                                    exec_id,
                                    org_id,
                                    def_id,
                                    gen_id,
                                    snap_id,
                                    now,
                                    admin_id,
                                    now,
                                    now,
                                ],
                            )
                        entities["executive_report"] = 1

                        if _table_exists(conn, "app_business_decision"):
                            dec = conn.execute(
                                "SELECT id FROM app_business_decision WHERE title = ? AND organization_id = ?",
                                ["Scale LatAm campaign investment (Synthetic)", org_id],
                            ).fetchone()
                            if dec:
                                did = int(dec[0])
                            else:
                                did = _next_id(conn, "app_business_decision")
                                conn.execute(
                                    """
                                    INSERT INTO app_business_decision
                                        (id, organization_id, executive_report_id, title, proposal, status,
                                         evidence_refs_json, created_by, created_at, updated_at, completed_at)
                                    VALUES (?, ?, ?, 'Scale LatAm campaign investment (Synthetic)',
                                            '[SYNTHETIC] Expand demo market presence based on report snapshot',
                                            'approved', '[]', ?, ?, ?, NULL)
                                    """,
                                    [did, org_id, exec_id, admin_id, now, now],
                                )
                            entities["business_decision"] = 1

                            if _table_exists(conn, "app_decision_action"):
                                act = conn.execute(
                                    "SELECT id FROM app_decision_action WHERE decision_id = ? AND title = ?",
                                    [did, "Brief campaign owners (Demo)"],
                                ).fetchone()
                                if not act:
                                    aid = _next_id(conn, "app_decision_action")
                                    conn.execute(
                                        """
                                        INSERT INTO app_decision_action
                                            (id, decision_id, title, status, assignee_user_id,
                                             due_at, completed_at, created_at, updated_at)
                                        VALUES (?, ?, 'Brief campaign owners (Demo)', 'planned', ?,
                                                NULL, NULL, ?, ?)
                                        """,
                                        [aid, did, admin_id, now, now],
                                    )
                                entities["decision_action"] = 1
                            else:
                                skipped.append("app_decision_action")
                        else:
                            skipped.append("app_business_decision")
                    else:
                        skipped.append("app_executive_report")
                else:
                    skipped.append("app_report_generation_or_snapshot")
            except Exception:
                skipped.append("reporting_chain")
        else:
            skipped.append("app_report_definition")

        result["seeded"] = True
        # Normalized count helpers for callers expecting totals
        entities["prospect_ids"] = prospect_ids
        entities["opportunity_ids"] = opportunity_ids
        entities["artist_ids"] = artist_ids
        entities["asset_ids"] = asset_ids
        entities["release_ids"] = release_ids

    return result


def _configure_stdio() -> None:
    """Avoid UnicodeEncodeError on Windows cp1252 consoles."""
    for stream in (sys.stdout, sys.stderr):
        reconf = getattr(stream, "reconfigure", None)
        if callable(reconf):
            try:
                reconf(encoding="utf-8", errors="replace")
            except Exception:
                pass


def main() -> int:
    _configure_stdio()

    if os.getenv("VOXMETRIKS_SEED_ENTERPRISE_DEMO", "").strip() not in ("1", "true", "yes", "on"):
        print(
            "Enterprise demo seed skipped. Set VOXMETRIKS_SEED_ENTERPRISE_DEMO=1 to run.",
            file=sys.stderr,
        )
        return 0

    print(_DEMO_BANNER)
    outcome = seed_enterprise_demo()
    if outcome["seeded"]:
        print("DEMO seed complete (synthetic):")
        for k, v in outcome.items():
            if k != "skipped":
                print(f"  {k}={v}")
        if outcome.get("skipped"):
            print("  skipped:", outcome["skipped"])
    else:
        print("DEMO seed: nothing inserted.", outcome.get("skipped"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
