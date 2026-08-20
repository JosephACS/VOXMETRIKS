"""Customer Success & Support use cases — Spec 025."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Any, Optional

import duckdb

from app.core.time_util import utc_now
from app.packages.customer_success.domain.entities import (
    CustomerIntervention,
    CustomerOnboarding,
    CustomerRisk,
    ExpansionOpportunity,
    HealthDefinition,
    HealthSnapshot,
    OnboardingStep,
    RenewalReadiness,
    SupportCase,
    SupportMessage,
    SupportSatisfaction,
    SupportSlaEvent,
)
from app.packages.customer_success.domain.errors import NotFoundError, StateError, ValidationError


def _next_id(conn: duckdb.DuckDBPyConnection, table: str) -> int:
    return int(conn.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table}").fetchone()[0])


def _now() -> datetime:
    return utc_now()


def _audit(conn, **kwargs) -> None:
    try:
        from app.packages.organizations.infrastructure.repositories.audit_repository import (
            AuditRepository,
        )
        AuditRepository(conn).append(source="customer_success.use_case", result="success", **kwargs)
    except Exception:
        pass


DEFAULT_STEPS = (
    ("kickoff", "Kickoff call"),
    ("data_access", "Grant data access"),
    ("training", "User training"),
    ("go_live", "Go-live checklist"),
)


class OnboardingUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def create(self, *, organization_id: int, actor_user_id: Optional[int] = None, request_id: Optional[str] = None) -> CustomerOnboarding:
        now = _now()
        oid = _next_id(self._conn, "app_customer_onboarding")
        self._conn.execute(
            """
            INSERT INTO app_customer_onboarding
                (id, organization_id, status, started_at, completed_at, created_by, created_at, updated_at)
            VALUES (?, ?, 'in_progress', ?, NULL, ?, ?, ?)
            """,
            [oid, organization_id, now, actor_user_id, now, now],
        )
        for i, (code, title) in enumerate(DEFAULT_STEPS):
            sid = _next_id(self._conn, "app_customer_onboarding_step")
            self._conn.execute(
                """
                INSERT INTO app_customer_onboarding_step
                    (id, onboarding_id, step_code, title, status, blocked_reason, completed_at, sort_order)
                VALUES (?, ?, ?, ?, 'pending', NULL, NULL, ?)
                """,
                [sid, oid, code, title, i],
            )
        _audit(self._conn, action="cs.onboarding.created", target_type="customer_onboarding",
               target_id=str(oid), actor_user_id=actor_user_id, organization_id=organization_id, request_id=request_id)
        return self.get(organization_id, oid)

    def get(self, organization_id: int, onboarding_id: int) -> CustomerOnboarding:
        row = self._conn.execute(
            """
            SELECT id, organization_id, status, started_at, completed_at, created_by, created_at, updated_at
            FROM app_customer_onboarding WHERE id = ? AND organization_id = ?
            """,
            [onboarding_id, organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError("Onboarding not found")
        return CustomerOnboarding(*row)

    def list_steps(self, organization_id: int, onboarding_id: int) -> list[OnboardingStep]:
        self.get(organization_id, onboarding_id)
        rows = self._conn.execute(
            """
            SELECT id, onboarding_id, step_code, title, status, blocked_reason, completed_at, sort_order
            FROM app_customer_onboarding_step WHERE onboarding_id = ? ORDER BY sort_order
            """,
            [onboarding_id],
        ).fetchall()
        return [OnboardingStep(*r) for r in rows]

    def complete_step(self, *, organization_id: int, onboarding_id: int, step_id: int, actor_user_id: Optional[int] = None, request_id: Optional[str] = None) -> OnboardingStep:
        self.get(organization_id, onboarding_id)
        row = self._conn.execute(
            "SELECT id, onboarding_id, step_code, title, status, blocked_reason, completed_at, sort_order FROM app_customer_onboarding_step WHERE id = ? AND onboarding_id = ?",
            [step_id, onboarding_id],
        ).fetchone()
        if not row:
            raise NotFoundError("Step not found")
        now = _now()
        self._conn.execute(
            "UPDATE app_customer_onboarding_step SET status = 'completed', completed_at = ?, blocked_reason = NULL WHERE id = ?",
            [now, step_id],
        )
        pending = self._conn.execute(
            "SELECT COUNT(*) FROM app_customer_onboarding_step WHERE onboarding_id = ? AND status != 'completed'",
            [onboarding_id],
        ).fetchone()[0]
        if int(pending) == 0:
            self._conn.execute(
                "UPDATE app_customer_onboarding SET status = 'completed', completed_at = ?, updated_at = ? WHERE id = ?",
                [now, now, onboarding_id],
            )
        else:
            self._conn.execute(
                "UPDATE app_customer_onboarding SET status = 'in_progress', updated_at = ? WHERE id = ?",
                [now, onboarding_id],
            )
        _audit(self._conn, action="cs.onboarding.step.completed", target_type="onboarding_step",
               target_id=str(step_id), actor_user_id=actor_user_id, organization_id=organization_id, request_id=request_id)
        return self.list_steps(organization_id, onboarding_id)[0] if False else OnboardingStep(
            *self._conn.execute(
                "SELECT id, onboarding_id, step_code, title, status, blocked_reason, completed_at, sort_order FROM app_customer_onboarding_step WHERE id = ?",
                [step_id],
            ).fetchone()
        )

    def block_step(self, *, organization_id: int, onboarding_id: int, step_id: int, reason: str, actor_user_id: Optional[int] = None, request_id: Optional[str] = None) -> OnboardingStep:
        self.get(organization_id, onboarding_id)
        now = _now()
        self._conn.execute(
            "UPDATE app_customer_onboarding_step SET status = 'blocked', blocked_reason = ? WHERE id = ? AND onboarding_id = ?",
            [reason, step_id, onboarding_id],
        )
        self._conn.execute(
            "UPDATE app_customer_onboarding SET status = 'blocked', updated_at = ? WHERE id = ?",
            [now, onboarding_id],
        )
        row = self._conn.execute(
            "SELECT id, onboarding_id, step_code, title, status, blocked_reason, completed_at, sort_order FROM app_customer_onboarding_step WHERE id = ?",
            [step_id],
        ).fetchone()
        if not row:
            raise NotFoundError("Step not found")
        _audit(self._conn, action="cs.onboarding.step.blocked", target_type="onboarding_step",
               target_id=str(step_id), actor_user_id=actor_user_id, organization_id=organization_id, request_id=request_id)
        return OnboardingStep(*row)


class HealthUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def get_active_definition(self) -> HealthDefinition:
        row = self._conn.execute(
            """
            SELECT id, organization_id, code, version, name, formula_json, weights_json,
                   null_handling, status, limitations, created_at
            FROM app_customer_health_definition WHERE status = 'active' ORDER BY version DESC LIMIT 1
            """
        ).fetchone()
        if not row:
            raise NotFoundError("Health definition not found")
        return HealthDefinition(*row)

    def calculate(self, *, organization_id: int, actor_user_id: Optional[int] = None, request_id: Optional[str] = None) -> HealthSnapshot:
        definition = self.get_active_definition()
        weights = json.loads(definition.weights_json)
        components: dict[str, Any] = {}
        missing = False

        # subscription_active
        sub_active = None
        try:
            row = self._conn.execute(
                "SELECT COUNT(*) FROM app_subscription WHERE organization_id = ? AND status IN ('active','trialing')",
                [organization_id],
            ).fetchone()
            sub_active = 1.0 if row and int(row[0]) > 0 else 0.0
        except Exception:
            missing = True
        components["subscription_active"] = {"value": sub_active, "available": sub_active is not None}

        # open_risks (invert: fewer risks = healthier)
        risk_score = None
        try:
            row = self._conn.execute(
                "SELECT COUNT(*) FROM app_customer_risk WHERE organization_id = ? AND status IN ('open','intervention_required')",
                [organization_id],
            ).fetchone()
            open_risks = int(row[0]) if row else 0
            risk_score = max(0.0, 1.0 - (0.25 * open_risks))
            components["open_risks"] = {"open_count": open_risks, "value": risk_score, "available": True}
        except Exception:
            missing = True
            components["open_risks"] = {"value": None, "available": False}

        # support_open
        support_score = None
        try:
            row = self._conn.execute(
                "SELECT COUNT(*) FROM app_support_case WHERE organization_id = ? AND status NOT IN ('resolved','closed')",
                [organization_id],
            ).fetchone()
            open_cases = int(row[0]) if row else 0
            support_score = max(0.0, 1.0 - (0.2 * open_cases))
            components["support_open"] = {"open_count": open_cases, "value": support_score, "available": True}
        except Exception:
            missing = True
            components["support_open"] = {"value": None, "available": False}

        if sub_active is None and risk_score is None and support_score is None:
            score = None
            score_state = "No disponible"
            confidence = None
            limitations = "Insufficient data — no inputs available. Not an AI score."
        else:
            total_w = 0.0
            acc = 0.0
            for key, w in weights.items():
                val = components.get(key, {}).get("value")
                if val is None:
                    missing = True
                    continue
                total_w += float(w)
                acc += float(w) * float(val)
            if total_w <= 0:
                score = None
                score_state = "insufficient_data"
                confidence = 0.0
                limitations = "All weighted inputs unavailable."
            else:
                score = round(acc / total_w, 4)
                confidence = round(total_w / sum(float(v) for v in weights.values()), 4)
                if score >= 0.75:
                    score_state = "healthy"
                elif score >= 0.5:
                    score_state = "watch"
                elif score >= 0.25:
                    score_state = "risk"
                else:
                    score_state = "critical"
                limitations = definition.limitations + (" Partial inputs." if missing else "")

        now = _now()
        sid = _next_id(self._conn, "app_customer_health_snapshot")
        self._conn.execute(
            """
            INSERT INTO app_customer_health_snapshot
                (id, organization_id, definition_id, score, score_state, confidence,
                 components_json, limitations, generated_at, generated_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                sid, organization_id, definition.id, score, score_state, confidence,
                json.dumps(components), limitations, now, actor_user_id,
            ],
        )
        _audit(self._conn, action="cs.health.calculated", target_type="health_snapshot",
               target_id=str(sid), actor_user_id=actor_user_id, organization_id=organization_id, request_id=request_id)
        return self.get_snapshot(organization_id, sid)

    def get_snapshot(self, organization_id: int, snapshot_id: int) -> HealthSnapshot:
        row = self._conn.execute(
            """
            SELECT id, organization_id, definition_id, score, score_state, confidence,
                   components_json, limitations, generated_at, generated_by
            FROM app_customer_health_snapshot WHERE id = ? AND organization_id = ?
            """,
            [snapshot_id, organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError("Health snapshot not found")
        return HealthSnapshot(*row)

    def latest(self, organization_id: int) -> Optional[HealthSnapshot]:
        row = self._conn.execute(
            """
            SELECT id, organization_id, definition_id, score, score_state, confidence,
                   components_json, limitations, generated_at, generated_by
            FROM app_customer_health_snapshot WHERE organization_id = ?
            ORDER BY id DESC LIMIT 1
            """,
            [organization_id],
        ).fetchone()
        return HealthSnapshot(*row) if row else None


class RiskUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def create(self, *, organization_id: int, title: str, description: str = "", severity: str = "medium", actor_user_id: Optional[int] = None, request_id: Optional[str] = None) -> CustomerRisk:
        now = _now()
        rid = _next_id(self._conn, "app_customer_risk")
        self._conn.execute(
            """
            INSERT INTO app_customer_risk
                (id, organization_id, title, status, severity, description, created_by, created_at, updated_at)
            VALUES (?, ?, ?, 'open', ?, ?, ?, ?, ?)
            """,
            [rid, organization_id, title.strip(), severity, description, actor_user_id, now, now],
        )
        _audit(self._conn, action="cs.risk.created", target_type="customer_risk", target_id=str(rid),
               actor_user_id=actor_user_id, organization_id=organization_id, request_id=request_id)
        return self.get(organization_id, rid)

    def get(self, organization_id: int, risk_id: int) -> CustomerRisk:
        row = self._conn.execute(
            "SELECT id, organization_id, title, status, severity, description, created_by, created_at, updated_at FROM app_customer_risk WHERE id = ? AND organization_id = ?",
            [risk_id, organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError("Risk not found")
        return CustomerRisk(*row)

    def list(self, organization_id: int) -> list[CustomerRisk]:
        rows = self._conn.execute(
            "SELECT id, organization_id, title, status, severity, description, created_by, created_at, updated_at FROM app_customer_risk WHERE organization_id = ? ORDER BY id DESC",
            [organization_id],
        ).fetchall()
        return [CustomerRisk(*r) for r in rows]


class InterventionUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def assign(self, *, organization_id: int, title: str, risk_id: Optional[int] = None, assignee_user_id: Optional[int] = None, actor_user_id: Optional[int] = None, request_id: Optional[str] = None) -> CustomerIntervention:
        if risk_id is not None:
            RiskUseCases(self._conn).get(organization_id, risk_id)
            self._conn.execute(
                "UPDATE app_customer_risk SET status = 'intervention_required', updated_at = ? WHERE id = ?",
                [_now(), risk_id],
            )
        now = _now()
        iid = _next_id(self._conn, "app_customer_intervention")
        self._conn.execute(
            """
            INSERT INTO app_customer_intervention
                (id, organization_id, risk_id, title, status, assignee_user_id, completed_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'planned', ?, NULL, ?, ?)
            """,
            [iid, organization_id, risk_id, title.strip(), assignee_user_id, now, now],
        )
        _audit(self._conn, action="cs.intervention.assigned", target_type="customer_intervention",
               target_id=str(iid), actor_user_id=actor_user_id, organization_id=organization_id, request_id=request_id)
        return self.get(organization_id, iid)

    def list(self, organization_id: int) -> list[CustomerIntervention]:
        rows = self._conn.execute(
            "SELECT id, organization_id, risk_id, title, status, assignee_user_id, completed_at, created_at, updated_at "
            "FROM app_customer_intervention WHERE organization_id = ? ORDER BY id DESC",
            [organization_id],
        ).fetchall()
        return [CustomerIntervention(*r) for r in rows]

    def get(self, organization_id: int, intervention_id: int) -> CustomerIntervention:
        row = self._conn.execute(
            "SELECT id, organization_id, risk_id, title, status, assignee_user_id, completed_at, created_at, updated_at FROM app_customer_intervention WHERE id = ? AND organization_id = ?",
            [intervention_id, organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError("Intervention not found")
        return CustomerIntervention(*row)

    def complete(self, *, organization_id: int, intervention_id: int, actor_user_id: Optional[int] = None, request_id: Optional[str] = None) -> CustomerIntervention:
        iv = self.get(organization_id, intervention_id)
        if iv.status in ("completed", "canceled"):
            raise StateError("Already closed")
        now = _now()
        self._conn.execute(
            "UPDATE app_customer_intervention SET status = 'completed', completed_at = ?, updated_at = ? WHERE id = ?",
            [now, now, intervention_id],
        )
        if iv.risk_id:
            self._conn.execute(
                "UPDATE app_customer_risk SET status = 'mitigated', updated_at = ? WHERE id = ?",
                [now, iv.risk_id],
            )
        _audit(self._conn, action="cs.intervention.completed", target_type="customer_intervention",
               target_id=str(intervention_id), actor_user_id=actor_user_id, organization_id=organization_id, request_id=request_id)
        return self.get(organization_id, intervention_id)


class RenewalUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def evaluate(self, *, organization_id: int, notes: str = "", actor_user_id: Optional[int] = None, request_id: Optional[str] = None) -> RenewalReadiness:
        latest = HealthUseCases(self._conn).latest(organization_id)
        if latest is None or latest.score is None:
            state, score = "insufficient_data", None
            notes = (notes + " Health unavailable.").strip()
        elif latest.score >= 0.7:
            state, score = "ready", latest.score
        elif latest.score >= 0.4:
            state, score = "at_risk", latest.score
        else:
            state, score = "unlikely", latest.score
        now = _now()
        rid = _next_id(self._conn, "app_renewal_readiness")
        self._conn.execute(
            """
            INSERT INTO app_renewal_readiness
                (id, organization_id, readiness_state, score, notes, evaluated_at, evaluated_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [rid, organization_id, state, score, notes, now, actor_user_id],
        )
        _audit(self._conn, action="cs.renewal.evaluated", target_type="renewal_readiness",
               target_id=str(rid), actor_user_id=actor_user_id, organization_id=organization_id, request_id=request_id)
        row = self._conn.execute(
            "SELECT id, organization_id, readiness_state, score, notes, evaluated_at, evaluated_by FROM app_renewal_readiness WHERE id = ?",
            [rid],
        ).fetchone()
        return RenewalReadiness(*row)


class ExpansionUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def create(self, *, organization_id: int, title: str, estimated_value: Optional[float] = None, notes: str = "", actor_user_id: Optional[int] = None, request_id: Optional[str] = None) -> ExpansionOpportunity:
        now = _now()
        eid = _next_id(self._conn, "app_expansion_opportunity")
        self._conn.execute(
            """
            INSERT INTO app_expansion_opportunity
                (id, organization_id, title, status, estimated_value, notes, created_by, created_at, updated_at)
            VALUES (?, ?, ?, 'identified', ?, ?, ?, ?, ?)
            """,
            [eid, organization_id, title.strip(), estimated_value, notes, actor_user_id, now, now],
        )
        _audit(self._conn, action="cs.expansion.created", target_type="expansion_opportunity",
               target_id=str(eid), actor_user_id=actor_user_id, organization_id=organization_id, request_id=request_id)
        row = self._conn.execute(
            "SELECT id, organization_id, title, status, estimated_value, notes, created_by, created_at, updated_at FROM app_expansion_opportunity WHERE id = ?",
            [eid],
        ).fetchone()
        return ExpansionOpportunity(*row)

    def list(self, organization_id: int) -> list[ExpansionOpportunity]:
        rows = self._conn.execute(
            "SELECT id, organization_id, title, status, estimated_value, notes, created_by, created_at, updated_at FROM app_expansion_opportunity WHERE organization_id = ? ORDER BY id DESC",
            [organization_id],
        ).fetchall()
        return [ExpansionOpportunity(*r) for r in rows]


class SupportUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def _get_case(self, organization_id: int, case_id: int) -> SupportCase:
        row = self._conn.execute(
            """
            SELECT id, organization_id, subject, category, priority, status, requester_user_id,
                   assignee_user_id, resolved_at, closed_at, created_at, updated_at
            FROM app_support_case WHERE id = ? AND organization_id = ?
            """,
            [case_id, organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError("Support case not found")
        return SupportCase(*row)

    def create(self, *, organization_id: int, subject: str, category: str = "general", priority: str = "normal", actor_user_id: Optional[int] = None, request_id: Optional[str] = None) -> SupportCase:
        if priority not in ("low", "normal", "high", "urgent"):
            raise ValidationError("Invalid priority")
        now = _now()
        cid = _next_id(self._conn, "app_support_case")
        self._conn.execute(
            """
            INSERT INTO app_support_case
                (id, organization_id, subject, category, priority, status, requester_user_id,
                 assignee_user_id, resolved_at, closed_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'open', ?, NULL, NULL, NULL, ?, ?)
            """,
            [cid, organization_id, subject.strip(), category, priority, actor_user_id, now, now],
        )
        # SLA event (academic)
        policy = self._conn.execute(
            "SELECT id, response_minutes FROM app_support_sla_policy WHERE organization_id = ? AND priority = ? AND status = 'active' LIMIT 1",
            [organization_id, priority],
        ).fetchone()
        if not policy:
            pid = _next_id(self._conn, "app_support_sla_policy")
            mins = {"low": 2880, "normal": 1440, "high": 480, "urgent": 120}[priority]
            self._conn.execute(
                """
                INSERT INTO app_support_sla_policy
                    (id, organization_id, name, priority, response_minutes, resolve_minutes, status, academic_label)
                VALUES (?, ?, ?, ?, ?, ?, 'active', 'academic_configuration_not_contractual')
                """,
                [pid, organization_id, f"Default {priority}", priority, mins, mins * 2],
            )
            policy = (pid, mins)
        eid = _next_id(self._conn, "app_support_sla_event")
        due = now + timedelta(minutes=int(policy[1]))
        self._conn.execute(
            """
            INSERT INTO app_support_sla_event (id, case_id, policy_id, event_type, due_at, occurred_at, met)
            VALUES (?, ?, ?, 'response_due', ?, ?, NULL)
            """,
            [eid, cid, int(policy[0]), due, now],
        )
        _audit(self._conn, action="support.case.created", target_type="support_case", target_id=str(cid),
               actor_user_id=actor_user_id, organization_id=organization_id, request_id=request_id)
        case = self._get_case(organization_id, cid)
        try:
            from app.packages.platform_ops.application.notify import notify_support, user_email
            notify_support(
                self._conn,
                to_email=user_email(self._conn, actor_user_id),
                organization_id=organization_id,
                template_code="support.ticket_created",
                subject="Ticket de soporte creado",
                title="Ticket creado",
                paragraphs=[
                    f"Se creo el ticket #{cid}: {subject.strip()}",
                    f"Prioridad: {priority}",
                ],
                related_id=str(cid),
            )
        except Exception:
            pass
        return case

    def triage(self, *, organization_id: int, case_id: int, actor_user_id: Optional[int] = None, request_id: Optional[str] = None) -> SupportCase:
        case = self._get_case(organization_id, case_id)
        if case.status not in ("open", "reopened"):
            raise StateError("Cannot triage from current status")
        now = _now()
        self._conn.execute("UPDATE app_support_case SET status = 'triaged', updated_at = ? WHERE id = ?", [now, case_id])
        _audit(self._conn, action="support.case.triaged", target_type="support_case", target_id=str(case_id),
               actor_user_id=actor_user_id, organization_id=organization_id, request_id=request_id)
        return self._get_case(organization_id, case_id)

    def assign(self, *, organization_id: int, case_id: int, assignee_user_id: int, actor_user_id: Optional[int] = None, request_id: Optional[str] = None) -> SupportCase:
        case = self._get_case(organization_id, case_id)
        if case.status in ("closed", "resolved"):
            raise StateError("Cannot assign closed/resolved case; reopen first")
        if case.status not in (
            "open",
            "triaged",
            "reopened",
            "assigned",
            "escalated",
            "in_progress",
            "waiting_customer",
        ):
            raise StateError("Cannot assign from current status")
        now = _now()
        aid = _next_id(self._conn, "app_support_assignment")
        self._conn.execute(
            "INSERT INTO app_support_assignment (id, case_id, assignee_user_id, assigned_by, assigned_at) VALUES (?, ?, ?, ?, ?)",
            [aid, case_id, assignee_user_id, actor_user_id, now],
        )
        self._conn.execute(
            "UPDATE app_support_case SET status = 'assigned', assignee_user_id = ?, updated_at = ? WHERE id = ?",
            [assignee_user_id, now, case_id],
        )
        _audit(self._conn, action="support.case.assigned", target_type="support_case", target_id=str(case_id),
               actor_user_id=actor_user_id, organization_id=organization_id, request_id=request_id)
        return self._get_case(organization_id, case_id)

    def add_message(self, *, organization_id: int, case_id: int, body: str, is_internal: bool = False, actor_user_id: Optional[int] = None, request_id: Optional[str] = None) -> SupportMessage:
        self._get_case(organization_id, case_id)
        now = _now()
        mid = _next_id(self._conn, "app_support_message")
        self._conn.execute(
            "INSERT INTO app_support_message (id, case_id, author_user_id, body, is_internal, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            [mid, case_id, actor_user_id, body.strip(), is_internal, now],
        )
        if not is_internal:
            self._conn.execute(
                "UPDATE app_support_case SET status = CASE WHEN status IN ('waiting_customer','resolved') THEN status ELSE 'in_progress' END, updated_at = ? WHERE id = ?",
                [now, case_id],
            )
        _audit(self._conn, action="support.message.added", target_type="support_message", target_id=str(mid),
               actor_user_id=actor_user_id, organization_id=organization_id,
               new_values={"is_internal": is_internal}, request_id=request_id)
        row = self._conn.execute(
            "SELECT id, case_id, author_user_id, body, is_internal, created_at FROM app_support_message WHERE id = ?",
            [mid],
        ).fetchone()
        msg = SupportMessage(*row)
        if not is_internal:
            try:
                case = self._get_case(organization_id, case_id)
                from app.packages.platform_ops.application.notify import notify_support, user_email
                # Agent reply → notify requester when author differs
                if case.requester_user_id and case.requester_user_id != actor_user_id:
                    notify_support(
                        self._conn,
                        to_email=user_email(self._conn, case.requester_user_id),
                        organization_id=organization_id,
                        template_code="support.agent_reply",
                        subject="Nueva respuesta de soporte",
                        title="Respuesta del agente",
                        paragraphs=[
                            f"Hay una nueva respuesta en el ticket #{case_id}.",
                            "Ingresa a la plataforma para leerla.",
                        ],
                        related_id=str(case_id),
                    )
            except Exception:
                pass
        return msg

    def list_messages(self, organization_id: int, case_id: int, *, include_internal: bool) -> list[SupportMessage]:
        self._get_case(organization_id, case_id)
        if include_internal:
            rows = self._conn.execute(
                "SELECT id, case_id, author_user_id, body, is_internal, created_at FROM app_support_message WHERE case_id = ? ORDER BY id",
                [case_id],
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT id, case_id, author_user_id, body, is_internal, created_at FROM app_support_message WHERE case_id = ? AND is_internal = FALSE ORDER BY id",
                [case_id],
            ).fetchall()
        return [SupportMessage(*r) for r in rows]

    def escalate(self, *, organization_id: int, case_id: int, actor_user_id: Optional[int] = None, request_id: Optional[str] = None) -> SupportCase:
        case = self._get_case(organization_id, case_id)
        if case.status not in (
            "triaged",
            "assigned",
            "in_progress",
            "waiting_customer",
            "reopened",
        ):
            raise StateError("Cannot escalate from current status")
        now = _now()
        self._conn.execute("UPDATE app_support_case SET status = 'escalated', updated_at = ? WHERE id = ?", [now, case_id])
        _audit(self._conn, action="support.case.escalated", target_type="support_case", target_id=str(case_id),
               actor_user_id=actor_user_id, organization_id=organization_id, request_id=request_id)
        return self._get_case(organization_id, case_id)

    def resolve(self, *, organization_id: int, case_id: int, actor_user_id: Optional[int] = None, request_id: Optional[str] = None) -> SupportCase:
        case = self._get_case(organization_id, case_id)
        if case.status in ("closed",):
            raise StateError("Closed case cannot be resolved")
        now = _now()
        self._conn.execute(
            "UPDATE app_support_case SET status = 'resolved', resolved_at = ?, updated_at = ? WHERE id = ?",
            [now, now, case_id],
        )
        _audit(self._conn, action="support.case.resolved", target_type="support_case", target_id=str(case_id),
               actor_user_id=actor_user_id, organization_id=organization_id, request_id=request_id)
        updated = self._get_case(organization_id, case_id)
        try:
            from app.packages.platform_ops.application.notify import notify_support, user_email
            notify_support(
                self._conn,
                to_email=user_email(self._conn, case.requester_user_id),
                organization_id=organization_id,
                template_code="support.ticket_resolved",
                subject="Ticket resuelto",
                title="Ticket resuelto",
                paragraphs=[f"El ticket #{case_id} fue marcado como resuelto."],
                related_id=str(case_id),
            )
        except Exception:
            pass
        return updated

    def close(self, *, organization_id: int, case_id: int, actor_user_id: Optional[int] = None, request_id: Optional[str] = None) -> SupportCase:
        case = self._get_case(organization_id, case_id)
        if case.status not in ("resolved", "escalated", "in_progress", "assigned", "waiting_customer"):
            if case.status != "resolved":
                # allow close from resolved primarily; also from waiting
                pass
        now = _now()
        self._conn.execute(
            "UPDATE app_support_case SET status = 'closed', closed_at = ?, updated_at = ? WHERE id = ?",
            [now, now, case_id],
        )
        _audit(self._conn, action="support.case.closed", target_type="support_case", target_id=str(case_id),
               actor_user_id=actor_user_id, organization_id=organization_id, request_id=request_id)
        return self._get_case(organization_id, case_id)

    def reopen(self, *, organization_id: int, case_id: int, actor_user_id: Optional[int] = None, request_id: Optional[str] = None) -> SupportCase:
        case = self._get_case(organization_id, case_id)
        if case.status not in ("closed", "resolved"):
            raise StateError("Only closed/resolved can reopen")
        now = _now()
        self._conn.execute(
            "UPDATE app_support_case SET status = 'reopened', closed_at = NULL, resolved_at = NULL, updated_at = ? WHERE id = ?",
            [now, case_id],
        )
        _audit(self._conn, action="support.case.reopened", target_type="support_case", target_id=str(case_id),
               actor_user_id=actor_user_id, organization_id=organization_id, request_id=request_id)
        return self._get_case(organization_id, case_id)

    def record_satisfaction(self, *, organization_id: int, case_id: int, score: int, comment: Optional[str] = None, actor_user_id: Optional[int] = None, request_id: Optional[str] = None) -> SupportSatisfaction:
        self._get_case(organization_id, case_id)
        if score < 1 or score > 5:
            raise ValidationError("score must be 1..5")
        now = _now()
        sid = _next_id(self._conn, "app_support_satisfaction")
        self._conn.execute(
            "INSERT INTO app_support_satisfaction (id, case_id, score, comment, recorded_by, recorded_at) VALUES (?, ?, ?, ?, ?, ?)",
            [sid, case_id, score, comment, actor_user_id, now],
        )
        _audit(self._conn, action="support.satisfaction.recorded", target_type="support_satisfaction",
               target_id=str(sid), actor_user_id=actor_user_id, organization_id=organization_id, request_id=request_id)
        row = self._conn.execute(
            "SELECT id, case_id, score, comment, recorded_by, recorded_at FROM app_support_satisfaction WHERE id = ?",
            [sid],
        ).fetchone()
        return SupportSatisfaction(*row)

    def list_cases(self, organization_id: int) -> list[SupportCase]:
        rows = self._conn.execute(
            """
            SELECT id, organization_id, subject, category, priority, status, requester_user_id,
                   assignee_user_id, resolved_at, closed_at, created_at, updated_at
            FROM app_support_case WHERE organization_id = ? ORDER BY id DESC
            """,
            [organization_id],
        ).fetchall()
        return [SupportCase(*r) for r in rows]

    def list_sla_events(self, organization_id: int, case_id: int) -> list[SupportSlaEvent]:
        self._get_case(organization_id, case_id)
        rows = self._conn.execute(
            "SELECT id, case_id, policy_id, event_type, due_at, occurred_at, met FROM app_support_sla_event WHERE case_id = ? ORDER BY id",
            [case_id],
        ).fetchall()
        return [SupportSlaEvent(*r) for r in rows]
