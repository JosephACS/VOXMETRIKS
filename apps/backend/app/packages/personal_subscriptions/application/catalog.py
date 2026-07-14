"""Canonical personal music plan catalog — Spec 029.

Demo-configurable amounts live ONLY here (never hard-coded in frontend).
Does not promise offline downloads, HiFi, ad-free, or exclusive content.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

import duckdb

from app.core.time_util import utc_now

OWNER_TYPE_USER = "user"
OWNER_TYPE_ORGANIZATION = "organization"


@dataclass(frozen=True)
class PersonalCatalogPrice:
    amount: Decimal
    billing_period: str  # monthly | annual


@dataclass(frozen=True)
class PersonalCatalogFeature:
    feature_code: str
    limit_value: Optional[int]  # None = unlimited when enabled
    enabled: bool = True


@dataclass(frozen=True)
class PersonalCatalogPlan:
    code: str
    display_name: str
    description: str
    sort_order: int
    max_members: int
    is_free: bool
    prices: tuple[PersonalCatalogPrice, ...]
    features: tuple[PersonalCatalogFeature, ...]


PERSONAL_CATALOG: tuple[PersonalCatalogPlan, ...] = (
    PersonalCatalogPlan(
        code="personal_free",
        display_name="Free",
        description="Escucha música gratis con límites de playlists y favoritos.",
        sort_order=10,
        max_members=1,
        is_free=True,
        prices=(PersonalCatalogPrice(Decimal("0.00"), "monthly"),),
        features=(
            PersonalCatalogFeature("music_playback", None),
            PersonalCatalogFeature("search", None),
            PersonalCatalogFeature("playlists", 3),
            PersonalCatalogFeature("favorites", 50),
            PersonalCatalogFeature("history_recent", 25),
            PersonalCatalogFeature("queue_basic", None),
            PersonalCatalogFeature("household_members", 1),
        ),
    ),
    PersonalCatalogPlan(
        code="premium_individual",
        display_name="Premium Individual",
        description="Playlists y favoritos sin límite configurado, historial completo y cola avanzada.",
        sort_order=20,
        max_members=1,
        is_free=False,
        prices=(
            PersonalCatalogPrice(Decimal("4.99"), "monthly"),
            PersonalCatalogPrice(Decimal("49.90"), "annual"),
        ),
        features=(
            PersonalCatalogFeature("music_playback", None),
            PersonalCatalogFeature("search", None),
            PersonalCatalogFeature("playlists", None),
            PersonalCatalogFeature("favorites", None),
            PersonalCatalogFeature("history_full", None),
            PersonalCatalogFeature("queue_advanced", None),
            PersonalCatalogFeature("recommendations_advanced", None),
            PersonalCatalogFeature("household_members", 1),
        ),
    ),
    PersonalCatalogPlan(
        code="premium_duo",
        display_name="Premium Duo",
        description="Titular + 1 miembro con perfiles, favoritos, historial y recomendaciones separados.",
        sort_order=30,
        max_members=2,
        is_free=False,
        prices=(
            PersonalCatalogPrice(Decimal("7.99"), "monthly"),
            PersonalCatalogPrice(Decimal("79.90"), "annual"),
        ),
        features=(
            PersonalCatalogFeature("music_playback", None),
            PersonalCatalogFeature("search", None),
            PersonalCatalogFeature("playlists", None),
            PersonalCatalogFeature("favorites", None),
            PersonalCatalogFeature("history_full", None),
            PersonalCatalogFeature("queue_advanced", None),
            PersonalCatalogFeature("recommendations_advanced", None),
            PersonalCatalogFeature("household_members", 2),
        ),
    ),
    PersonalCatalogPlan(
        code="premium_family",
        display_name="Premium Familiar",
        description="Titular + hasta 5 miembros con perfiles separados.",
        sort_order=40,
        max_members=6,
        is_free=False,
        prices=(
            PersonalCatalogPrice(Decimal("9.99"), "monthly"),
            PersonalCatalogPrice(Decimal("99.90"), "annual"),
        ),
        features=(
            PersonalCatalogFeature("music_playback", None),
            PersonalCatalogFeature("search", None),
            PersonalCatalogFeature("playlists", None),
            PersonalCatalogFeature("favorites", None),
            PersonalCatalogFeature("history_full", None),
            PersonalCatalogFeature("queue_advanced", None),
            PersonalCatalogFeature("recommendations_advanced", None),
            PersonalCatalogFeature("household_members", 6),
        ),
    ),
)

PERSONAL_PLAN_CODES = frozenset(p.code for p in PERSONAL_CATALOG)
PREMIUM_PLAN_CODES = frozenset(
    p.code for p in PERSONAL_CATALOG if not p.is_free
)


def _next_id(conn: duckdb.DuckDBPyConnection, table: str) -> int:
    return int(conn.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table}").fetchone()[0])


def _quantize(amount: object) -> Decimal:
    return Decimal(str(amount)).quantize(Decimal("0.01"))


def ensure_personal_catalog(conn: duckdb.DuckDBPyConnection) -> None:
    """Idempotent upsert of the personal catalog (active prices + features)."""
    now = utc_now()
    for plan in PERSONAL_CATALOG:
        row = conn.execute(
            "SELECT id FROM personal_plan WHERE code = ?", [plan.code]
        ).fetchone()
        if row:
            plan_id = int(row[0])
            conn.execute(
                """
                UPDATE personal_plan
                SET display_name = ?, description = ?, status = 'active',
                    max_members = ?, sort_order = ?, is_free = ?, updated_at = ?
                WHERE id = ?
                """,
                [
                    plan.display_name,
                    plan.description,
                    plan.max_members,
                    plan.sort_order,
                    plan.is_free,
                    now,
                    plan_id,
                ],
            )
        else:
            plan_id = _next_id(conn, "personal_plan")
            conn.execute(
                """
                INSERT INTO personal_plan (
                    id, code, display_name, description, status,
                    max_members, sort_order, is_free, created_at, updated_at
                ) VALUES (?, ?, ?, ?, 'active', ?, ?, ?, ?, ?)
                """,
                [
                    plan_id,
                    plan.code,
                    plan.display_name,
                    plan.description,
                    plan.max_members,
                    plan.sort_order,
                    plan.is_free,
                    now,
                    now,
                ],
            )

        for price in plan.prices:
            existing = conn.execute(
                """
                SELECT id, amount, status FROM personal_plan_price
                WHERE plan_id = ? AND billing_period = ? AND currency = 'USD'
                """,
                [plan_id, price.billing_period],
            ).fetchone()
            amount = _quantize(price.amount)
            if existing:
                price_id = int(existing[0])
                conn.execute(
                    """
                    UPDATE personal_plan_price
                    SET amount = ?, status = 'active', updated_at = ?
                    WHERE id = ?
                    """,
                    [amount, now, price_id],
                )
            else:
                conn.execute(
                    """
                    INSERT INTO personal_plan_price (
                        id, plan_id, currency, billing_period, amount,
                        status, created_at, updated_at
                    ) VALUES (?, ?, 'USD', ?, ?, 'active', ?, ?)
                    """,
                    [
                        _next_id(conn, "personal_plan_price"),
                        plan_id,
                        price.billing_period,
                        amount,
                        now,
                        now,
                    ],
                )

        # Replace features for plan (idempotent by code)
        for feat in plan.features:
            frow = conn.execute(
                """
                SELECT id FROM personal_plan_feature
                WHERE plan_id = ? AND feature_code = ?
                """,
                [plan_id, feat.feature_code],
            ).fetchone()
            if frow:
                conn.execute(
                    """
                    UPDATE personal_plan_feature
                    SET limit_value = ?, enabled = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    [feat.limit_value, feat.enabled, now, int(frow[0])],
                )
            else:
                conn.execute(
                    """
                    INSERT INTO personal_plan_feature (
                        id, plan_id, feature_code, limit_value, enabled,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        _next_id(conn, "personal_plan_feature"),
                        plan_id,
                        feat.feature_code,
                        feat.limit_value,
                        feat.enabled,
                        now,
                        now,
                    ],
                )
