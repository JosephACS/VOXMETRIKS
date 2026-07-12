"""Central money / date formatters for transactional email (and billing copy)."""

from __future__ import annotations

from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional, Union

NumberLike = Union[Decimal, int, float, str]


def format_money(amount: NumberLike, currency: str) -> str:
    """Format amounts as ``$100.00 USD`` (exactly 2 decimal places)."""
    value = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    code = (currency or "").strip().upper() or "USD"
    return f"${value:.2f} {code}"


def format_due_date(due: Optional[Union[date, datetime, str]]) -> str:
    """Human due-date line for invoices; never ``N/A``."""
    if due is None or due == "":
        return "Sin fecha de vencimiento definida"
    if isinstance(due, datetime):
        return due.date().isoformat()
    if isinstance(due, date):
        return due.isoformat()
    text = str(due).strip()
    return text or "Sin fecha de vencimiento definida"
