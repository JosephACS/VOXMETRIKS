"""Campaigns use cases — Spec 022."""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

import duckdb

from app.core.time_util import utc_now
from app.packages.campaigns.domain.entities import (
    AttributionDefinition,
    AttributableRevenueRecord,
    Campaign,
    CampaignApproval,
    CampaignBudget,
    CampaignExpense,
    CampaignObjective,
    CampaignResult,
    CampaignRoiSnapshot,
    CampaignStatusHistoryEntry,
    CampaignTarget,
)
from app.packages.campaigns.domain.errors import (
    ApprovalStateError,
    BudgetExceededError,
    CampaignsError,
    InvalidTransitionError,
    NotFoundError,
    SeparationOfDutiesError,
    ValidationError,
)

_CAMPAIGN_COLS = (
    "id", "organization_id", "name", "status", "market", "segment",
    "start_date", "end_date", "artist_profile_id", "catalog_release_id",
    "created_by", "created_at", "updated_at",
)

_VALID_TRANSITIONS: dict[str, frozenset[str]] = {
    "draft": frozenset({"pending_approval", "canceled"}),
    "pending_approval": frozenset({"approved", "draft", "canceled"}),
    "approved": frozenset({"active", "canceled"}),
    "active": frozenset({"paused", "completed", "canceled"}),
    "paused": frozenset({"active", "completed", "canceled"}),
    "completed": frozenset(),
    "canceled": frozenset(),
}


def _next_id(conn: duckdb.DuckDBPyConnection, table: str) -> int:
    return int(conn.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table}").fetchone()[0])


def _now():
    return utc_now()


def _audit(
    conn: duckdb.DuckDBPyConnection,
    *,
    action: str,
    target_type: str,
    target_id: str,
    actor_user_id: Optional[int],
    organization_id: Optional[int] = None,
    previous_values: Optional[dict[str, Any]] = None,
    new_values: Optional[dict[str, Any]] = None,
    reason: Optional[str] = None,
    request_id: Optional[str] = None,
) -> None:
    try:
        from app.packages.organizations.infrastructure.repositories.audit_repository import (
            AuditRepository,
        )
        AuditRepository(conn).append(
            action=action,
            target_type=target_type,
            target_id=target_id,
            source="campaigns.use_case",
            result="success",
            actor_user_id=actor_user_id,
            organization_id=organization_id,
            previous_values=previous_values,
            new_values=new_values,
            reason=reason,
            request_id=request_id,
        )
    except Exception:
        pass


def _map_campaign(row: tuple) -> Campaign:
    return Campaign(**dict(zip(_CAMPAIGN_COLS, row)))


def _record_status_history(
    conn: duckdb.DuckDBPyConnection,
    *,
    campaign_id: int,
    organization_id: int,
    from_status: Optional[str],
    to_status: str,
    actor_user_id: Optional[int],
    reason: Optional[str] = None,
) -> None:
    now = _now()
    hid = _next_id(conn, "app_campaign_status_history")
    conn.execute(
        """
        INSERT INTO app_campaign_status_history
            (id, campaign_id, organization_id, from_status, to_status, reason,
             actor_user_id, at, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [hid, campaign_id, organization_id, from_status, to_status, reason,
         actor_user_id, now, now],
    )


class CampaignUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def _get_or_raise(self, campaign_id: int, organization_id: int) -> Campaign:
        row = self._conn.execute(
            f"SELECT {', '.join(_CAMPAIGN_COLS)} FROM app_campaign WHERE id = ? AND organization_id = ?",
            [campaign_id, organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"Campaign {campaign_id} not found")
        return _map_campaign(row)

    def create(
        self,
        *,
        actor_user_id: int,
        organization_id: int,
        name: str,
        market: Optional[str] = None,
        segment: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        artist_profile_id: Optional[int] = None,
        catalog_release_id: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> Campaign:
        if not name or not name.strip():
            raise ValidationError("Campaign name is required")
        now = _now()
        cid = _next_id(self._conn, "app_campaign")
        self._conn.execute(
            """
            INSERT INTO app_campaign
                (id, organization_id, name, status, market, segment, start_date, end_date,
                 artist_profile_id, catalog_release_id, created_by, created_at, updated_at)
            VALUES (?, ?, ?, 'draft', ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [cid, organization_id, name.strip(), market, segment, start_date, end_date,
             artist_profile_id, catalog_release_id, actor_user_id, now, now],
        )
        _record_status_history(
            self._conn, campaign_id=cid, organization_id=organization_id,
            from_status=None, to_status="draft", actor_user_id=actor_user_id,
        )
        _audit(self._conn, action="campaign.created", target_type="campaign",
               target_id=str(cid), actor_user_id=actor_user_id,
               organization_id=organization_id, new_values={"name": name},
               request_id=request_id)
        return self._get_or_raise(cid, organization_id)

    def update(
        self,
        campaign_id: int,
        organization_id: int,
        *,
        actor_user_id: int,
        name: Optional[str] = None,
        market: Optional[str] = None,
        segment: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        artist_profile_id: Optional[int] = None,
        catalog_release_id: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> Campaign:
        campaign = self._get_or_raise(campaign_id, organization_id)
        if campaign.status in ("completed", "canceled"):
            raise InvalidTransitionError(f"Cannot update campaign in status {campaign.status}")
        now = _now()
        new_name = name.strip() if name else campaign.name
        self._conn.execute(
            """
            UPDATE app_campaign SET
                name = ?, market = ?, segment = ?, start_date = ?, end_date = ?,
                artist_profile_id = ?, catalog_release_id = ?, updated_at = ?
            WHERE id = ? AND organization_id = ?
            """,
            [new_name, market if market is not None else campaign.market,
             segment if segment is not None else campaign.segment,
             start_date if start_date is not None else campaign.start_date,
             end_date if end_date is not None else campaign.end_date,
             artist_profile_id if artist_profile_id is not None else campaign.artist_profile_id,
             catalog_release_id if catalog_release_id is not None else campaign.catalog_release_id,
             now, campaign_id, organization_id],
        )
        _audit(self._conn, action="campaign.updated", target_type="campaign",
               target_id=str(campaign_id), actor_user_id=actor_user_id,
               organization_id=organization_id, request_id=request_id)
        return self._get_or_raise(campaign_id, organization_id)

    def _transition(
        self,
        campaign_id: int,
        organization_id: int,
        *,
        to_status: str,
        actor_user_id: int,
        reason: Optional[str] = None,
        request_id: Optional[str] = None,
        audit_action: str = "campaign.status_changed",
    ) -> Campaign:
        campaign = self._get_or_raise(campaign_id, organization_id)
        allowed = _VALID_TRANSITIONS.get(campaign.status, frozenset())
        if to_status not in allowed:
            raise InvalidTransitionError(
                f"Cannot transition from {campaign.status} to {to_status}"
            )
        now = _now()
        self._conn.execute(
            "UPDATE app_campaign SET status = ?, updated_at = ? WHERE id = ? AND organization_id = ?",
            [to_status, now, campaign_id, organization_id],
        )
        _record_status_history(
            self._conn, campaign_id=campaign_id, organization_id=organization_id,
            from_status=campaign.status, to_status=to_status,
            actor_user_id=actor_user_id, reason=reason,
        )
        _audit(self._conn, action=audit_action, target_type="campaign",
               target_id=str(campaign_id), actor_user_id=actor_user_id,
               organization_id=organization_id,
               previous_values={"status": campaign.status},
               new_values={"status": to_status}, reason=reason,
               request_id=request_id)
        return self._get_or_raise(campaign_id, organization_id)

    def submit_for_approval(
        self, campaign_id: int, organization_id: int, *, actor_user_id: int,
        request_id: Optional[str] = None,
    ) -> Campaign:
        return self._transition(
            campaign_id, organization_id, to_status="pending_approval",
            actor_user_id=actor_user_id, request_id=request_id,
            audit_action="campaign.submitted_for_approval",
        )

    def activate(
        self, campaign_id: int, organization_id: int, *, actor_user_id: int,
        request_id: Optional[str] = None,
    ) -> Campaign:
        return self._transition(
            campaign_id, organization_id, to_status="active",
            actor_user_id=actor_user_id, request_id=request_id,
            audit_action="campaign.activated",
        )

    def pause(
        self, campaign_id: int, organization_id: int, *, actor_user_id: int,
        request_id: Optional[str] = None,
    ) -> Campaign:
        return self._transition(
            campaign_id, organization_id, to_status="paused",
            actor_user_id=actor_user_id, request_id=request_id,
        )

    def complete(
        self, campaign_id: int, organization_id: int, *, actor_user_id: int,
        request_id: Optional[str] = None,
    ) -> Campaign:
        return self._transition(
            campaign_id, organization_id, to_status="completed",
            actor_user_id=actor_user_id, request_id=request_id,
            audit_action="campaign.completed",
        )

    def cancel(
        self, campaign_id: int, organization_id: int, *, actor_user_id: int,
        reason: Optional[str] = None, request_id: Optional[str] = None,
    ) -> Campaign:
        return self._transition(
            campaign_id, organization_id, to_status="canceled",
            actor_user_id=actor_user_id, reason=reason, request_id=request_id,
            audit_action="campaign.canceled",
        )

    def close(
        self, campaign_id: int, organization_id: int, *, actor_user_id: int,
        request_id: Optional[str] = None,
    ) -> Campaign:
        """Close = complete (campaign.close permission)."""
        campaign = self._get_or_raise(campaign_id, organization_id)
        if campaign.status == "completed":
            return campaign
        return self.complete(campaign_id, organization_id, actor_user_id=actor_user_id,
                             request_id=request_id)

    def list(
        self, organization_id: int, *, status: Optional[str] = None,
        limit: int = 25, offset: int = 0,
    ) -> tuple[list[Campaign], int]:
        where = "organization_id = ?"
        params: list[Any] = [organization_id]
        if status:
            where += " AND status = ?"
            params.append(status)
        total = int(self._conn.execute(
            f"SELECT COUNT(*) FROM app_campaign WHERE {where}", params
        ).fetchone()[0])
        rows = self._conn.execute(
            f"SELECT {', '.join(_CAMPAIGN_COLS)} FROM app_campaign WHERE {where} "
            f"ORDER BY id DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
        return [_map_campaign(r) for r in rows], total

    def get(self, campaign_id: int, organization_id: int) -> Campaign:
        return self._get_or_raise(campaign_id, organization_id)


class CampaignObjectiveUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def add(
        self, campaign_id: int, organization_id: int, *,
        objective_type: str, description: Optional[str] = None, priority: int = 1,
        actor_user_id: Optional[int] = None, request_id: Optional[str] = None,
    ) -> CampaignObjective:
        CampaignUseCases(self._conn).get(campaign_id, organization_id)
        now = _now()
        oid = _next_id(self._conn, "app_campaign_objective")
        self._conn.execute(
            """
            INSERT INTO app_campaign_objective
                (id, campaign_id, organization_id, objective_type, description, priority,
                 created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [oid, campaign_id, organization_id, objective_type, description, priority, now, now],
        )
        row = self._conn.execute(
            "SELECT id, campaign_id, organization_id, objective_type, description, priority, "
            "created_at, updated_at FROM app_campaign_objective WHERE id = ?",
            [oid],
        ).fetchone()
        _audit(self._conn, action="campaign_objective.added", target_type="campaign_objective",
               target_id=str(oid), actor_user_id=actor_user_id, organization_id=organization_id,
               request_id=request_id)
        return CampaignObjective(*row)

    def list(self, campaign_id: int, organization_id: int) -> list[CampaignObjective]:
        CampaignUseCases(self._conn).get(campaign_id, organization_id)
        rows = self._conn.execute(
            "SELECT id, campaign_id, organization_id, objective_type, description, priority, "
            "created_at, updated_at FROM app_campaign_objective "
            "WHERE campaign_id = ? AND organization_id = ? ORDER BY priority",
            [campaign_id, organization_id],
        ).fetchall()
        return [CampaignObjective(*r) for r in rows]


class CampaignTargetUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def set(
        self, campaign_id: int, organization_id: int, *,
        metric_code: str, target_value: float, unit: str = "count",
        actor_user_id: Optional[int] = None, request_id: Optional[str] = None,
    ) -> CampaignTarget:
        CampaignUseCases(self._conn).get(campaign_id, organization_id)
        now = _now()
        existing = self._conn.execute(
            "SELECT id FROM app_campaign_target WHERE campaign_id = ? AND metric_code = ?",
            [campaign_id, metric_code],
        ).fetchone()
        if existing:
            self._conn.execute(
                "UPDATE app_campaign_target SET target_value = ?, unit = ?, updated_at = ? WHERE id = ?",
                [target_value, unit, now, existing[0]],
            )
            tid = int(existing[0])
        else:
            tid = _next_id(self._conn, "app_campaign_target")
            self._conn.execute(
                """
                INSERT INTO app_campaign_target
                    (id, campaign_id, organization_id, metric_code, target_value, unit,
                     created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [tid, campaign_id, organization_id, metric_code, target_value, unit, now, now],
            )
        row = self._conn.execute(
            "SELECT id, campaign_id, organization_id, metric_code, target_value, unit, "
            "created_at, updated_at FROM app_campaign_target WHERE id = ?",
            [tid],
        ).fetchone()
        _audit(self._conn, action="campaign_target.set", target_type="campaign_target",
               target_id=str(tid), actor_user_id=actor_user_id, organization_id=organization_id,
               request_id=request_id)
        return CampaignTarget(*row)

    def list(self, campaign_id: int, organization_id: int) -> list[CampaignTarget]:
        CampaignUseCases(self._conn).get(campaign_id, organization_id)
        rows = self._conn.execute(
            "SELECT id, campaign_id, organization_id, metric_code, target_value, unit, "
            "created_at, updated_at FROM app_campaign_target "
            "WHERE campaign_id = ? AND organization_id = ?",
            [campaign_id, organization_id],
        ).fetchall()
        return [CampaignTarget(*r) for r in rows]


class CampaignBudgetUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def set(
        self, campaign_id: int, organization_id: int, *,
        amount: float, currency: str, approval_threshold: Optional[float] = None,
        actor_user_id: Optional[int] = None, request_id: Optional[str] = None,
    ) -> CampaignBudget:
        if amount <= 0:
            raise ValidationError("Budget amount must be positive")
        CampaignUseCases(self._conn).get(campaign_id, organization_id)
        now = _now()
        existing = self._conn.execute(
            "SELECT id FROM app_campaign_budget WHERE campaign_id = ?",
            [campaign_id],
        ).fetchone()
        if existing:
            self._conn.execute(
                """
                UPDATE app_campaign_budget SET amount = ?, currency = ?, approval_threshold = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                [amount, currency.upper(), approval_threshold, now, existing[0]],
            )
            bid = int(existing[0])
        else:
            bid = _next_id(self._conn, "app_campaign_budget")
            self._conn.execute(
                """
                INSERT INTO app_campaign_budget
                    (id, campaign_id, organization_id, amount, currency, approval_threshold,
                     override_approved, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, FALSE, ?, ?)
                """,
                [bid, campaign_id, organization_id, amount, currency.upper(),
                 approval_threshold, now, now],
            )
        row = self._conn.execute(
            "SELECT id, campaign_id, organization_id, amount, currency, approval_threshold, "
            "override_approved, override_reason, override_by, override_at, created_at, updated_at "
            "FROM app_campaign_budget WHERE id = ?",
            [bid],
        ).fetchone()
        _audit(self._conn, action="campaign_budget.set", target_type="campaign_budget",
               target_id=str(bid), actor_user_id=actor_user_id, organization_id=organization_id,
               request_id=request_id)
        return CampaignBudget(*row)

    def get(self, campaign_id: int, organization_id: int) -> Optional[CampaignBudget]:
        CampaignUseCases(self._conn).get(campaign_id, organization_id)
        row = self._conn.execute(
            "SELECT id, campaign_id, organization_id, amount, currency, approval_threshold, "
            "override_approved, override_reason, override_by, override_at, created_at, updated_at "
            "FROM app_campaign_budget WHERE campaign_id = ? AND organization_id = ?",
            [campaign_id, organization_id],
        ).fetchone()
        return CampaignBudget(*row) if row else None

    def _total_expenses(self, campaign_id: int) -> float:
        row = self._conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM app_campaign_expense WHERE campaign_id = ?",
            [campaign_id],
        ).fetchone()
        return float(row[0]) if row else 0.0


class CampaignApprovalUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def submit(
        self, campaign_id: int, organization_id: int, *,
        approval_type: str, actor_user_id: int, request_id: Optional[str] = None,
    ) -> CampaignApproval:
        CampaignUseCases(self._conn).get(campaign_id, organization_id)
        pending = self._conn.execute(
            "SELECT id FROM app_campaign_approval WHERE campaign_id = ? AND approval_type = ? "
            "AND status = 'pending'",
            [campaign_id, approval_type],
        ).fetchone()
        if pending:
            raise ApprovalStateError(f"Pending {approval_type} approval already exists")
        now = _now()
        aid = _next_id(self._conn, "app_campaign_approval")
        self._conn.execute(
            """
            INSERT INTO app_campaign_approval
                (id, campaign_id, organization_id, approval_type, status, requested_by,
                 requested_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, ?)
            """,
            [aid, campaign_id, organization_id, approval_type, actor_user_id, now, now, now],
        )
        if approval_type == "launch":
            campaign = CampaignUseCases(self._conn).get(campaign_id, organization_id)
            if campaign.status == "draft":
                CampaignUseCases(self._conn)._transition(
                    campaign_id, organization_id, to_status="pending_approval",
                    actor_user_id=actor_user_id, request_id=request_id,
                )
        row = self._conn.execute(
            "SELECT id, campaign_id, organization_id, approval_type, status, requested_by, "
            "decided_by, decision_reason, requested_at, decided_at, created_at, updated_at "
            "FROM app_campaign_approval WHERE id = ?",
            [aid],
        ).fetchone()
        _audit(self._conn, action="campaign_approval.submitted", target_type="campaign_approval",
               target_id=str(aid), actor_user_id=actor_user_id, organization_id=organization_id,
               request_id=request_id)
        return CampaignApproval(*row)

    def decide(
        self, approval_id: int, organization_id: int, *,
        approved: bool, actor_user_id: int, reason: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> CampaignApproval:
        row = self._conn.execute(
            "SELECT id, campaign_id, organization_id, approval_type, status, requested_by, "
            "decided_by, decision_reason, requested_at, decided_at, created_at, updated_at "
            "FROM app_campaign_approval WHERE id = ? AND organization_id = ?",
            [approval_id, organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"Approval {approval_id} not found")
        approval = CampaignApproval(*row)
        if approval.status != "pending":
            raise ApprovalStateError("Approval is not pending")
        if approval.requested_by == actor_user_id:
            raise SeparationOfDutiesError("Approver cannot be the same as requester")
        now = _now()
        new_status = "approved" if approved else "rejected"
        self._conn.execute(
            """
            UPDATE app_campaign_approval SET status = ?, decided_by = ?, decision_reason = ?,
                decided_at = ?, updated_at = ?
            WHERE id = ?
            """,
            [new_status, actor_user_id, reason, now, now, approval_id],
        )
        if approval.approval_type == "launch" and approved:
            CampaignUseCases(self._conn)._transition(
                approval.campaign_id, organization_id, to_status="approved",
                actor_user_id=actor_user_id, reason=reason, request_id=request_id,
            )
        elif approval.approval_type == "launch" and not approved:
            CampaignUseCases(self._conn)._transition(
                approval.campaign_id, organization_id, to_status="draft",
                actor_user_id=actor_user_id, reason=reason, request_id=request_id,
            )
        elif approval.approval_type in ("budget_override", "expense_override") and approved:
            self._conn.execute(
                """
                UPDATE app_campaign_budget SET override_approved = TRUE, override_reason = ?,
                    override_by = ?, override_at = ?, updated_at = ?
                WHERE campaign_id = ?
                """,
                [reason, actor_user_id, now, now, approval.campaign_id],
            )
        row2 = self._conn.execute(
            "SELECT id, campaign_id, organization_id, approval_type, status, requested_by, "
            "decided_by, decision_reason, requested_at, decided_at, created_at, updated_at "
            "FROM app_campaign_approval WHERE id = ?",
            [approval_id],
        ).fetchone()
        _audit(self._conn, action=f"campaign_approval.{new_status}", target_type="campaign_approval",
               target_id=str(approval_id), actor_user_id=actor_user_id,
               organization_id=organization_id, reason=reason, request_id=request_id)
        return CampaignApproval(*row2)

    def list(self, campaign_id: int, organization_id: int) -> list[CampaignApproval]:
        CampaignUseCases(self._conn).get(campaign_id, organization_id)
        rows = self._conn.execute(
            "SELECT id, campaign_id, organization_id, approval_type, status, requested_by, "
            "decided_by, decision_reason, requested_at, decided_at, created_at, updated_at "
            "FROM app_campaign_approval WHERE campaign_id = ? AND organization_id = ? "
            "ORDER BY id DESC",
            [campaign_id, organization_id],
        ).fetchall()
        return [CampaignApproval(*r) for r in rows]


class CampaignExpenseUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def add(
        self, campaign_id: int, organization_id: int, *,
        amount: float, currency: str, category: str, expense_date: date,
        description: Optional[str] = None, actor_user_id: int,
        override_id: Optional[int] = None, request_id: Optional[str] = None,
    ) -> CampaignExpense:
        if amount <= 0:
            raise ValidationError("Expense amount must be positive")
        CampaignUseCases(self._conn).get(campaign_id, organization_id)
        budget_uc = CampaignBudgetUseCases(self._conn)
        budget = budget_uc.get(campaign_id, organization_id)
        if budget:
            total = budget_uc._total_expenses(campaign_id)
            if total + amount > budget.amount and not budget.override_approved and not override_id:
                raise BudgetExceededError(
                    f"Expense would exceed budget ({total + amount:.2f} > {budget.amount:.2f})"
                )
            if override_id:
                appr = self._conn.execute(
                    "SELECT status FROM app_campaign_approval WHERE id = ? AND campaign_id = ?",
                    [override_id, campaign_id],
                ).fetchone()
                if not appr or appr[0] != "approved":
                    raise ApprovalStateError("Expense override approval not approved")
        now = _now()
        eid = _next_id(self._conn, "app_campaign_expense")
        self._conn.execute(
            """
            INSERT INTO app_campaign_expense
                (id, campaign_id, organization_id, amount, currency, category, description,
                 expense_date, recorded_by, override_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [eid, campaign_id, organization_id, amount, currency.upper(), category,
             description, expense_date, actor_user_id, override_id, now, now],
        )
        row = self._conn.execute(
            "SELECT id, campaign_id, organization_id, amount, currency, category, description, "
            "expense_date, recorded_by, override_id, created_at, updated_at "
            "FROM app_campaign_expense WHERE id = ?",
            [eid],
        ).fetchone()
        _audit(self._conn, action="campaign_expense.added", target_type="campaign_expense",
               target_id=str(eid), actor_user_id=actor_user_id, organization_id=organization_id,
               request_id=request_id)
        return CampaignExpense(*row)

    def list(self, campaign_id: int, organization_id: int) -> list[CampaignExpense]:
        CampaignUseCases(self._conn).get(campaign_id, organization_id)
        rows = self._conn.execute(
            "SELECT id, campaign_id, organization_id, amount, currency, category, description, "
            "expense_date, recorded_by, override_id, created_at, updated_at "
            "FROM app_campaign_expense WHERE campaign_id = ? AND organization_id = ? "
            "ORDER BY expense_date DESC",
            [campaign_id, organization_id],
        ).fetchall()
        return [CampaignExpense(*r) for r in rows]


class CampaignResultUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def record(
        self, campaign_id: int, organization_id: int, *,
        metric_code: str, value: float, unit: str = "count",
        is_monetary: bool = False, period_start: Optional[date] = None,
        period_end: Optional[date] = None, source_label: Optional[str] = None,
        actor_user_id: Optional[int] = None, request_id: Optional[str] = None,
    ) -> CampaignResult:
        CampaignUseCases(self._conn).get(campaign_id, organization_id)
        now = _now()
        rid = _next_id(self._conn, "app_campaign_result")
        self._conn.execute(
            """
            INSERT INTO app_campaign_result
                (id, campaign_id, organization_id, metric_code, value, unit, is_monetary,
                 period_start, period_end, source_label, recorded_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [rid, campaign_id, organization_id, metric_code, value, unit, is_monetary,
             period_start, period_end, source_label, now, now, now],
        )
        row = self._conn.execute(
            "SELECT id, campaign_id, organization_id, metric_code, value, unit, is_monetary, "
            "period_start, period_end, source_label, recorded_at, created_at, updated_at "
            "FROM app_campaign_result WHERE id = ?",
            [rid],
        ).fetchone()
        _audit(self._conn, action="campaign_result.recorded", target_type="campaign_result",
               target_id=str(rid), actor_user_id=actor_user_id, organization_id=organization_id,
               request_id=request_id)
        return CampaignResult(*row)

    def list(self, campaign_id: int, organization_id: int) -> list[CampaignResult]:
        CampaignUseCases(self._conn).get(campaign_id, organization_id)
        rows = self._conn.execute(
            "SELECT id, campaign_id, organization_id, metric_code, value, unit, is_monetary, "
            "period_start, period_end, source_label, recorded_at, created_at, updated_at "
            "FROM app_campaign_result WHERE campaign_id = ? AND organization_id = ?",
            [campaign_id, organization_id],
        ).fetchall()
        return [CampaignResult(*r) for r in rows]


class AttributionDefinitionUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def create(
        self, campaign_id: int, organization_id: int, *,
        model_code: str, confidence: float, responsible: str,
        description: Optional[str] = None, actor_user_id: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> AttributionDefinition:
        CampaignUseCases(self._conn).get(campaign_id, organization_id)
        if not (0 <= confidence <= 1):
            raise ValidationError("Confidence must be between 0 and 1")
        now = _now()
        max_ver = self._conn.execute(
            "SELECT COALESCE(MAX(version), 0) FROM app_attribution_definition WHERE campaign_id = ?",
            [campaign_id],
        ).fetchone()[0]
        did = _next_id(self._conn, "app_attribution_definition")
        self._conn.execute(
            """
            INSERT INTO app_attribution_definition
                (id, campaign_id, organization_id, version, model_code, description,
                 confidence, responsible, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'draft', ?, ?)
            """,
            [did, campaign_id, organization_id, int(max_ver) + 1, model_code,
             description, confidence, responsible, now, now],
        )
        row = self._conn.execute(
            "SELECT id, campaign_id, organization_id, version, model_code, description, "
            "confidence, responsible, status, approved_by, approved_at, created_at, updated_at "
            "FROM app_attribution_definition WHERE id = ?",
            [did],
        ).fetchone()
        _audit(self._conn, action="attribution_definition.created",
               target_type="attribution_definition", target_id=str(did),
               actor_user_id=actor_user_id, organization_id=organization_id,
               request_id=request_id)
        return AttributionDefinition(*row)

    def approve(
        self, definition_id: int, organization_id: int, *, actor_user_id: int,
        request_id: Optional[str] = None,
    ) -> AttributionDefinition:
        row = self._conn.execute(
            "SELECT id, campaign_id, organization_id, version, model_code, description, "
            "confidence, responsible, status, approved_by, approved_at, created_at, updated_at "
            "FROM app_attribution_definition WHERE id = ? AND organization_id = ?",
            [definition_id, organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"Attribution definition {definition_id} not found")
        if row[8] != "draft":
            raise ApprovalStateError("Attribution definition is not draft")
        now = _now()
        self._conn.execute(
            "UPDATE app_attribution_definition SET status = 'approved', approved_by = ?, "
            "approved_at = ?, updated_at = ? WHERE id = ?",
            [actor_user_id, now, now, definition_id],
        )
        row2 = self._conn.execute(
            "SELECT id, campaign_id, organization_id, version, model_code, description, "
            "confidence, responsible, status, approved_by, approved_at, created_at, updated_at "
            "FROM app_attribution_definition WHERE id = ?",
            [definition_id],
        ).fetchone()
        return AttributionDefinition(*row2)

    def get_latest_approved(
        self, campaign_id: int, organization_id: int,
    ) -> Optional[AttributionDefinition]:
        row = self._conn.execute(
            "SELECT id, campaign_id, organization_id, version, model_code, description, "
            "confidence, responsible, status, approved_by, approved_at, created_at, updated_at "
            "FROM app_attribution_definition WHERE campaign_id = ? AND organization_id = ? "
            "AND status = 'approved' ORDER BY version DESC LIMIT 1",
            [campaign_id, organization_id],
        ).fetchone()
        return AttributionDefinition(*row) if row else None


class AttributableRevenueUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def record(
        self, campaign_id: int, organization_id: int, *,
        attribution_definition_id: int, amount: float, currency: str,
        period_start: date, period_end: date,
        actor_user_id: Optional[int] = None, request_id: Optional[str] = None,
    ) -> AttributableRevenueRecord:
        CampaignUseCases(self._conn).get(campaign_id, organization_id)
        now = _now()
        rid = _next_id(self._conn, "app_attributable_revenue_record")
        self._conn.execute(
            """
            INSERT INTO app_attributable_revenue_record
                (id, campaign_id, organization_id, attribution_definition_id, amount, currency,
                 period_start, period_end, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
            """,
            [rid, campaign_id, organization_id, attribution_definition_id, amount,
             currency.upper(), period_start, period_end, now, now],
        )
        row = self._conn.execute(
            "SELECT id, campaign_id, organization_id, attribution_definition_id, amount, currency, "
            "period_start, period_end, status, approved_by, approved_at, created_at, updated_at "
            "FROM app_attributable_revenue_record WHERE id = ?",
            [rid],
        ).fetchone()
        return AttributableRevenueRecord(*row)

    def approve(
        self, record_id: int, organization_id: int, *, actor_user_id: int,
        request_id: Optional[str] = None,
    ) -> AttributableRevenueRecord:
        row = self._conn.execute(
            "SELECT id, campaign_id, organization_id, attribution_definition_id, amount, currency, "
            "period_start, period_end, status, approved_by, approved_at, created_at, updated_at "
            "FROM app_attributable_revenue_record WHERE id = ? AND organization_id = ?",
            [record_id, organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError(f"Revenue record {record_id} not found")
        if row[8] != "pending":
            raise ApprovalStateError("Revenue record is not pending")
        now = _now()
        self._conn.execute(
            "UPDATE app_attributable_revenue_record SET status = 'approved', approved_by = ?, "
            "approved_at = ?, updated_at = ? WHERE id = ?",
            [actor_user_id, now, now, record_id],
        )
        row2 = self._conn.execute(
            "SELECT id, campaign_id, organization_id, attribution_definition_id, amount, currency, "
            "period_start, period_end, status, approved_by, approved_at, created_at, updated_at "
            "FROM app_attributable_revenue_record WHERE id = ?",
            [record_id],
        ).fetchone()
        _audit(self._conn, action="attributable_revenue.approved",
               target_type="attributable_revenue_record", target_id=str(record_id),
               actor_user_id=actor_user_id, organization_id=organization_id,
               request_id=request_id)
        return AttributableRevenueRecord(*row2)

    def list(self, campaign_id: int, organization_id: int) -> list[AttributableRevenueRecord]:
        rows = self._conn.execute(
            "SELECT id, campaign_id, organization_id, attribution_definition_id, amount, currency, "
            "period_start, period_end, status, approved_by, approved_at, created_at, updated_at "
            "FROM app_attributable_revenue_record WHERE campaign_id = ? AND organization_id = ?",
            [campaign_id, organization_id],
        ).fetchall()
        return [AttributableRevenueRecord(*r) for r in rows]


class CampaignRoiUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def compute_snapshot(
        self, campaign_id: int, organization_id: int, *,
        actor_user_id: Optional[int] = None, request_id: Optional[str] = None,
    ) -> CampaignRoiSnapshot:
        campaign = CampaignUseCases(self._conn).get(campaign_id, organization_id)
        now = _now()
        reasons: list[str] = []

        attr_def = AttributionDefinitionUseCases(self._conn).get_latest_approved(
            campaign_id, organization_id
        )
        revenue_rows = self._conn.execute(
            "SELECT amount, currency, period_start, period_end, attribution_definition_id "
            "FROM app_attributable_revenue_record WHERE campaign_id = ? AND status = 'approved'",
            [campaign_id],
        ).fetchall()
        expense_rows = self._conn.execute(
            "SELECT amount, currency FROM app_campaign_expense WHERE campaign_id = ?",
            [campaign_id],
        ).fetchall()
        budget = CampaignBudgetUseCases(self._conn).get(campaign_id, organization_id)
        targets = CampaignTargetUseCases(self._conn).list(campaign_id, organization_id)
        results = CampaignResultUseCases(self._conn).list(campaign_id, organization_id)

        total_expenses = sum(r[0] for r in expense_rows) if expense_rows else 0.0
        expense_currency = expense_rows[0][1] if expense_rows else None
        total_revenue = sum(r[0] for r in revenue_rows) if revenue_rows else 0.0
        revenue_currency = revenue_rows[0][1] if revenue_rows else None

        period_start = campaign.start_date
        period_end = campaign.end_date
        currency = budget.currency if budget else (revenue_currency or expense_currency)

        roi_available = True
        if not revenue_rows:
            roi_available = False
            reasons.append("no_approved_attributable_revenue")
        if not expense_rows:
            roi_available = False
            reasons.append("no_valid_expenses")
        if not attr_def:
            roi_available = False
            reasons.append("no_approved_attribution_definition")
        elif not attr_def.responsible:
            roi_available = False
            reasons.append("missing_responsible")
        if revenue_currency and expense_currency and revenue_currency != expense_currency:
            roi_available = False
            reasons.append("currency_mismatch")
        if budget and budget.currency and revenue_currency and budget.currency != revenue_currency:
            roi_available = False
            reasons.append("budget_currency_mismatch")
        if not period_start or not period_end:
            roi_available = False
            reasons.append("missing_campaign_period")
        for rev in revenue_rows:
            if rev[2] != period_start or rev[3] != period_end:
                roi_available = False
                reasons.append("revenue_period_mismatch")
                break
            if attr_def and rev[4] != attr_def.id:
                roi_available = False
                reasons.append("attribution_definition_mismatch")
                break

        roi_value: Optional[float] = None
        unavailable_reason: Optional[str] = None
        status = "available" if roi_available else "unavailable"
        if roi_available and total_expenses > 0:
            roi_value = (total_revenue - total_expenses) / total_expenses
        elif not roi_available:
            unavailable_reason = ";".join(reasons)

        cost_per_result: Optional[float] = None
        non_monetary = [r for r in results if not r.is_monetary and r.value > 0]
        if total_expenses > 0 and non_monetary:
            cost_per_result = total_expenses / sum(r.value for r in non_monetary)

        budget_utilization: Optional[float] = None
        if budget and budget.amount > 0:
            budget_utilization = total_expenses / budget.amount

        goal_attainment: Optional[float] = None
        if targets and results:
            target = targets[0]
            matching = [r for r in results if r.metric_code == target.metric_code and not r.is_monetary]
            if matching and target.target_value > 0:
                goal_attainment = matching[0].value / target.target_value

        engagement_lift: Optional[float] = None
        stream_results = [r for r in results if r.metric_code == "streams" and not r.is_monetary]
        if stream_results:
            engagement_lift = stream_results[0].value

        sid = _next_id(self._conn, "app_campaign_roi_snapshot")
        self._conn.execute(
            """
            INSERT INTO app_campaign_roi_snapshot
                (id, campaign_id, organization_id, attribution_definition_id, period_start,
                 period_end, currency, status, roi_value, unavailable_reason, cost_per_result,
                 budget_utilization, goal_attainment, engagement_lift, computed_at, computed_by,
                 created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [sid, campaign_id, organization_id,
             attr_def.id if attr_def else None, period_start, period_end, currency,
             status, roi_value, unavailable_reason, cost_per_result, budget_utilization,
             goal_attainment, engagement_lift, now, actor_user_id, now],
        )
        row = self._conn.execute(
            "SELECT id, campaign_id, organization_id, attribution_definition_id, period_start, "
            "period_end, currency, status, roi_value, unavailable_reason, cost_per_result, "
            "budget_utilization, goal_attainment, engagement_lift, computed_at, computed_by, "
            "created_at FROM app_campaign_roi_snapshot WHERE id = ?",
            [sid],
        ).fetchone()
        _audit(self._conn, action="campaign_roi.computed", target_type="campaign_roi_snapshot",
               target_id=str(sid), actor_user_id=actor_user_id, organization_id=organization_id,
               new_values={"status": status, "roi_value": roi_value},
               request_id=request_id)
        return CampaignRoiSnapshot(*row)

    def get_latest(self, campaign_id: int, organization_id: int) -> Optional[CampaignRoiSnapshot]:
        CampaignUseCases(self._conn).get(campaign_id, organization_id)
        row = self._conn.execute(
            "SELECT id, campaign_id, organization_id, attribution_definition_id, period_start, "
            "period_end, currency, status, roi_value, unavailable_reason, cost_per_result, "
            "budget_utilization, goal_attainment, engagement_lift, computed_at, computed_by, "
            "created_at FROM app_campaign_roi_snapshot WHERE campaign_id = ? AND organization_id = ? "
            "ORDER BY id DESC LIMIT 1",
            [campaign_id, organization_id],
        ).fetchone()
        return CampaignRoiSnapshot(*row) if row else None


class CampaignHistoryUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def get(self, campaign_id: int, organization_id: int) -> list[CampaignStatusHistoryEntry]:
        CampaignUseCases(self._conn).get(campaign_id, organization_id)
        rows = self._conn.execute(
            "SELECT id, campaign_id, organization_id, from_status, to_status, reason, "
            "actor_user_id, at, created_at FROM app_campaign_status_history "
            "WHERE campaign_id = ? AND organization_id = ? ORDER BY at",
            [campaign_id, organization_id],
        ).fetchall()
        return [CampaignStatusHistoryEntry(*r) for r in rows]
