"""Contracts HTTP router — Spec 017 · /api/v1/crm/contracts."""

from __future__ import annotations

from typing import Optional

import duckdb
from fastapi import APIRouter, Depends, Query

from app.core.database import get_write_conn
from app.packages.contracts.application.use_cases import ContractUseCases
from app.packages.contracts.infrastructure.repository import CommercialContract
from app.packages.contracts.presentation.schemas import (
    ContractAcceptRequest,
    ContractActionRequest,
    ContractCreateRequest,
    ContractOut,
    ContractTerminateRequest,
    PaginatedContracts,
)
from app.packages.crm.presentation.dependencies import (
    require_crm_permission,
    request_id_header,
)

router = APIRouter(prefix="/crm/contracts", tags=["Contracts"])


def _contract_out(c: CommercialContract) -> ContractOut:
    return ContractOut(
        id=c.id,
        quotation_version_id=c.quotation_version_id,
        opportunity_id=c.opportunity_id,
        organization_id=c.organization_id,
        legal_name=c.legal_name,
        signatory_user_id=c.signatory_user_id,
        signatory_contact_id=c.signatory_contact_id,
        status=c.status,
        acceptance_evidence=c.acceptance_evidence,
        accepted_at=c.accepted_at,
        rejected_at=c.rejected_at,
        expired_at=c.expired_at,
        terminated_at=c.terminated_at,
        termination_reason=c.termination_reason,
        approved_by=c.approved_by,
        approved_at=c.approved_at,
        approval_notes=c.approval_notes,
        created_by=c.created_by,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


def _raise_http(exc: Exception):
    from fastapi import HTTPException
    if isinstance(exc, HTTPException):
        raise exc
    if isinstance(exc, KeyError):
        raise HTTPException(status_code=404, detail={"message": "Not found", "code": "not_found"})
    if isinstance(exc, ValueError):
        raise HTTPException(status_code=422, detail={"message": str(exc), "code": "validation_error"})
    raise HTTPException(status_code=500, detail={"message": "Internal error", "code": "internal_error"})


@router.post("", status_code=201, response_model=ContractOut)
def create_contract(
    body: ContractCreateRequest,
    actor: dict = Depends(require_crm_permission("contract.create")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        c = ContractUseCases(conn).create(
            actor_user_id=actor["user_id"],
            quotation_version_id=body.quotation_version_id,
            opportunity_id=body.opportunity_id,
            legal_name=body.legal_name,
            organization_id=body.organization_id,
            signatory_user_id=body.signatory_user_id,
            signatory_contact_id=body.signatory_contact_id,
            terms_snapshot=body.terms_snapshot,
            request_id=actor["request_id"],
        )
        return _contract_out(c)
    except Exception as exc:
        _raise_http(exc)


@router.get("", response_model=PaginatedContracts)
def list_contracts(
    page: int = Query(1, ge=1),
    limit: int = Query(25, ge=1, le=100),
    opportunity_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    actor: dict = Depends(require_crm_permission("contract.create")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        page = max(1, page)
        lim = min(max(1, limit), 100)
        offset = (page - 1) * lim
        items, total = ContractUseCases(conn).list(opportunity_id=opportunity_id, status=status, limit=lim, offset=offset)
        return PaginatedContracts(items=[_contract_out(c) for c in items], page=page, limit=lim, total=total)
    except Exception as exc:
        _raise_http(exc)


@router.get("/{contract_id}", response_model=ContractOut)
def get_contract(
    contract_id: int,
    actor: dict = Depends(require_crm_permission("contract.create")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        return _contract_out(ContractUseCases(conn).get(contract_id))
    except Exception as exc:
        _raise_http(exc)


@router.post("/{contract_id}/submit", response_model=ContractOut)
def submit_contract(
    contract_id: int,
    actor: dict = Depends(require_crm_permission("contract.create")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        return _contract_out(ContractUseCases(conn).submit_for_approval(
            contract_id, actor_user_id=actor["user_id"], request_id=actor["request_id"]
        ))
    except Exception as exc:
        _raise_http(exc)


@router.post("/{contract_id}/approve", response_model=ContractOut)
def approve_contract(
    contract_id: int,
    body: ContractActionRequest,
    actor: dict = Depends(require_crm_permission("contract.approve")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        return _contract_out(ContractUseCases(conn).approve(
            contract_id, actor_user_id=actor["user_id"],
            approval_notes=body.reason, request_id=actor["request_id"]
        ))
    except Exception as exc:
        _raise_http(exc)


@router.post("/{contract_id}/send", response_model=ContractOut)
def send_contract(
    contract_id: int,
    actor: dict = Depends(require_crm_permission("contract.create")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        return _contract_out(ContractUseCases(conn).send(
            contract_id, actor_user_id=actor["user_id"], request_id=actor["request_id"]
        ))
    except Exception as exc:
        _raise_http(exc)


@router.post("/{contract_id}/accept", response_model=ContractOut)
def accept_contract(
    contract_id: int,
    body: ContractAcceptRequest,
    actor: dict = Depends(require_crm_permission("contract.accept")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        return _contract_out(ContractUseCases(conn).accept(
            contract_id, actor_user_id=actor["user_id"],
            acceptance_evidence=body.acceptance_evidence, request_id=actor["request_id"]
        ))
    except Exception as exc:
        _raise_http(exc)


@router.post("/{contract_id}/reject", response_model=ContractOut)
def reject_contract(
    contract_id: int,
    body: ContractActionRequest,
    actor: dict = Depends(require_crm_permission("contract.create")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        return _contract_out(ContractUseCases(conn).reject(
            contract_id, actor_user_id=actor["user_id"],
            reason=body.reason, request_id=actor["request_id"]
        ))
    except Exception as exc:
        _raise_http(exc)


@router.post("/{contract_id}/expire", response_model=ContractOut)
def expire_contract(
    contract_id: int,
    actor: dict = Depends(require_crm_permission("contract.approve")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        return _contract_out(ContractUseCases(conn).expire(
            contract_id, actor_user_id=actor["user_id"], request_id=actor["request_id"]
        ))
    except Exception as exc:
        _raise_http(exc)


@router.post("/{contract_id}/terminate", response_model=ContractOut)
def terminate_contract(
    contract_id: int,
    body: ContractTerminateRequest,
    actor: dict = Depends(require_crm_permission("contract.approve")),
    conn: duckdb.DuckDBPyConnection = Depends(get_write_conn),
):
    try:
        return _contract_out(ContractUseCases(conn).terminate(
            contract_id, actor_user_id=actor["user_id"],
            reason=body.reason, request_id=actor["request_id"]
        ))
    except Exception as exc:
        _raise_http(exc)
