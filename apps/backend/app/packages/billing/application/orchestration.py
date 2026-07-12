"""Subscription orchestration hooks for billing — Spec 019.

Thin layer that calls SubscriptionUseCases from billing use cases.
Avoids circular imports: billing → subscriptions; subscriptions never imports billing.
"""

from __future__ import annotations

from typing import Optional

import duckdb


def notify_subscription_past_due(
    conn: duckdb.DuckDBPyConnection,
    *,
    subscription_id: int,
    actor_user_id: int,
    request_id: Optional[str] = None,
) -> None:
    """Mark subscription past_due and limit access when invoice goes past due."""
    from app.packages.subscriptions.application.use_cases import SubscriptionUseCases

    try:
        SubscriptionUseCases(conn).update_access_state(
            subscription_id,
            actor_user_id=actor_user_id,
            access_state="limited",
            also_set_past_due=True,
            reason="billing_past_due",
            request_id=request_id,
        )
    except Exception:
        pass


def notify_subscription_recovered(
    conn: duckdb.DuckDBPyConnection,
    *,
    subscription_id: int,
    actor_user_id: int,
    request_id: Optional[str] = None,
) -> None:
    """Restore subscription access when payment is settled."""
    from app.packages.subscriptions.application.use_cases import SubscriptionUseCases

    try:
        SubscriptionUseCases(conn).update_access_state(
            subscription_id,
            actor_user_id=actor_user_id,
            access_state="full",
            also_restore_active=True,
            reason="payment_settled",
            request_id=request_id,
        )
    except Exception:
        pass
