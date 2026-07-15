"""Royalty Pydantic schemas — Spec 030. Decimal money only."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, List, Optional

from pydantic import BaseModel, field_validator


def _as_decimal(v: Any) -> Decimal:
    if isinstance(v, Decimal):
        return v
    if isinstance(v, float):
        return Decimal(str(v))
    return Decimal(str(v))


class PoolCreateRequest(BaseModel):
    currency: str
    period_start: date
    period_end: date
    idempotency_key: str
    attribution_method: str = "PRO_RATA_STREAM_SHARE"
    total_amount: Decimal = Decimal("0")
    label: Optional[str] = None
    is_demo: bool = False

    @field_validator("total_amount", mode="before")
    @classmethod
    def _dec_total(cls, v: Any) -> Decimal:
        return _as_decimal(v)


class B2CSourceRequest(BaseModel):
    amount: Decimal
    currency: str
    source_payment_id: Optional[str] = None
    source_invoice_id: Optional[str] = None
    reason: Optional[str] = None
    evidence_ref: Optional[str] = None
    approve: bool = False

    @field_validator("amount", mode="before")
    @classmethod
    def _dec_amt(cls, v: Any) -> Decimal:
        return _as_decimal(v)


class ManualB2BSourceRequest(BaseModel):
    amount: Decimal
    currency: str
    reason: str
    source_payment_id: Optional[str] = None
    source_invoice_id: Optional[str] = None
    evidence_ref: Optional[str] = None
    approve: bool = True

    @field_validator("amount", mode="before")
    @classmethod
    def _dec_amt(cls, v: Any) -> Decimal:
        return _as_decimal(v)


class AssetScopeIn(BaseModel):
    asset_id: int
    warehouse_track_id: Optional[int] = None
    rights_contract_id: Optional[int] = None


class ProRataSettlementRequest(BaseModel):
    idempotency_key: str
    asset_scopes: Optional[List[AssetScopeIn]] = None
    synthetic_event_counts: Optional[dict[int, int]] = None


class AdjustmentRequest(BaseModel):
    amount: Decimal
    reason: str
    party_allocation_id: Optional[int] = None

    @field_validator("amount", mode="before")
    @classmethod
    def _dec_amt(cls, v: Any) -> Decimal:
        return _as_decimal(v)


class RejectSettlementRequest(BaseModel):
    reason: str = "rejected"


class PayoutBatchCreateRequest(BaseModel):
    idempotency_key: str
    destination_type: str = "demo_wallet"
    destination_ref_prefix: str = "demo_wallet"


class SimulatePayoutRequest(BaseModel):
    scenario: str = "succeed"


class RetryPayoutRequest(BaseModel):
    scenario: str = "succeed"


class PoolOut(BaseModel):
    id: int
    organization_id: Optional[int]
    currency: str
    period_start: date
    period_end: date
    status: str
    attribution_method: str
    total_amount: Decimal
    residual_amount: Decimal
    label: Optional[str]
    is_demo: bool
    idempotency_key: str
    created_by: int
    approved_by: Optional[int]
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime]
    sources: Optional[List[dict[str, Any]]] = None


class SettlementOut(BaseModel):
    id: int
    pool_id: int
    status: str
    currency: str
    gross_total: Decimal
    adjustment_total: Decimal
    net_total: Decimal
    block_conflict_id: Optional[int]
    idempotency_key: str
    created_by: int
    approved_by: Optional[int]
    finalized_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    block_reason: Optional[str]
    asset_allocations: Optional[List[dict[str, Any]]] = None
    party_allocations: Optional[List[dict[str, Any]]] = None


class StatementOut(BaseModel):
    id: int
    settlement_run_id: int
    party_id: int
    party_name: str
    period_start: date
    period_end: date
    currency: str
    gross_amount: Decimal
    adjustment_amount: Decimal
    net_amount: Decimal
    status: str
    export_json: Optional[str]
    created_at: datetime


class PayoutBatchOut(BaseModel):
    id: int
    settlement_run_id: int
    status: str
    currency: str
    total_amount: Decimal
    idempotency_key: str
    created_by: int
    created_at: datetime
    updated_at: datetime
    instructions: Optional[List[dict[str, Any]]] = None
    simulated_only: bool = True


class MetricsOut(BaseModel):
    income_note: str
    distributable_pool_approved: Decimal
    distributable_pool_allocated_or_closed: Decimal
    pool_count: int
    settlement_gross_total: Decimal
    settlement_net_total: Decimal
    settlement_count: int
    payout_paid_simulated_total: Decimal
    payout_batch_count: int
    simulated_only: bool = True
