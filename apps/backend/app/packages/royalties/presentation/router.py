"""Royalty HTTP routers — Spec 030.

Prefixes: /royalties, /settlements, /payouts
Mounted under /api/v1 via royalties_router.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.packages.royalties.application.use_cases import RoyaltiesUseCases
from app.packages.royalties.domain.errors import RoyaltyError
from app.packages.royalties.presentation.dependencies import require_org_royalty_permission
from app.packages.royalties.presentation.error_mapping import raise_royalty_http
from app.packages.royalties.presentation.schemas import (
    AdjustmentRequest,
    B2CSourceRequest,
    ManualB2BSourceRequest,
    MetricsOut,
    PayoutBatchCreateRequest,
    PayoutBatchOut,
    PoolCreateRequest,
    PoolOut,
    ProRataSettlementRequest,
    RejectSettlementRequest,
    RetryPayoutRequest,
    SettlementOut,
    SimulatePayoutRequest,
    StatementOut,
)

royalties_sub = APIRouter(prefix="/royalties", tags=["Royalties"])
settlements_sub = APIRouter(prefix="/settlements", tags=["Settlements"])
payouts_sub = APIRouter(prefix="/payouts", tags=["Payouts"])


def _pool_out(d: dict) -> PoolOut:
    return PoolOut(**{k: d[k] for k in PoolOut.model_fields if k in d})


def _settlement_out(d: dict) -> SettlementOut:
    return SettlementOut(**{k: d[k] for k in SettlementOut.model_fields if k in d})


def _statement_out(d: dict) -> StatementOut:
    return StatementOut(**{k: d[k] for k in StatementOut.model_fields if k in d})


def _batch_out(d: dict) -> PayoutBatchOut:
    return PayoutBatchOut(
        **{k: d[k] for k in PayoutBatchOut.model_fields if k in d and k != "simulated_only"},
        simulated_only=True,
    )


# ── /royalties ─────────────────────────────────────────────────────────────


@royalties_sub.get("/pools", response_model=list[PoolOut])
def list_pools(
    ctx: dict = Depends(require_org_royalty_permission("royalty.view")),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[PoolOut]:
    try:
        rows = RoyaltiesUseCases(ctx["conn"]).list_pools(
            organization_id=ctx["organization_id"], limit=limit, offset=offset
        )
    except RoyaltyError as e:
        raise_royalty_http(e)
    return [_pool_out(r) for r in rows]


@royalties_sub.post("/pools", response_model=PoolOut, status_code=201)
def create_pool(
    body: PoolCreateRequest,
    ctx: dict = Depends(require_org_royalty_permission("royalty.pool.manage")),
) -> PoolOut:
    try:
        pool = RoyaltiesUseCases(ctx["conn"]).create_pool(
            actor_user_id=ctx["user_id"],
            organization_id=ctx["organization_id"],
            currency=body.currency,
            period_start=body.period_start,
            period_end=body.period_end,
            idempotency_key=body.idempotency_key,
            attribution_method=body.attribution_method,
            total_amount=body.total_amount,
            label=body.label,
            is_demo=body.is_demo,
        )
    except RoyaltyError as e:
        raise_royalty_http(e)
    return _pool_out(pool)


@royalties_sub.get("/pools/{pool_id}", response_model=PoolOut)
def get_pool(
    pool_id: int,
    ctx: dict = Depends(require_org_royalty_permission("royalty.view")),
) -> PoolOut:
    try:
        pool = RoyaltiesUseCases(ctx["conn"]).get_pool(pool_id)
    except RoyaltyError as e:
        raise_royalty_http(e)
    return _pool_out(pool)


@royalties_sub.post("/pools/{pool_id}/sources/b2c", response_model=dict, status_code=201)
def add_b2c_source(
    pool_id: int,
    body: B2CSourceRequest,
    ctx: dict = Depends(require_org_royalty_permission("royalty.pool.manage")),
) -> dict:
    try:
        return RoyaltiesUseCases(ctx["conn"]).add_b2c_source(
            pool_id=pool_id,
            actor_user_id=ctx["user_id"],
            amount=body.amount,
            currency=body.currency,
            source_payment_id=body.source_payment_id,
            source_invoice_id=body.source_invoice_id,
            reason=body.reason,
            evidence_ref=body.evidence_ref,
            organization_id=ctx["organization_id"],
            approve=body.approve,
        )
    except RoyaltyError as e:
        raise_royalty_http(e)


@royalties_sub.post("/pools/{pool_id}/sources/manual-b2b", response_model=dict, status_code=201)
def add_manual_b2b_source(
    pool_id: int,
    body: ManualB2BSourceRequest,
    ctx: dict = Depends(require_org_royalty_permission("royalty.pool.manage")),
) -> dict:
    try:
        return RoyaltiesUseCases(ctx["conn"]).add_manual_b2b_source(
            pool_id=pool_id,
            actor_user_id=ctx["user_id"],
            amount=body.amount,
            currency=body.currency,
            reason=body.reason,
            source_payment_id=body.source_payment_id,
            source_invoice_id=body.source_invoice_id,
            evidence_ref=body.evidence_ref,
            organization_id=ctx["organization_id"],
            approve=body.approve,
        )
    except RoyaltyError as e:
        raise_royalty_http(e)


@royalties_sub.post("/pools/{pool_id}/approve", response_model=PoolOut)
def approve_pool(
    pool_id: int,
    ctx: dict = Depends(require_org_royalty_permission("royalty.approve")),
) -> PoolOut:
    try:
        pool = RoyaltiesUseCases(ctx["conn"]).approve_pool(
            pool_id=pool_id, actor_user_id=ctx["user_id"]
        )
    except RoyaltyError as e:
        raise_royalty_http(e)
    return _pool_out(pool)


@royalties_sub.post("/pools/{pool_id}/settle/pro-rata", response_model=SettlementOut)
def settle_pro_rata(
    pool_id: int,
    body: ProRataSettlementRequest,
    ctx: dict = Depends(require_org_royalty_permission("royalty.settle")),
) -> SettlementOut:
    try:
        scopes = [s.model_dump() for s in body.asset_scopes] if body.asset_scopes else None
        run = RoyaltiesUseCases(ctx["conn"]).calculate_pro_rata_settlement(
            pool_id=pool_id,
            actor_user_id=ctx["user_id"],
            idempotency_key=body.idempotency_key,
            asset_scopes=scopes,
            synthetic_event_counts=body.synthetic_event_counts,
        )
    except RoyaltyError as e:
        raise_royalty_http(e)
    return _settlement_out(run)


@royalties_sub.get("/metrics", response_model=MetricsOut)
def metrics(
    ctx: dict = Depends(require_org_royalty_permission("royalty.view")),
) -> MetricsOut:
    data = RoyaltiesUseCases(ctx["conn"]).metrics_dashboard(
        organization_id=ctx["organization_id"]
    )
    return MetricsOut(**data)


@royalties_sub.get("/statements", response_model=list[StatementOut])
def list_statements(
    ctx: dict = Depends(require_org_royalty_permission("royalty.view")),
    settlement_run_id: Optional[int] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> list[StatementOut]:
    try:
        rows = RoyaltiesUseCases(ctx["conn"]).list_statements(
            settlement_run_id=settlement_run_id, limit=limit, offset=offset
        )
    except RoyaltyError as e:
        raise_royalty_http(e)
    return [_statement_out(r) for r in rows]


# ── /settlements ───────────────────────────────────────────────────────────


@settlements_sub.get("/{settlement_id}", response_model=SettlementOut)
def get_settlement(
    settlement_id: int,
    ctx: dict = Depends(require_org_royalty_permission("royalty.view")),
) -> SettlementOut:
    try:
        run = RoyaltiesUseCases(ctx["conn"]).get_settlement(settlement_id)
    except RoyaltyError as e:
        raise_royalty_http(e)
    return _settlement_out(run)


@settlements_sub.post("/{settlement_id}/contract-splits", response_model=SettlementOut)
def contract_splits(
    settlement_id: int,
    ctx: dict = Depends(require_org_royalty_permission("royalty.settle")),
) -> SettlementOut:
    try:
        run = RoyaltiesUseCases(ctx["conn"]).calculate_contract_splits(
            settlement_run_id=settlement_id, actor_user_id=ctx["user_id"]
        )
    except RoyaltyError as e:
        raise_royalty_http(e)
    return _settlement_out(run)


@settlements_sub.post("/{settlement_id}/adjustments", response_model=dict)
def apply_adjustment(
    settlement_id: int,
    body: AdjustmentRequest,
    ctx: dict = Depends(require_org_royalty_permission("royalty.adjust")),
) -> dict:
    try:
        return RoyaltiesUseCases(ctx["conn"]).apply_adjustment(
            settlement_run_id=settlement_id,
            actor_user_id=ctx["user_id"],
            amount=body.amount,
            reason=body.reason,
            party_allocation_id=body.party_allocation_id,
        )
    except RoyaltyError as e:
        raise_royalty_http(e)


@settlements_sub.post("/{settlement_id}/statements", response_model=list[StatementOut])
def generate_statements(
    settlement_id: int,
    ctx: dict = Depends(require_org_royalty_permission("royalty.settle")),
) -> list[StatementOut]:
    try:
        rows = RoyaltiesUseCases(ctx["conn"]).generate_statements(
            settlement_run_id=settlement_id, actor_user_id=ctx["user_id"]
        )
    except RoyaltyError as e:
        raise_royalty_http(e)
    return [_statement_out(r) for r in rows]


@settlements_sub.post("/{settlement_id}/submit", response_model=SettlementOut)
def submit_settlement(
    settlement_id: int,
    ctx: dict = Depends(require_org_royalty_permission("royalty.settle")),
) -> SettlementOut:
    try:
        run = RoyaltiesUseCases(ctx["conn"]).submit_for_approval(
            settlement_run_id=settlement_id, actor_user_id=ctx["user_id"]
        )
    except RoyaltyError as e:
        raise_royalty_http(e)
    return _settlement_out(run)


@settlements_sub.post("/{settlement_id}/approve", response_model=SettlementOut)
def approve_settlement(
    settlement_id: int,
    ctx: dict = Depends(require_org_royalty_permission("royalty.approve")),
) -> SettlementOut:
    try:
        run = RoyaltiesUseCases(ctx["conn"]).approve_settlement(
            settlement_run_id=settlement_id, actor_user_id=ctx["user_id"]
        )
    except RoyaltyError as e:
        raise_royalty_http(e)
    return _settlement_out(run)


@settlements_sub.post("/{settlement_id}/reject", response_model=SettlementOut)
def reject_settlement(
    settlement_id: int,
    body: RejectSettlementRequest,
    ctx: dict = Depends(require_org_royalty_permission("royalty.approve")),
) -> SettlementOut:
    try:
        run = RoyaltiesUseCases(ctx["conn"]).reject_settlement(
            settlement_run_id=settlement_id,
            actor_user_id=ctx["user_id"],
            reason=body.reason,
        )
    except RoyaltyError as e:
        raise_royalty_http(e)
    return _settlement_out(run)


@settlements_sub.post("/{settlement_id}/finalize", response_model=SettlementOut)
def finalize_settlement(
    settlement_id: int,
    ctx: dict = Depends(require_org_royalty_permission("royalty.approve")),
) -> SettlementOut:
    try:
        run = RoyaltiesUseCases(ctx["conn"]).finalize_settlement(
            settlement_run_id=settlement_id, actor_user_id=ctx["user_id"]
        )
    except RoyaltyError as e:
        raise_royalty_http(e)
    return _settlement_out(run)


@settlements_sub.post("/{settlement_id}/payout-batches", response_model=PayoutBatchOut, status_code=201)
def create_payout_batch(
    settlement_id: int,
    body: PayoutBatchCreateRequest,
    ctx: dict = Depends(require_org_royalty_permission("royalty.payout")),
) -> PayoutBatchOut:
    try:
        batch = RoyaltiesUseCases(ctx["conn"]).create_payout_batch(
            settlement_run_id=settlement_id,
            actor_user_id=ctx["user_id"],
            idempotency_key=body.idempotency_key,
            destination_type=body.destination_type,
            destination_ref_prefix=body.destination_ref_prefix,
        )
    except RoyaltyError as e:
        raise_royalty_http(e)
    return _batch_out(batch)


# ── /payouts ───────────────────────────────────────────────────────────────


@payouts_sub.get("/batches/{batch_id}", response_model=PayoutBatchOut)
def get_payout_batch(
    batch_id: int,
    ctx: dict = Depends(require_org_royalty_permission("royalty.view")),
) -> PayoutBatchOut:
    try:
        batch = RoyaltiesUseCases(ctx["conn"])._get_batch(batch_id)
    except RoyaltyError as e:
        raise_royalty_http(e)
    return _batch_out(batch)


@payouts_sub.post("/batches/{batch_id}/simulate", response_model=PayoutBatchOut)
def simulate_payouts(
    batch_id: int,
    body: SimulatePayoutRequest,
    ctx: dict = Depends(require_org_royalty_permission("royalty.payout")),
) -> PayoutBatchOut:
    try:
        batch = RoyaltiesUseCases(ctx["conn"]).simulate_payouts(
            batch_id=batch_id, actor_user_id=ctx["user_id"], scenario=body.scenario
        )
    except RoyaltyError as e:
        raise_royalty_http(e)
    return _batch_out(batch)


@payouts_sub.post("/instructions/{instruction_id}/retry", response_model=PayoutBatchOut)
def retry_payout(
    instruction_id: int,
    body: RetryPayoutRequest,
    ctx: dict = Depends(require_org_royalty_permission("royalty.payout")),
) -> PayoutBatchOut:
    try:
        batch = RoyaltiesUseCases(ctx["conn"]).retry_payout(
            instruction_id=instruction_id,
            actor_user_id=ctx["user_id"],
            scenario=body.scenario,
        )
    except RoyaltyError as e:
        raise_royalty_http(e)
    return _batch_out(batch)


@payouts_sub.post("/batches/{batch_id}/reverse", response_model=PayoutBatchOut)
def reverse_payout(
    batch_id: int,
    ctx: dict = Depends(require_org_royalty_permission("royalty.payout")),
) -> PayoutBatchOut:
    try:
        batch = RoyaltiesUseCases(ctx["conn"]).reverse_payout(
            batch_id=batch_id, actor_user_id=ctx["user_id"]
        )
    except RoyaltyError as e:
        raise_royalty_http(e)
    return _batch_out(batch)


# Aggregate router exported for main.py
royalties_router = APIRouter()
royalties_router.include_router(royalties_sub)
royalties_router.include_router(settlements_sub)
royalties_router.include_router(payouts_sub)
