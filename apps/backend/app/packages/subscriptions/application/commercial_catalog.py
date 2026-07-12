"""Canonical commercial plan catalog — VOXMETRIKS.

Single source of truth for Starter / Professional / Business / Enterprise.
Billing period in DB is ``annual`` (schema CHECK); product copy may say yearly.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

import duckdb

from app.core.time_util import utc_now

# Amounts that historically appeared in demos/tests — never delete, only retire
# when active and not part of the commercial catalog.
_LEGACY_DEMO_AMOUNTS = frozenset(
    {
        Decimal("75"),
        Decimal("75.00"),
        Decimal("75.0000"),
        Decimal("100"),
        Decimal("100.00"),
        Decimal("100.0000"),
        Decimal("200"),
        Decimal("200.00"),
        Decimal("200.0000"),
        Decimal("500"),
        Decimal("500.00"),
        Decimal("500.0000"),
    }
)


@dataclass(frozen=True)
class CatalogPrice:
    amount: Decimal
    billing_period: str  # monthly | annual


@dataclass(frozen=True)
class CatalogFeature:
    feature_code: str
    limit_value: Optional[int]
    enabled: bool = True


@dataclass(frozen=True)
class CatalogPlan:
    code: str
    display_name: str
    description: str
    sort_order: int
    trial_days_default: int
    prices: tuple[CatalogPrice, ...]
    features: tuple[CatalogFeature, ...]


COMMERCIAL_CATALOG: tuple[CatalogPlan, ...] = (
    CatalogPlan(
        code="starter",
        display_name="Starter",
        description="VOXMETRIKS Starter — entry commercial plan.",
        sort_order=10,
        trial_days_default=14,
        prices=(
            CatalogPrice(Decimal("49.00"), "monthly"),
            CatalogPrice(Decimal("490.00"), "annual"),
        ),
        features=(
            CatalogFeature("seats", 5),
            CatalogFeature("projects", 3),
            CatalogFeature("support_standard", None),
        ),
    ),
    CatalogPlan(
        code="professional",
        display_name="Professional",
        description="VOXMETRIKS Professional — growth commercial plan.",
        sort_order=20,
        trial_days_default=14,
        prices=(
            CatalogPrice(Decimal("99.00"), "monthly"),
            CatalogPrice(Decimal("990.00"), "annual"),
        ),
        features=(
            CatalogFeature("seats", 25),
            CatalogFeature("projects", 20),
            CatalogFeature("support_priority", None),
            CatalogFeature("analytics_core", None),
        ),
    ),
    CatalogPlan(
        code="business",
        display_name="Business",
        description="VOXMETRIKS Business — team commercial plan.",
        sort_order=30,
        trial_days_default=14,
        prices=(
            CatalogPrice(Decimal("199.00"), "monthly"),
            CatalogPrice(Decimal("1990.00"), "annual"),
        ),
        features=(
            CatalogFeature("seats", 100),
            CatalogFeature("projects", 100),
            CatalogFeature("support_priority", None),
            CatalogFeature("analytics_advanced", None),
            CatalogFeature("sso", None),
        ),
    ),
    CatalogPlan(
        code="enterprise",
        display_name="Enterprise",
        description="VOXMETRIKS Enterprise — full commercial plan.",
        sort_order=40,
        trial_days_default=30,
        prices=(
            CatalogPrice(Decimal("499.00"), "monthly"),
            CatalogPrice(Decimal("4990.00"), "annual"),
        ),
        features=(
            CatalogFeature("seats", None),  # unlimited
            CatalogFeature("projects", None),
            CatalogFeature("support_dedicated", None),
            CatalogFeature("analytics_advanced", None),
            CatalogFeature("sso", None),
            CatalogFeature("custom_sla", None),
        ),
    ),
)

COMMERCIAL_PLAN_CODES = frozenset(p.code for p in COMMERCIAL_CATALOG)
COMMERCIAL_ACTIVE_AMOUNTS = frozenset(
    price.amount.quantize(Decimal("0.01"))
    for plan in COMMERCIAL_CATALOG
    for price in plan.prices
)


def _next_id(conn: duckdb.DuckDBPyConnection, table: str) -> int:
    return int(conn.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table}").fetchone()[0])


def _quantize(amount: object) -> Decimal:
    return Decimal(str(amount)).quantize(Decimal("0.01"))


def ensure_commercial_catalog(
    conn: duckdb.DuckDBPyConnection,
    *,
    actor_user_id: int = 0,
) -> dict:
    """Idempotently upsert the commercial catalog. Never deletes historical rows."""
    now = utc_now()
    result: dict = {"plans": {}, "prices_active": [], "prices_retired": [], "features": 0}

    for spec in COMMERCIAL_CATALOG:
        plan_row = conn.execute(
            "SELECT id, status FROM app_plan WHERE code = ?", [spec.code]
        ).fetchone()
        if plan_row:
            plan_id = int(plan_row[0])
            conn.execute(
                """
                UPDATE app_plan SET
                    display_name = ?, description = ?, status = 'active',
                    trial_days_default = ?, sort_order = ?, updated_at = ?
                WHERE id = ?
                """,
                [
                    spec.display_name,
                    spec.description,
                    spec.trial_days_default,
                    spec.sort_order,
                    now,
                    plan_id,
                ],
            )
        else:
            plan_id = _next_id(conn, "app_plan")
            conn.execute(
                """
                INSERT INTO app_plan
                    (id, code, display_name, description, status, trial_days_default,
                     sort_order, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'active', ?, ?, ?, ?)
                """,
                [
                    plan_id,
                    spec.code,
                    spec.display_name,
                    spec.description,
                    spec.trial_days_default,
                    spec.sort_order,
                    now,
                    now,
                ],
            )
        result["plans"][spec.code] = plan_id

        for price in spec.prices:
            amount = _quantize(price.amount)
            active = conn.execute(
                """
                SELECT id, amount FROM app_plan_price
                WHERE plan_id = ? AND currency = 'USD' AND billing_period = ?
                  AND status = 'active'
                """,
                [plan_id, price.billing_period],
            ).fetchone()
            if active and _quantize(active[1]) == amount:
                result["prices_active"].append(
                    {
                        "plan_id": plan_id,
                        "price_id": int(active[0]),
                        "amount": str(amount),
                        "billing_period": price.billing_period,
                        "currency": "USD",
                        "status": "active",
                    }
                )
                continue

            if active:
                conn.execute(
                    "UPDATE app_plan_price SET status = 'retired', updated_at = ? WHERE id = ?",
                    [now, int(active[0])],
                )
                result["prices_retired"].append(int(active[0]))

            price_id = _next_id(conn, "app_plan_price")
            conn.execute(
                """
                INSERT INTO app_plan_price
                    (id, plan_id, currency, billing_period, amount, status, created_at, updated_at)
                VALUES (?, ?, 'USD', ?, ?, 'active', ?, ?)
                """,
                [price_id, plan_id, price.billing_period, str(amount), now, now],
            )
            result["prices_active"].append(
                {
                    "plan_id": plan_id,
                    "price_id": price_id,
                    "amount": str(amount),
                    "billing_period": price.billing_period,
                    "currency": "USD",
                    "status": "active",
                }
            )

        for feat in spec.features:
            existing = conn.execute(
                "SELECT id FROM app_plan_feature WHERE plan_id = ? AND feature_code = ?",
                [plan_id, feat.feature_code],
            ).fetchone()
            if existing:
                conn.execute(
                    """
                    UPDATE app_plan_feature
                    SET limit_value = ?, enabled = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    [feat.limit_value, feat.enabled, now, int(existing[0])],
                )
            else:
                fid = _next_id(conn, "app_plan_feature")
                conn.execute(
                    """
                    INSERT INTO app_plan_feature
                        (id, plan_id, feature_code, limit_value, enabled, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        fid,
                        plan_id,
                        feat.feature_code,
                        feat.limit_value,
                        feat.enabled,
                        now,
                        now,
                    ],
                )
            result["features"] += 1

    # Retire legacy demo/test amounts still active outside commercial amounts
    legacy_rows = conn.execute(
        """
        SELECT pp.id, pp.amount, p.code
        FROM app_plan_price pp
        JOIN app_plan p ON p.id = pp.plan_id
        WHERE pp.status = 'active' AND pp.currency = 'USD'
        """
    ).fetchall()
    for price_id, amount, plan_code in legacy_rows:
        amt = _quantize(amount)
        if amt in COMMERCIAL_ACTIVE_AMOUNTS and str(plan_code) in COMMERCIAL_PLAN_CODES:
            continue
        if amt in _LEGACY_DEMO_AMOUNTS or str(plan_code).startswith("demo-"):
            conn.execute(
                "UPDATE app_plan_price SET status = 'retired', updated_at = ? WHERE id = ?",
                [now, int(price_id)],
            )
            result["prices_retired"].append(int(price_id))

    # Soft-archive obsolete demo plan code (keep row; retire remaining prices)
    demo = conn.execute(
        "SELECT id FROM app_plan WHERE code = 'demo-enterprise-starter'"
    ).fetchone()
    if demo:
        did = int(demo[0])
        conn.execute(
            """
            UPDATE app_plan_price SET status = 'retired', updated_at = ?
            WHERE plan_id = ? AND status = 'active'
            """,
            [now, did],
        )
        conn.execute(
            """
            UPDATE app_plan SET status = 'archived', updated_at = ?,
                description = COALESCE(description, '') || ' [ARCHIVED_DEMO_CATALOG]'
            WHERE id = ? AND status != 'archived'
            """,
            [now, did],
        )

    _ = actor_user_id  # reserved for future audit actor
    return result


def get_active_price_id(
    conn: duckdb.DuckDBPyConnection,
    *,
    plan_code: str,
    billing_period: str = "monthly",
    currency: str = "USD",
) -> Optional[int]:
    """Resolve active commercial price id (period ``annual`` = yearly)."""
    period = "annual" if billing_period in {"yearly", "year", "y"} else billing_period
    row = conn.execute(
        """
        SELECT pp.id
        FROM app_plan_price pp
        JOIN app_plan p ON p.id = pp.plan_id
        WHERE p.code = ? AND p.status = 'active'
          AND pp.currency = ? AND pp.billing_period = ? AND pp.status = 'active'
        LIMIT 1
        """,
        [plan_code, currency.upper(), period],
    ).fetchone()
    return int(row[0]) if row else None


def subscription_line_description(
    conn: duckdb.DuckDBPyConnection,
    *,
    subscription_id: int,
) -> Optional[tuple[str, Decimal, str]]:
    """Return (description, unit_price, currency) for a subscription invoice line."""
    from app.core.money_format import format_money

    row = conn.execute(
        """
        SELECT p.display_name, pp.billing_period, pp.amount, pp.currency
        FROM app_subscription s
        JOIN app_plan p ON p.id = s.plan_id
        LEFT JOIN app_plan_price pp ON pp.id = s.plan_price_id
        WHERE s.id = ?
        """,
        [subscription_id],
    ).fetchone()
    if not row:
        return None
    name, period, amount, currency = row
    if amount is None:
        return None
    period_label = "yearly" if str(period) == "annual" else str(period)
    money = format_money(amount, currency or "USD")
    desc = f"{name} · {period_label} · {money}"
    return desc, Decimal(str(amount)), str(currency or "USD")
