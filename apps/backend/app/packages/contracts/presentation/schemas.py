"""Contract Pydantic schemas — Spec 017."""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel


class ContractCreateRequest(BaseModel):
    quotation_version_id: int
    opportunity_id: int
    legal_name: str
    organization_id: Optional[int] = None
    signatory_user_id: Optional[int] = None
    signatory_contact_id: Optional[int] = None
    terms_snapshot: Optional[dict] = None


class ContractActionRequest(BaseModel):
    reason: Optional[str] = None


class ContractAcceptRequest(BaseModel):
    acceptance_evidence: Optional[str] = None


class ContractTerminateRequest(BaseModel):
    reason: str


class ContractOut(BaseModel):
    id: int
    quotation_version_id: int
    opportunity_id: int
    organization_id: Optional[int]
    legal_name: str
    signatory_user_id: Optional[int]
    signatory_contact_id: Optional[int]
    status: str
    acceptance_evidence: Optional[str]
    accepted_at: Optional[datetime]
    rejected_at: Optional[datetime]
    expired_at: Optional[datetime]
    terminated_at: Optional[datetime]
    termination_reason: Optional[str]
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    approval_notes: Optional[str]
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedContracts(BaseModel):
    items: List[ContractOut]
    page: int
    limit: int
    total: int
