"""Recurring revenue KPIs — MRR/ARR from subscriptions + plan prices.

Policy (conservative, no FX):
- Active MRR: status=active only; trial/canceled/expired excluded
- Past-due MRR: status=past_due, reported separately
- Total recurring exposure: active + past_due (labeled)
- Monthly price → amount; annual → amount/12
- ARR = MRR × 12 per currency bucket
- Missing price/currency/period → null (No disponible)
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional

import duckdb


def _monthly_amount(amount: float, billing_period: str) -> Optional[float]:
    period = (billing_period or "").strip().lower()
    if period in ("monthly", "month", "m"):
        return float(amount)
    if period in ("yearly", "annual", "year", "y"):
        return float(amount) / 12.0
    return None


def compute_recurring_revenue(
    conn: duckdb.DuckDBPyConnection,
    *,
    organization_id: int,
) -> dict[str, Any]:
    """Return multi-currency MRR/ARR breakdown with honest nulls."""
    try:
        rows = conn.execute(
            """
            SELECT s.status, s.billing_currency, pp.amount, pp.billing_period, pp.currency
            FROM app_subscription s
            LEFT JOIN app_plan_price pp ON pp.id = s.plan_price_id AND pp.status = 'active'
            WHERE s.organization_id = ?
              AND s.status IN ('active', 'past_due', 'trialing')
            """,
            [organization_id],
        ).fetchall()
    except duckdb.CatalogException:
        return {
            "active_mrr": None,
            "active_arr": None,
            "primary_currency": None,
            "quality_status": "schema_unavailable",
            "active_by_currency": [],
            "past_due_by_currency": [],
            "total_recurring_exposure_by_currency": [],
            "trialing_excluded": 0,
            "unavailable_rows": 0,
            "policy": {
                "active_mrr": "subscriptions status=active only",
                "past_due_mrr": "reported separately; not included in Active MRR",
                "trial": "excluded from MRR",
                "annual_normalization": "amount/12",
                "fx": "none — multi-currency remains No disponible for single KPI",
            },
            "source_label": "subscriptions:plan_price",
        }

    active_by_ccy: dict[str, float] = {}
    past_due_by_ccy: dict[str, float] = {}
    unavailable = 0
    trialing_skipped = 0

    for status, billing_currency, amount, billing_period, price_currency in rows:
        if status == "trialing":
            trialing_skipped += 1
            continue
        currency = (price_currency or billing_currency or "").upper()
        if not currency or amount is None or billing_period is None:
            unavailable += 1
            continue
        if price_currency and billing_currency and str(price_currency).upper() != str(billing_currency).upper():
            unavailable += 1
            continue
        monthly = _monthly_amount(float(amount), str(billing_period))
        if monthly is None:
            unavailable += 1
            continue
        bucket = active_by_ccy if status == "active" else past_due_by_ccy
        bucket[currency] = bucket.get(currency, 0.0) + monthly

    def _pack(by_ccy: dict[str, float]) -> list[dict[str, Any]]:
        return [
            {
                "currency": ccy,
                "mrr": round(v, 4),
                "arr": round(v * 12.0, 4),
            }
            for ccy, v in sorted(by_ccy.items())
        ]

    active = _pack(active_by_ccy)
    past_due = _pack(past_due_by_ccy)
    exposure: dict[str, float] = {}
    for ccy, v in active_by_ccy.items():
        exposure[ccy] = exposure.get(ccy, 0.0) + v
    for ccy, v in past_due_by_ccy.items():
        exposure[ccy] = exposure.get(ccy, 0.0) + v

    # Primary display KPI: single-currency Active MRR if exactly one currency, else null
    primary_mrr: Optional[float] = None
    primary_arr: Optional[float] = None
    primary_currency: Optional[str] = None
    quality = "ok"
    if len(active) == 1:
        primary_mrr = active[0]["mrr"]
        primary_arr = active[0]["arr"]
        primary_currency = active[0]["currency"]
    elif len(active) == 0:
        primary_mrr = None
        primary_arr = None
        quality = "no_active_recurring"
    else:
        primary_mrr = None
        primary_arr = None
        quality = "multi_currency_no_fx"

    return {
        "active_mrr": primary_mrr,
        "active_arr": primary_arr,
        "primary_currency": primary_currency,
        "quality_status": quality,
        "active_by_currency": active,
        "past_due_by_currency": past_due,
        "total_recurring_exposure_by_currency": _pack(exposure),
        "trialing_excluded": trialing_skipped,
        "unavailable_rows": unavailable,
        "policy": {
            "active_mrr": "subscriptions status=active only",
            "past_due_mrr": "reported separately; not included in Active MRR",
            "trial": "excluded from MRR",
            "annual_normalization": "amount/12",
            "fx": "none — multi-currency remains No disponible for single KPI",
        },
        "source_label": "subscriptions:plan_price",
    }
