"""Simulated payout provider — Spec 030.

Never stores bank credentials. Always labeled simulated / MOCK.
No real money movement.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from app.core.time_util import utc_now


PAYOUT_SCENARIOS = frozenset(
    {
        "succeed",
        "processing",
        "failed",
        "invalid_destination",
        "duplicate_request",
        "reversed",
    }
)


@dataclass(frozen=True)
class SimulatedPayoutRequest:
    amount: Decimal
    currency: str
    idempotency_key: str
    destination_type: str
    destination_ref: str
    instruction_id: Optional[int] = None
    scenario: Optional[str] = None


@dataclass(frozen=True)
class SimulatedPayoutResult:
    success: bool
    status: str
    labeled_simulated: bool
    message: str
    provider_ref: str
    error_code: Optional[str] = None
    scenario: Optional[str] = None


class SimulatedPayoutProvider:
    """Academic payout simulator — never moves real money, never stores bank data."""

    code = "simulated_payout"
    is_simulated = True

    def pay(self, request: SimulatedPayoutRequest) -> SimulatedPayoutResult:
        scenario = (request.scenario or "succeed").strip().lower()
        if scenario not in PAYOUT_SCENARIOS:
            raise ValueError(f"Unknown simulated payout scenario={scenario!r}")

        # Refuse anything that looks like raw bank vaulting
        ref = (request.destination_ref or "").strip()
        if request.destination_type not in (
            "demo_wallet",
            "demo_bank_reference",
            "simulated_account_token",
        ):
            return SimulatedPayoutResult(
                success=False,
                status="failed",
                labeled_simulated=True,
                message="[SIMULATED] Invalid destination_type — not a real payout",
                provider_ref="",
                error_code="invalid_destination",
                scenario="invalid_destination",
            )

        token = (
            f"sim_{hashlib.sha256(request.idempotency_key.encode()).hexdigest()[:14]}"
        )
        now = utc_now().isoformat()

        if scenario == "succeed":
            return SimulatedPayoutResult(
                success=True,
                status="paid_simulated",
                labeled_simulated=True,
                message=f"[SIMULATED] Payout succeeded at {now} — not a real transfer",
                provider_ref=token,
                scenario=scenario,
            )
        if scenario == "processing":
            return SimulatedPayoutResult(
                success=True,
                status="processing",
                labeled_simulated=True,
                message="[SIMULATED] Payout processing — not a real transfer",
                provider_ref=token,
                scenario=scenario,
            )
        if scenario == "failed":
            return SimulatedPayoutResult(
                success=False,
                status="failed",
                labeled_simulated=True,
                message="[SIMULATED] Payout failed — not a real transfer",
                provider_ref=token,
                error_code="simulated_failure",
                scenario=scenario,
            )
        if scenario == "invalid_destination":
            return SimulatedPayoutResult(
                success=False,
                status="failed",
                labeled_simulated=True,
                message="[SIMULATED] Invalid destination — tokens only, no bank vault",
                provider_ref=token,
                error_code="invalid_destination",
                scenario=scenario,
            )
        if scenario == "duplicate_request":
            # Deterministic ref from key — idempotent replay
            dup = f"sim_dup_{hashlib.sha256(request.idempotency_key.encode()).hexdigest()[:14]}"
            return SimulatedPayoutResult(
                success=True,
                status="paid_simulated",
                labeled_simulated=True,
                message="[SIMULATED] Duplicate request — returned prior outcome",
                provider_ref=dup,
                scenario=scenario,
            )
        # reversed
        return SimulatedPayoutResult(
            success=True,
            status="reversed",
            labeled_simulated=True,
            message="[SIMULATED] Payout reversed — not a real transfer",
            provider_ref=token or f"sim_rev_{uuid.uuid4().hex[:12]}",
            scenario=scenario,
        )
