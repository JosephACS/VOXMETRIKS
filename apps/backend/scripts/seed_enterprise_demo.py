"""Optional enterprise demo seed — Spec 028 polish.

Run explicitly only when ``VOXMETRIKS_SEED_ENTERPRISE_DEMO=1``:

    VOXMETRIKS_SEED_ENTERPRISE_DEMO=1 python scripts/seed_enterprise_demo.py

Never executes on import. All records are synthetic / demo.
Safe when tables are missing (skips gracefully). Does not touch warehouse facts.
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
╔══════════════════════════════════════════════════════════════════╗
║  VOXMETRIKS ENTERPRISE DEMO SEED — SYNTHETIC / ACADEMIC DATA     ║
║  Opt-in only. Not for production or compliance.                   ║
╚══════════════════════════════════════════════════════════════════╝
"""


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


def seed_enterprise_demo() -> dict[str, object]:
    from app.core.database import using_write_conn
    from app.core.time_util import utc_now

    result: dict[str, object] = {
        "seeded": False,
        "organization_id": None,
        "plan_id": None,
        "subscription_id": None,
        "entities": {},
        "skipped": [],
    }

    with using_write_conn() as conn:
        now = utc_now()

        if not _table_exists(conn, "app_user"):
            result["skipped"].append("app_user")
            return result

        admin = conn.execute(
            "SELECT id FROM app_user WHERE username = 'admin' OR email LIKE '%admin%' LIMIT 1"
        ).fetchone()
        if not admin:
            result["skipped"].append("admin_user")
            return result
        admin_id = int(admin[0])

        # ── Organization ──────────────────────────────────────────────────
        org_id: int | None = None
        if _table_exists(conn, "app_organization"):
            existing = conn.execute(
                "SELECT id FROM app_organization WHERE slug = 'enterprise-demo-s028'"
            ).fetchone()
            if existing:
                org_id = int(existing[0])
            else:
                org_id = _next_id(conn, "app_organization")
                cols = "id, display_name, slug, organization_type, country_code, timezone, default_currency, status, created_by, created_at, updated_at"
                vals = "?, 'Enterprise Demo Org (Synthetic)', 'enterprise-demo-s028', 'label', 'US', 'UTC', 'USD', 'active', ?, ?, ?"
                params: list = [org_id, admin_id, now, now]
                if _has_column(conn, "app_organization", "is_demo"):
                    cols += ", is_demo"
                    vals += ", TRUE"
                conn.execute(f"INSERT INTO app_organization ({cols}) VALUES ({vals})", params)
            result["organization_id"] = org_id

            if _table_exists(conn, "app_organization_member"):
                member = conn.execute(
                    "SELECT id FROM app_organization_member WHERE organization_id = ? AND user_id = ?",
                    [org_id, admin_id],
                ).fetchone()
                if not member:
                    mid = _next_id(conn, "app_organization_member")
                    conn.execute(
                        """
                        INSERT INTO app_organization_member
                            (id, organization_id, user_id, status, created_by, created_at, updated_at)
                        VALUES (?, ?, ?, 'active', ?, ?, ?)
                        """,
                        [mid, org_id, admin_id, admin_id, now, now],
                    )
                    member_id = mid
                else:
                    member_id = int(member[0])
                if _table_exists(conn, "app_business_role") and _table_exists(conn, "app_member_role"):
                    owner = conn.execute(
                        "SELECT id FROM app_business_role WHERE code = 'owner'"
                    ).fetchone()
                    if owner and not conn.execute(
                        "SELECT 1 FROM app_member_role WHERE member_id = ? AND role_id = ? AND status = 'active'",
                        [member_id, int(owner[0])],
                    ).fetchone():
                        mrid = _next_id(conn, "app_member_role")
                        conn.execute(
                            """
                            INSERT INTO app_member_role
                                (id, member_id, role_id, status, assigned_by, assigned_at)
                            VALUES (?, ?, ?, 'active', ?, ?)
                            """,
                            [mrid, member_id, int(owner[0]), admin_id, now],
                        )
        else:
            result["skipped"].append("app_organization")
            return result

        assert org_id is not None

        # ── Plan + subscription (commercial Professional $99 monthly) ─────
        plan_id: int | None = None
        price_id: int | None = None
        if _table_exists(conn, "app_plan"):
            from app.packages.subscriptions.application.commercial_catalog import (
                ensure_commercial_catalog,
                get_active_price_id,
            )

            ensure_commercial_catalog(conn)
            plan_row = conn.execute(
                "SELECT id FROM app_plan WHERE code = 'professional' AND status = 'active'"
            ).fetchone()
            if plan_row:
                plan_id = int(plan_row[0])
            result["plan_id"] = plan_id
            if plan_id and _table_exists(conn, "app_plan_price"):
                price_id = get_active_price_id(
                    conn, plan_code="professional", billing_period="monthly", currency="USD"
                )
                if price_id is None:
                    # Fallback create should not be needed after ensure_commercial_catalog
                    price_id = _next_id(conn, "app_plan_price")
                    conn.execute(
                        """
                        INSERT INTO app_plan_price
                            (id, plan_id, currency, billing_period, amount, status, created_at, updated_at)
                        VALUES (?, ?, 'USD', 'monthly', 99.00, 'active', ?, ?)
                        """,
                        [price_id, plan_id, now, now],
                    )
                result["plan_price_id"] = price_id
        else:
            result["skipped"].append("app_plan")

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
                price_id = result.get("plan_price_id")
                conn.execute(
                    """
                    INSERT INTO app_subscription
                        (id, organization_id, plan_id, plan_price_id, status, billing_currency,
                         activation_source, access_state, created_at, updated_at)
                    VALUES (?, ?, ?, ?, 'active', 'USD', 'demo_seed_synthetic', 'full', ?, ?)
                    """,
                    [sub_id, org_id, plan_id, price_id, now, now],
                )
            # Keep existing demo sub linked to a priced plan when possible
            if sub_id and result.get("plan_price_id"):
                conn.execute(
                    """
                    UPDATE app_subscription
                    SET plan_price_id = COALESCE(plan_price_id, ?),
                        status = CASE WHEN status = 'trialing' THEN 'active' ELSE status END,
                        updated_at = ?
                    WHERE id = ? AND organization_id = ?
                    """,
                    [result["plan_price_id"], now, sub_id, org_id],
                )
            result["subscription_id"] = sub_id
            result["entities"]["subscription"] = sub_id
        else:
            result["skipped"].append("app_subscription")

        # ── CRM prospect + opportunity + quotation ────────────────────────
        if _table_exists(conn, "app_crm_prospect"):
            prosp = conn.execute(
                "SELECT id FROM app_crm_prospect WHERE display_name = 'Demo Prospect (Synthetic)' AND organization_id = ?",
                [org_id],
            ).fetchone()
            if prosp:
                prospect_id = int(prosp[0])
            else:
                prospect_id = _next_id(conn, "app_crm_prospect")
                conn.execute(
                    """
                    INSERT INTO app_crm_prospect
                        (id, display_name, company_name, email, phone, source, status,
                         owner_user_id, organization_id, notes, created_at, updated_at, deleted_at)
                    VALUES (?, 'Demo Prospect (Synthetic)', 'Demo Label Co',
                            'demo.prospect@example.invalid', NULL, 'demo_seed',
                            'qualified', ?, ?, '[SYNTHETIC] demo prospect', ?, ?, NULL)
                    """,
                    [prospect_id, admin_id, org_id, now, now],
                )
            result["entities"]["prospect"] = prospect_id

            if _table_exists(conn, "app_crm_opportunity"):
                opp = conn.execute(
                    "SELECT id FROM app_crm_opportunity WHERE name = 'Demo Opportunity (Synthetic)' AND organization_id = ?",
                    [org_id],
                ).fetchone()
                if opp:
                    opportunity_id = int(opp[0])
                else:
                    opportunity_id = _next_id(conn, "app_crm_opportunity")
                    conn.execute(
                        """
                        INSERT INTO app_crm_opportunity
                            (id, prospect_id, name, description, stage, probability,
                             expected_value, currency, expected_close_date, actual_close_date,
                             outcome, owner_user_id, organization_id, created_at, updated_at, deleted_at)
                        VALUES (?, ?, 'Demo Opportunity (Synthetic)',
                                '[SYNTHETIC] demo opportunity', 'proposal', 60,
                                1000.00, 'USD', NULL, NULL, NULL, ?, ?, ?, ?, NULL)
                        """,
                        [opportunity_id, prospect_id, admin_id, org_id, now, now],
                    )
                result["entities"]["opportunity"] = opportunity_id

                if _table_exists(conn, "app_crm_quotation"):
                    quot = conn.execute(
                        "SELECT id FROM app_crm_quotation WHERE opportunity_id = ?",
                        [opportunity_id],
                    ).fetchone()
                    if quot:
                        quotation_id = int(quot[0])
                    else:
                        quotation_id = _next_id(conn, "app_crm_quotation")
                        # Discover required columns loosely
                        try:
                            conn.execute(
                                """
                                INSERT INTO app_crm_quotation
                                    (id, opportunity_id, status, currency, notes, row_version,
                                     current_version_no, created_by, created_at, updated_at, deleted_at)
                                VALUES (?, ?, 'draft', 'USD', '[SYNTHETIC] demo quotation', 1, 0, ?, ?, ?, NULL)
                                """,
                                [quotation_id, opportunity_id, admin_id, now, now],
                            )
                        except Exception:
                            result["skipped"].append("app_crm_quotation_insert")
                            quotation_id = None  # type: ignore
                    if quotation_id:
                        result["entities"]["quotation"] = quotation_id
                        # Related commercial chain: contact → version → item → accepted → contract
                        if _table_exists(conn, "app_crm_contact"):
                            ct = conn.execute(
                                "SELECT id FROM app_crm_contact WHERE email = 'demo.contact@example.invalid'"
                            ).fetchone()
                            if ct:
                                contact_id = int(ct[0])
                            else:
                                contact_id = _next_id(conn, "app_crm_contact")
                                conn.execute(
                                    """
                                    INSERT INTO app_crm_contact
                                        (id, full_name, email, email_normalized, phone, company_name,
                                         linked_user_id, created_by, created_at, updated_at, deleted_at)
                                    VALUES (?, 'Demo Contact (Synthetic)', 'demo.contact@example.invalid',
                                            'demo.contact@example.invalid', NULL, 'Demo Label Co',
                                            NULL, ?, ?, ?, NULL)
                                    """,
                                    [contact_id, admin_id, now, now],
                                )
                            result["entities"]["contact"] = contact_id
                            if _table_exists(conn, "app_crm_prospect_contact"):
                                if not conn.execute(
                                    "SELECT 1 FROM app_crm_prospect_contact WHERE prospect_id = ? AND contact_id = ?",
                                    [prospect_id, contact_id],
                                ).fetchone():
                                    conn.execute(
                                        """
                                        INSERT INTO app_crm_prospect_contact
                                            (prospect_id, contact_id, is_primary, is_decision_maker, is_signatory, added_at)
                                        VALUES (?, ?, TRUE, TRUE, TRUE, ?)
                                        """,
                                        [prospect_id, contact_id, now],
                                    )

                        if _table_exists(conn, "app_crm_quotation_version"):
                            ver = conn.execute(
                                "SELECT id FROM app_crm_quotation_version WHERE quotation_id = ?",
                                [quotation_id],
                            ).fetchone()
                            if ver:
                                version_id = int(ver[0])
                            else:
                                version_id = _next_id(conn, "app_crm_quotation_version")
                                try:
                                    conn.execute(
                                        """
                                        INSERT INTO app_crm_quotation_version
                                            (id, quotation_id, version_no, status, subtotal, discount_pct,
                                             discount_requires_approval, total, notes, is_immutable,
                                             sent_at, accepted_at, rejected_at, created_by, created_at)
                                        VALUES (?, ?, 1, 'accepted', 1000.00, 0, FALSE, 1000.00,
                                                '[SYNTHETIC] demo quotation version', TRUE, ?, ?, NULL, ?, ?)
                                        """,
                                        [version_id, quotation_id, now, now, admin_id, now],
                                    )
                                    conn.execute(
                                        "UPDATE app_crm_quotation SET status = 'accepted', current_version_no = 1, updated_at = ? WHERE id = ?",
                                        [now, quotation_id],
                                    )
                                except Exception:
                                    result["skipped"].append("app_crm_quotation_version_insert")
                                    version_id = None  # type: ignore
                            if version_id:
                                result["entities"]["quotation_version"] = version_id
                                if _table_exists(conn, "app_crm_quotation_item"):
                                    if not conn.execute(
                                        "SELECT 1 FROM app_crm_quotation_item WHERE quotation_version_id = ?",
                                        [version_id],
                                    ).fetchone():
                                        item_id = _next_id(conn, "app_crm_quotation_item")
                                        try:
                                            conn.execute(
                                                """
                                                INSERT INTO app_crm_quotation_item
                                                    (id, quotation_version_id, description, quantity, unit_price,
                                                     discount_pct, line_total, sort_order, created_at)
                                                VALUES (?, ?, '[SYNTHETIC] Enterprise starter seats', 1, 1000.00,
                                                        0, 1000.00, 1, ?)
                                                """,
                                                [item_id, version_id, now],
                                            )
                                            result["entities"]["quotation_item"] = item_id
                                        except Exception:
                                            result["skipped"].append("app_crm_quotation_item_insert")

                                if _table_exists(conn, "app_commercial_contract"):
                                    cc = conn.execute(
                                        "SELECT id FROM app_commercial_contract WHERE quotation_version_id = ?",
                                        [version_id],
                                    ).fetchone()
                                    if cc:
                                        contract_id = int(cc[0])
                                    else:
                                        contract_id = _next_id(conn, "app_commercial_contract")
                                        try:
                                            conn.execute(
                                                """
                                                INSERT INTO app_commercial_contract
                                                    (id, quotation_version_id, opportunity_id, organization_id,
                                                     legal_name, status, acceptance_evidence, accepted_at,
                                                     created_by, created_at, updated_at)
                                                VALUES (?, ?, ?, ?, 'Demo Label Co (Synthetic)', 'accepted',
                                                        '[SYNTHETIC] demo acceptance evidence', ?, ?, ?, ?)
                                                """,
                                                [contract_id, version_id, opportunity_id, org_id, now, admin_id, now, now],
                                            )
                                        except Exception:
                                            result["skipped"].append("app_commercial_contract_insert")
                                            contract_id = None  # type: ignore
                                    if contract_id:
                                        result["entities"]["commercial_contract"] = contract_id
        else:
            result["skipped"].append("app_crm_prospect")

        # ── Billing profile + invoice + mock payment ──────────────────────
        if _table_exists(conn, "app_billing_profile"):
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
                    VALUES (?, ?, 'USD', 'Enterprise Demo Org (Synthetic)', 'DEMO-TAX',
                            'Academic address', 'billing-demo@example.invalid', 'active', ?, ?)
                    """,
                    [billing_profile_id, org_id, now, now],
                )
            result["entities"]["billing_profile"] = billing_profile_id

            if _table_exists(conn, "app_invoice"):
                inv = conn.execute(
                    "SELECT id FROM app_invoice WHERE invoice_number = 'DEMO-INV-001'"
                ).fetchone()
                if inv:
                    invoice_id = int(inv[0])
                else:
                    invoice_id = _next_id(conn, "app_invoice")
                    conn.execute(
                        """
                        INSERT INTO app_invoice
                            (id, organization_id, billing_profile_id, subscription_id,
                             invoice_number, currency, status, subtotal, total,
                             amount_paid, amount_due, period_start, period_end, due_date,
                             issued_at, paid_at, voided_at, notes, created_at, updated_at)
                        VALUES (?, ?, ?, ?, 'DEMO-INV-001', 'USD', 'paid',
                                0, 0, 0, 0, NULL, NULL, NULL, ?, ?, NULL,
                                '[SYNTHETIC] demo invoice — MOCK payment path', ?, ?)
                        """,
                        [invoice_id, org_id, billing_profile_id, sub_id, now, now, now, now],
                    )
                result["entities"]["invoice"] = invoice_id

                if _table_exists(conn, "app_payment") and _table_exists(conn, "app_payment_attempt"):
                    try:
                        att = conn.execute(
                            "SELECT id FROM app_payment_attempt WHERE organization_id = ? AND invoice_id = ?",
                            [org_id, invoice_id],
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
                                VALUES (?, ?, ?, NULL, 'mock', ?, 0.01, 'USD', 'succeeded', 'demo-attempt',
                                        NULL, ?, ?)
                                """,
                                [attempt_id, org_id, invoice_id, f"demo-seed-{invoice_id}", now, now],
                            )
                        pay = conn.execute(
                            "SELECT id FROM app_payment WHERE payment_attempt_id = ?",
                            [attempt_id],
                        ).fetchone()
                        if not pay:
                            payment_id = _next_id(conn, "app_payment")
                            conn.execute(
                                """
                                INSERT INTO app_payment
                                    (id, organization_id, payment_attempt_id, provider_code, amount, currency,
                                     status, provider_payment_id, settled_at, reconciled_at, created_at, updated_at)
                                VALUES (?, ?, ?, 'mock', 0.01, 'USD', 'settled', 'demo-pay', ?, NULL, ?, ?)
                                """,
                                [payment_id, org_id, attempt_id, now, now, now],
                            )
                            result["entities"]["payment"] = payment_id
                        else:
                            result["entities"]["payment"] = int(pay[0])
                        result["entities"]["payment_attempt"] = attempt_id
                    except Exception:
                        result["skipped"].append("app_payment_insert")
        else:
            result["skipped"].append("app_billing_profile")

        # ── Artist + catalog asset + rights ───────────────────────────────
        artist_id = None
        if _table_exists(conn, "app_artist_profile"):
            art = conn.execute(
                "SELECT id FROM app_artist_profile WHERE display_name = 'Demo Artist (Synthetic)' AND organization_id = ?",
                [org_id],
            ).fetchone()
            if art:
                artist_id = int(art[0])
            else:
                artist_id = _next_id(conn, "app_artist_profile")
                conn.execute(
                    """
                    INSERT INTO app_artist_profile
                        (id, organization_id, display_name, legal_name, normalized_name,
                         status, warehouse_artist_id, created_by, created_at, updated_at)
                    VALUES (?, ?, 'Demo Artist (Synthetic)', 'Demo Artist Legal',
                            'demo artist synthetic', 'active', NULL, ?, ?, ?)
                    """,
                    [artist_id, org_id, admin_id, now, now],
                )
            result["entities"]["artist"] = artist_id

            if _table_exists(conn, "app_catalog_asset"):
                asset = conn.execute(
                    "SELECT id FROM app_catalog_asset WHERE title = 'Demo Track Asset (Synthetic)' AND organization_id = ?",
                    [org_id],
                ).fetchone()
                if asset:
                    asset_id = int(asset[0])
                else:
                    asset_id = _next_id(conn, "app_catalog_asset")
                    conn.execute(
                        """
                        INSERT INTO app_catalog_asset
                            (id, organization_id, title, status, warehouse_track_id,
                             artist_profile_id, created_by, created_at, updated_at)
                        VALUES (?, ?, 'Demo Track Asset (Synthetic)', 'active', NULL, ?, ?, ?, ?)
                        """,
                        [asset_id, org_id, artist_id, admin_id, now, now],
                    )
                result["entities"]["catalog_asset"] = asset_id

                if _table_exists(conn, "app_rights_contract"):
                    rc = conn.execute(
                        "SELECT id FROM app_rights_contract WHERE asset_id = ? AND organization_id = ?",
                        [asset_id, org_id],
                    ).fetchone()
                    if not rc:
                        rc_id = _next_id(conn, "app_rights_contract")
                        conn.execute(
                            """
                            INSERT INTO app_rights_contract
                                (id, organization_id, asset_id, rights_type, status, exclusive,
                                 valid_from, valid_to, evidence_ref, created_by, created_at, updated_at)
                            VALUES (?, ?, ?, 'master', 'active', FALSE, CURRENT_DATE, NULL,
                                    '[SYNTHETIC] demo rights — not a legal license', ?, ?, ?)
                            """,
                            [rc_id, org_id, asset_id, admin_id, now, now],
                        )
                        result["entities"]["rights_contract"] = rc_id
                    else:
                        result["entities"]["rights_contract"] = int(rc[0])
        else:
            result["skipped"].append("app_artist_profile")

        # ── Campaign ──────────────────────────────────────────────────────
        if _table_exists(conn, "app_campaign"):
            camp = conn.execute(
                "SELECT id FROM app_campaign WHERE name = 'Demo Campaign (Synthetic)' AND organization_id = ?",
                [org_id],
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
                    VALUES (?, ?, 'Demo Campaign (Synthetic)', 'active', 'LATAM', 'demo',
                            NULL, NULL, ?, NULL, ?, ?, ?)
                    """,
                    [campaign_id, org_id, artist_id, admin_id, now, now],
                )
            result["entities"]["campaign"] = campaign_id
            if _table_exists(conn, "app_campaign_budget"):
                if not conn.execute(
                    "SELECT 1 FROM app_campaign_budget WHERE campaign_id = ?", [campaign_id]
                ).fetchone():
                    try:
                        bid = _next_id(conn, "app_campaign_budget")
                        conn.execute(
                            """
                            INSERT INTO app_campaign_budget
                                (id, campaign_id, organization_id, amount, currency, created_at, updated_at)
                            VALUES (?, ?, ?, 500.00, 'USD', ?, ?)
                            """,
                            [bid, campaign_id, org_id, now, now],
                        )
                        result["entities"]["campaign_budget"] = bid
                    except Exception:
                        result["skipped"].append("app_campaign_budget_insert")
            if _table_exists(conn, "app_campaign_expense"):
                if not conn.execute(
                    "SELECT 1 FROM app_campaign_expense WHERE campaign_id = ? AND category = 'demo_ads'",
                    [campaign_id],
                ).fetchone():
                    try:
                        eid = _next_id(conn, "app_campaign_expense")
                        conn.execute(
                            """
                            INSERT INTO app_campaign_expense
                                (id, campaign_id, organization_id, amount, currency, category,
                                 description, expense_date, recorded_by, created_at, updated_at)
                            VALUES (?, ?, ?, 100.00, 'USD', 'demo_ads',
                                    '[SYNTHETIC] demo spend', CURRENT_DATE, ?, ?, ?)
                            """,
                            [eid, campaign_id, org_id, admin_id, now, now],
                        )
                        result["entities"]["campaign_expense"] = eid
                    except Exception:
                        result["skipped"].append("app_campaign_expense_insert")
        else:
            result["skipped"].append("app_campaign")

        # ── Executive report definition + generation + snapshot + decision ─
        if _table_exists(conn, "app_report_definition"):
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
                    VALUES (?, ?, 'demo-exec', 'Demo Executive Report (Synthetic)',
                            '[SYNTHETIC] demo report definition', 'active', 'last_30d', ?, ?, ?)
                    """,
                    [def_id, org_id, admin_id, now, now],
                )
            result["entities"]["report_definition"] = def_id

            if _table_exists(conn, "app_report_generation") and _table_exists(conn, "app_report_snapshot"):
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
                        "kpis": [],
                        "campaigns": {"count": 1, "roi_status": "No disponible"},
                        "generated_label": "synthetic_demo_seed",
                    }
                    limitations = (
                        "[SYNTHETIC] Immutable demo snapshot. Not certified. ROI may be unavailable."
                    )
                    conn.execute(
                        """
                        INSERT INTO app_report_snapshot
                            (id, organization_id, generation_id, definition_id, payload_json,
                             kpi_versions_json, unavailable_sources_json, limitations,
                             generated_at, generated_by)
                        VALUES (?, ?, ?, ?, ?, '[]', '["roi"]', ?, ?, ?)
                        """,
                        [snap_id, org_id, gen_id, def_id, json.dumps(payload), limitations, now, admin_id],
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
                result["entities"]["report_generation"] = gen_id
                result["entities"]["report_snapshot"] = snap_id

                if _table_exists(conn, "app_executive_report"):
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
                            VALUES (?, ?, ?, ?, ?, 'Demo Executive Report (Synthetic)', 'published',
                                    NULL, NULL, ?, NULL, ?, ?, ?)
                            """,
                            [exec_id, org_id, def_id, gen_id, snap_id, now, admin_id, now, now],
                        )
                    result["entities"]["executive_report"] = exec_id

                    if _table_exists(conn, "app_business_decision"):
                        dec = conn.execute(
                            "SELECT id FROM app_business_decision WHERE title = 'Demo Decision (Synthetic)' AND organization_id = ?",
                            [org_id],
                        ).fetchone()
                        if not dec:
                            did = _next_id(conn, "app_business_decision")
                            conn.execute(
                                """
                                INSERT INTO app_business_decision
                                    (id, organization_id, executive_report_id, title, proposal, status,
                                     evidence_refs_json, created_by, created_at, updated_at, completed_at)
                                VALUES (?, ?, ?, 'Demo Decision (Synthetic)',
                                        '[SYNTHETIC] Expand demo market presence', 'approved',
                                        '[]', ?, ?, ?, NULL)
                                """,
                                [did, org_id, exec_id, admin_id, now, now],
                            )
                            result["entities"]["business_decision"] = did
                        else:
                            result["entities"]["business_decision"] = int(dec[0])
        else:
            result["skipped"].append("app_report_definition")

        # ── Customer success + support ────────────────────────────────────
        if _table_exists(conn, "app_customer_onboarding"):
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
                        [("kickoff", "Kickoff call"), ("training", "User training")]
                    ):
                        sid = _next_id(conn, "app_customer_onboarding_step")
                        conn.execute(
                            """
                            INSERT INTO app_customer_onboarding_step
                                (id, onboarding_id, step_code, title, status, blocked_reason, completed_at, sort_order)
                            VALUES (?, ?, ?, ?, 'pending', NULL, NULL, ?)
                            """,
                            [sid, oid, code, title, i],
                        )
                result["entities"]["onboarding"] = oid
            else:
                result["entities"]["onboarding"] = int(ob[0])

        if _table_exists(conn, "app_customer_risk"):
            risk = conn.execute(
                "SELECT id FROM app_customer_risk WHERE organization_id = ? AND title = 'Demo Risk (Synthetic)'",
                [org_id],
            ).fetchone()
            if risk:
                risk_id = int(risk[0])
            else:
                risk_id = _next_id(conn, "app_customer_risk")
                try:
                    conn.execute(
                        """
                        INSERT INTO app_customer_risk
                            (id, organization_id, title, status, severity, description, created_by, created_at, updated_at)
                        VALUES (?, ?, 'Demo Risk (Synthetic)', 'open', 'medium',
                                '[SYNTHETIC] demo churn risk for walkthrough', ?, ?, ?)
                        """,
                        [risk_id, org_id, admin_id, now, now],
                    )
                except Exception:
                    result["skipped"].append("app_customer_risk_insert")
                    risk_id = None  # type: ignore
            if risk_id:
                result["entities"]["customer_risk"] = risk_id
                if _table_exists(conn, "app_customer_intervention"):
                    if not conn.execute(
                        "SELECT 1 FROM app_customer_intervention WHERE organization_id = ? AND risk_id = ?",
                        [org_id, risk_id],
                    ).fetchone():
                        try:
                            iid = _next_id(conn, "app_customer_intervention")
                            conn.execute(
                                """
                                INSERT INTO app_customer_intervention
                                    (id, organization_id, risk_id, title, status, assignee_user_id,
                                     completed_at, created_at, updated_at)
                                VALUES (?, ?, ?, 'Demo Intervention (Synthetic)', 'planned', ?, NULL, ?, ?)
                                """,
                                [iid, org_id, risk_id, admin_id, now, now],
                            )
                            result["entities"]["customer_intervention"] = iid
                        except Exception:
                            result["skipped"].append("app_customer_intervention_insert")

        if _table_exists(conn, "app_customer_health_snapshot"):
            # Ensure definition exists via schema seed; create a snapshot
            defn = conn.execute(
                "SELECT id FROM app_customer_health_definition WHERE status = 'active' ORDER BY version DESC LIMIT 1"
            ).fetchone() if _table_exists(conn, "app_customer_health_definition") else None
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
                        VALUES (?, ?, ?, 0.8, 'healthy', 0.7,
                                '{"subscription_active":{"value":1.0}}',
                                '[SYNTHETIC] Rule-based demo health — not AI.', ?, ?)
                        """,
                        [hid, org_id, int(defn[0]), now, admin_id],
                    )
                    result["entities"]["health_snapshot"] = hid

        if _table_exists(conn, "app_support_case"):
            sc = conn.execute(
                "SELECT id FROM app_support_case WHERE subject = 'Demo Support Case (Synthetic)' AND organization_id = ?",
                [org_id],
            ).fetchone()
            if not sc:
                cid = _next_id(conn, "app_support_case")
                conn.execute(
                    """
                    INSERT INTO app_support_case
                        (id, organization_id, subject, category, priority, status,
                         requester_user_id, assignee_user_id, resolved_at, closed_at,
                         created_at, updated_at)
                    VALUES (?, ?, 'Demo Support Case (Synthetic)', 'general', 'normal', 'open',
                            ?, ?, NULL, NULL, ?, ?)
                    """,
                    [cid, org_id, admin_id, admin_id, now, now],
                )
                if _table_exists(conn, "app_support_message"):
                    mid = _next_id(conn, "app_support_message")
                    conn.execute(
                        """
                        INSERT INTO app_support_message
                            (id, case_id, author_user_id, body, is_internal, created_at)
                        VALUES (?, ?, ?, '[SYNTHETIC] Customer-visible demo message', FALSE, ?)
                        """,
                        [mid, cid, admin_id, now],
                    )
                    mid2 = _next_id(conn, "app_support_message")
                    conn.execute(
                        """
                        INSERT INTO app_support_message
                            (id, case_id, author_user_id, body, is_internal, created_at)
                        VALUES (?, ?, ?, '[SYNTHETIC] Internal note — staff only', TRUE, ?)
                        """,
                        [mid2, cid, admin_id, now],
                    )
                result["entities"]["support_case"] = cid
            else:
                result["entities"]["support_case"] = int(sc[0])

        result["seeded"] = True

    return result


def main() -> int:
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
