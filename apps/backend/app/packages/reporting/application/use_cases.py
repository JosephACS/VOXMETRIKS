"""Reporting use cases — Spec 024."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from typing import Any, Optional

import duckdb

from app.core.database import transactional
from app.core.time_util import utc_now
from app.packages.reporting.domain.entities import (
    BusinessDecision,
    DecisionAction,
    DecisionFollowUp,
    ExecutiveReport,
    ReportDefinition,
    ReportGeneration,
    ReportSnapshot,
)
from app.packages.reporting.domain.errors import NotFoundError, StateError, ValidationError


def _next_id(conn: duckdb.DuckDBPyConnection, table: str) -> int:
    return int(conn.execute(f"SELECT COALESCE(MAX(id), 0) + 1 FROM {table}").fetchone()[0])


def _now() -> datetime:
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
            source="reporting.use_case",
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


def _row_def(r) -> ReportDefinition:
    return ReportDefinition(
        id=int(r[0]), organization_id=int(r[1]), code=r[2], title=r[3], description=r[4] or "",
        status=r[5], default_period=r[6], created_by=r[7], created_at=r[8], updated_at=r[9],
    )


def _row_gen(r) -> ReportGeneration:
    return ReportGeneration(
        id=int(r[0]), organization_id=int(r[1]), definition_id=int(r[2]), status=r[3],
        period_start=r[4], period_end=r[5], filters_json=r[6] or "{}",
        requested_by=r[7], requested_at=r[8], completed_at=r[9],
        error_message=r[10], snapshot_id=r[11],
    )


def _row_snap(r) -> ReportSnapshot:
    return ReportSnapshot(
        id=int(r[0]), organization_id=int(r[1]), generation_id=int(r[2]), definition_id=int(r[3]),
        payload_json=r[4], kpi_versions_json=r[5] or "[]", unavailable_sources_json=r[6] or "[]",
        limitations=r[7] or "", generated_at=r[8], generated_by=r[9],
    )


def _row_exec(r) -> ExecutiveReport:
    return ExecutiveReport(
        id=int(r[0]), organization_id=int(r[1]), definition_id=int(r[2]), generation_id=int(r[3]),
        snapshot_id=int(r[4]), title=r[5], status=r[6], period_start=r[7], period_end=r[8],
        published_at=r[9], archived_at=r[10], created_by=r[11], created_at=r[12], updated_at=r[13],
    )


def _row_dec(r) -> BusinessDecision:
    return BusinessDecision(
        id=int(r[0]), organization_id=int(r[1]), executive_report_id=r[2], title=r[3],
        proposal=r[4], status=r[5], evidence_refs_json=r[6] or "[]",
        created_by=r[7], created_at=r[8], updated_at=r[9], completed_at=r[10],
    )


def _row_action(r) -> DecisionAction:
    return DecisionAction(
        id=int(r[0]), decision_id=int(r[1]), title=r[2], status=r[3],
        assignee_user_id=r[4], due_at=r[5], completed_at=r[6], created_at=r[7], updated_at=r[8],
    )


def _row_fu(r) -> DecisionFollowUp:
    return DecisionFollowUp(
        id=int(r[0]), decision_id=int(r[1]), note=r[2], created_by=r[3], created_at=r[4],
    )


class ReportDefinitionUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def create(
        self,
        *,
        organization_id: int,
        code: str,
        title: str,
        description: str = "",
        default_period: str = "last_30d",
        actor_user_id: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> ReportDefinition:
        code = (code or "").strip()
        title = (title or "").strip()
        if not code or not title:
            raise ValidationError("code and title are required")
        now = _now()
        rid = _next_id(self._conn, "app_report_definition")
        self._conn.execute(
            """
            INSERT INTO app_report_definition
                (id, organization_id, code, title, description, status, default_period,
                 created_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 'active', ?, ?, ?, ?)
            """,
            [rid, organization_id, code, title, description or "", default_period, actor_user_id, now, now],
        )
        _audit(
            self._conn, action="report.definition.created", target_type="report_definition",
            target_id=str(rid), actor_user_id=actor_user_id, organization_id=organization_id,
            new_values={"code": code, "title": title}, request_id=request_id,
        )
        return self.get(organization_id, rid)

    def get(self, organization_id: int, definition_id: int) -> ReportDefinition:
        row = self._conn.execute(
            """
            SELECT id, organization_id, code, title, description, status, default_period,
                   created_by, created_at, updated_at
            FROM app_report_definition WHERE id = ? AND organization_id = ?
            """,
            [definition_id, organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError("Report definition not found")
        return _row_def(row)

    def list(self, organization_id: int, *, limit: int = 50, offset: int = 0) -> tuple[list[ReportDefinition], int]:
        total = int(
            self._conn.execute(
                "SELECT COUNT(*) FROM app_report_definition WHERE organization_id = ?",
                [organization_id],
            ).fetchone()[0]
        )
        rows = self._conn.execute(
            """
            SELECT id, organization_id, code, title, description, status, default_period,
                   created_by, created_at, updated_at
            FROM app_report_definition WHERE organization_id = ?
            ORDER BY id DESC LIMIT ? OFFSET ?
            """,
            [organization_id, limit, offset],
        ).fetchall()
        return [_row_def(r) for r in rows], total


class ReportGenerationUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def request(
        self,
        *,
        organization_id: int,
        definition_id: int,
        period_start: Optional[str] = None,
        period_end: Optional[str] = None,
        filters: Optional[dict[str, Any]] = None,
        actor_user_id: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> ReportGeneration:
        ReportDefinitionUseCases(self._conn).get(organization_id, definition_id)
        now = _now()
        gid = _next_id(self._conn, "app_report_generation")
        self._conn.execute(
            """
            INSERT INTO app_report_generation
                (id, organization_id, definition_id, status, period_start, period_end,
                 filters_json, requested_by, requested_at, completed_at, error_message, snapshot_id)
            VALUES (?, ?, ?, 'requested', ?, ?, ?, ?, ?, NULL, NULL, NULL)
            """,
            [
                gid, organization_id, definition_id, period_start, period_end,
                json.dumps(filters or {}), actor_user_id, now,
            ],
        )
        _audit(
            self._conn, action="report.generation.requested", target_type="report_generation",
            target_id=str(gid), actor_user_id=actor_user_id, organization_id=organization_id,
            request_id=request_id,
        )
        return self.get(organization_id, gid)

    def get(self, organization_id: int, generation_id: int) -> ReportGeneration:
        row = self._conn.execute(
            """
            SELECT id, organization_id, definition_id, status, period_start, period_end,
                   filters_json, requested_by, requested_at, completed_at, error_message, snapshot_id
            FROM app_report_generation WHERE id = ? AND organization_id = ?
            """,
            [generation_id, organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError("Report generation not found")
        return _row_gen(row)

    def generate_snapshot(
        self,
        *,
        organization_id: int,
        generation_id: int,
        actor_user_id: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> tuple[ReportGeneration, ReportSnapshot, ExecutiveReport]:
        gen = self.get(organization_id, generation_id)
        if gen.status not in ("requested", "failed"):
            raise StateError(f"Cannot generate from status={gen.status}")

        now = _now()
        self._conn.execute(
            "UPDATE app_report_generation SET status = 'generating' WHERE id = ? AND organization_id = ?",
            [generation_id, organization_id],
        )

        definition = ReportDefinitionUseCases(self._conn).get(organization_id, gen.definition_id)

        kpi_rows = []
        try:
            kpi_rows = self._conn.execute(
                """
                SELECT d.id, d.code, d.version, d.name, s.id, s.value, s.quality_status, s.is_synthetic
                FROM app_kpi_definition d
                LEFT JOIN app_kpi_snapshot s
                  ON s.kpi_definition_id = d.id
                 AND s.organization_id = ?
                 AND (? IS NULL OR s.period >= ?)
                 AND (? IS NULL OR s.period <= ?)
                WHERE d.status = 'active'
                ORDER BY d.code, d.version DESC, s.id DESC
                """,
                [
                    organization_id,
                    gen.period_start,
                    gen.period_start,
                    gen.period_end,
                    gen.period_end,
                ],
            ).fetchall()
        except Exception:
            kpi_rows = []

        seen_codes: set[str] = set()
        kpi_versions: list[dict[str, Any]] = []
        kpi_payload: list[dict[str, Any]] = []
        unavailable: list[str] = []

        for row in kpi_rows:
            code = row[1]
            if code in seen_codes:
                continue
            seen_codes.add(code)
            kpi_versions.append({"kpi_definition_id": int(row[0]), "code": code, "version": int(row[2])})
            if row[4] is None or row[5] is None:
                unavailable.append(code)
                kpi_payload.append({
                    "code": code, "version": int(row[2]), "value": None,
                    "status": "No disponible", "quality_status": row[6],
                })
            else:
                kpi_payload.append({
                    "code": code, "version": int(row[2]), "value": float(row[5]) if row[5] is not None else None,
                    "quality_status": row[6], "is_synthetic": bool(row[7]) if row[7] is not None else False,
                    "kpi_snapshot_id": int(row[4]),
                })

        # Campaign / ROI availability (honest)
        campaign_summary: dict[str, Any] = {"count": 0, "roi_status": "No disponible"}
        try:
            camp = self._conn.execute(
                "SELECT COUNT(*) FROM app_campaign WHERE organization_id = ?",
                [organization_id],
            ).fetchone()
            campaign_summary["count"] = int(camp[0]) if camp else 0
            # ROI often unavailable by design (Spec 022)
            campaign_summary["roi_status"] = "No disponible"
            if campaign_summary["count"] == 0:
                unavailable.append("campaigns")
        except Exception:
            unavailable.append("campaigns")

        if not kpi_payload:
            unavailable.append("kpi_catalog")

        limitations = (
            "Academic executive report snapshot. Not a certified financial statement. "
            "Historical snapshots are immutable and are not recalculated when KPIs change. "
            "ROI and customer-health sources may be unavailable."
        )
        payload = {
            "organization_id": organization_id,
            "definition_code": definition.code,
            "period_start": gen.period_start,
            "period_end": gen.period_end,
            "kpis": kpi_payload,
            "campaigns": campaign_summary,
            "billing": {"status": "referenced_when_available"},
            "generated_label": "synthetic_or_warehouse_backed",
        }

        sid = _next_id(self._conn, "app_report_snapshot")
        self._conn.execute(
            """
            INSERT INTO app_report_snapshot
                (id, organization_id, generation_id, definition_id, payload_json,
                 kpi_versions_json, unavailable_sources_json, limitations, generated_at, generated_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                sid, organization_id, generation_id, gen.definition_id,
                json.dumps(payload, default=str), json.dumps(kpi_versions),
                json.dumps(unavailable), limitations, now, actor_user_id,
            ],
        )

        # Sections
        for i, (code, title, content) in enumerate([
            ("summary", "Executive Summary", {"kpis": kpi_payload[:5]}),
            ("campaigns", "Campaigns & ROI", campaign_summary),
            ("limitations", "Limitations", {"text": limitations, "unavailable": unavailable}),
        ]):
            sec_id = _next_id(self._conn, "app_report_section")
            self._conn.execute(
                """
                INSERT INTO app_report_section
                    (id, snapshot_id, section_code, title, content_json, sort_order)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [sec_id, sid, code, title, json.dumps(content, default=str), i],
            )

        self._conn.execute(
            """
            UPDATE app_report_generation
            SET status = 'ready', completed_at = ?, snapshot_id = ?, error_message = NULL
            WHERE id = ? AND organization_id = ?
            """,
            [now, sid, generation_id, organization_id],
        )

        eid = _next_id(self._conn, "app_executive_report")
        self._conn.execute(
            """
            INSERT INTO app_executive_report
                (id, organization_id, definition_id, generation_id, snapshot_id, title, status,
                 period_start, period_end, published_at, archived_at, created_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 'draft', ?, ?, NULL, NULL, ?, ?, ?)
            """,
            [
                eid, organization_id, gen.definition_id, generation_id, sid,
                definition.title, gen.period_start, gen.period_end, actor_user_id, now, now,
            ],
        )

        _audit(
            self._conn, action="report.snapshot.generated", target_type="report_snapshot",
            target_id=str(sid), actor_user_id=actor_user_id, organization_id=organization_id,
            new_values={"executive_report_id": eid, "unavailable": unavailable},
            request_id=request_id,
        )

        snap = ReportSnapshotUseCases(self._conn).get(organization_id, sid)
        exec_r = ExecutiveReportUseCases(self._conn).get(organization_id, eid)
        return self.get(organization_id, generation_id), snap, exec_r


class ReportSnapshotUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def get(self, organization_id: int, snapshot_id: int) -> ReportSnapshot:
        row = self._conn.execute(
            """
            SELECT id, organization_id, generation_id, definition_id, payload_json,
                   kpi_versions_json, unavailable_sources_json, limitations, generated_at, generated_by
            FROM app_report_snapshot WHERE id = ? AND organization_id = ?
            """,
            [snapshot_id, organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError("Report snapshot not found")
        return _row_snap(row)


class ExecutiveReportUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def get(self, organization_id: int, report_id: int) -> ExecutiveReport:
        row = self._conn.execute(
            """
            SELECT id, organization_id, definition_id, generation_id, snapshot_id, title, status,
                   period_start, period_end, published_at, archived_at, created_by, created_at, updated_at
            FROM app_executive_report WHERE id = ? AND organization_id = ?
            """,
            [report_id, organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError("Executive report not found")
        return _row_exec(row)

    def list(self, organization_id: int, *, status: Optional[str] = None, limit: int = 50, offset: int = 0):
        where = "organization_id = ?"
        params: list[Any] = [organization_id]
        if status:
            where += " AND status = ?"
            params.append(status)
        total = int(self._conn.execute(f"SELECT COUNT(*) FROM app_executive_report WHERE {where}", params).fetchone()[0])
        rows = self._conn.execute(
            f"""
            SELECT id, organization_id, definition_id, generation_id, snapshot_id, title, status,
                   period_start, period_end, published_at, archived_at, created_by, created_at, updated_at
            FROM app_executive_report WHERE {where}
            ORDER BY id DESC LIMIT ? OFFSET ?
            """,
            [*params, limit, offset],
        ).fetchall()
        return [_row_exec(r) for r in rows], total

    def submit_for_approval(self, *, organization_id: int, report_id: int, actor_user_id: Optional[int] = None, request_id: Optional[str] = None) -> ExecutiveReport:
        report = self.get(organization_id, report_id)
        if report.status != "draft":
            raise StateError("Only draft reports can be submitted")
        now = _now()
        self._conn.execute(
            "UPDATE app_executive_report SET status = 'pending_approval', updated_at = ? WHERE id = ?",
            [now, report_id],
        )
        _audit(self._conn, action="report.submitted", target_type="executive_report", target_id=str(report_id),
               actor_user_id=actor_user_id, organization_id=organization_id, request_id=request_id)
        return self.get(organization_id, report_id)

    def approve(self, *, organization_id: int, report_id: int, comment: Optional[str] = None, actor_user_id: Optional[int] = None, request_id: Optional[str] = None) -> ExecutiveReport:
        report = self.get(organization_id, report_id)
        if report.status not in ("draft", "pending_approval"):
            raise StateError(f"Cannot approve from status={report.status}")
        now = _now()
        aid = _next_id(self._conn, "app_report_approval")
        self._conn.execute(
            """
            INSERT INTO app_report_approval (id, executive_report_id, decision, approved_by, approved_at, comment)
            VALUES (?, ?, 'approved', ?, ?, ?)
            """,
            [aid, report_id, actor_user_id, now, comment],
        )
        self._conn.execute(
            "UPDATE app_executive_report SET status = 'approved', updated_at = ? WHERE id = ?",
            [now, report_id],
        )
        _audit(self._conn, action="report.approved", target_type="executive_report", target_id=str(report_id),
               actor_user_id=actor_user_id, organization_id=organization_id, request_id=request_id)
        return self.get(organization_id, report_id)

    def publish(self, *, organization_id: int, report_id: int, actor_user_id: Optional[int] = None, request_id: Optional[str] = None) -> ExecutiveReport:
        report = self.get(organization_id, report_id)
        if report.status != "approved":
            raise StateError("Only approved reports can be published")
        now = _now()
        self._conn.execute(
            "UPDATE app_executive_report SET status = 'published', published_at = ?, updated_at = ? WHERE id = ?",
            [now, now, report_id],
        )
        _audit(self._conn, action="report.published", target_type="executive_report", target_id=str(report_id),
               actor_user_id=actor_user_id, organization_id=organization_id, request_id=request_id)
        published = self.get(organization_id, report_id)
        try:
            from app.packages.platform_ops.application.notify import notify_report_ready, user_email
            notify_report_ready(
                self._conn,
                to_email=user_email(self._conn, actor_user_id),
                organization_id=organization_id,
                report_title=published.title,
                report_id=report_id,
            )
        except Exception:
            pass
        return published

    def archive(self, *, organization_id: int, report_id: int, actor_user_id: Optional[int] = None, request_id: Optional[str] = None) -> ExecutiveReport:
        report = self.get(organization_id, report_id)
        if report.status == "archived":
            raise StateError("Already archived")
        now = _now()
        self._conn.execute(
            "UPDATE app_executive_report SET status = 'archived', archived_at = ?, updated_at = ? WHERE id = ?",
            [now, now, report_id],
        )
        _audit(self._conn, action="report.archived", target_type="executive_report", target_id=str(report_id),
               actor_user_id=actor_user_id, organization_id=organization_id, request_id=request_id)
        return self.get(organization_id, report_id)

    def export_csv(self, *, organization_id: int, report_id: int) -> str:
        report = self.get(organization_id, report_id)
        snap = ReportSnapshotUseCases(self._conn).get(organization_id, report.snapshot_id)
        payload = json.loads(snap.payload_json)
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["field", "value"])
        writer.writerow(["report_id", report.id])
        writer.writerow(["title", report.title])
        writer.writerow(["status", report.status])
        writer.writerow(["limitations", snap.limitations])
        writer.writerow(["disclaimer", "Not a certified export; academic/demo only"])
        for kpi in payload.get("kpis", []):
            writer.writerow([f"kpi.{kpi.get('code')}", kpi.get("value")])
            writer.writerow([f"kpi.{kpi.get('code')}.status", kpi.get("status") or kpi.get("quality_status")])
        writer.writerow(["unavailable_sources", snap.unavailable_sources_json])
        return buf.getvalue()


class BusinessDecisionUseCases:
    def __init__(self, conn: duckdb.DuckDBPyConnection) -> None:
        self._conn = conn

    def create(
        self,
        *,
        organization_id: int,
        title: str,
        proposal: str,
        executive_report_id: Optional[int] = None,
        evidence_refs: Optional[list[Any]] = None,
        actor_user_id: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> BusinessDecision:
        title = (title or "").strip()
        proposal = (proposal or "").strip()
        if not title or not proposal:
            raise ValidationError("title and proposal are required")
        if executive_report_id is not None:
            ExecutiveReportUseCases(self._conn).get(organization_id, executive_report_id)
        now = _now()
        did = _next_id(self._conn, "app_business_decision")
        self._conn.execute(
            """
            INSERT INTO app_business_decision
                (id, organization_id, executive_report_id, title, proposal, status,
                 evidence_refs_json, created_by, created_at, updated_at, completed_at)
            VALUES (?, ?, ?, ?, ?, 'proposed', ?, ?, ?, ?, NULL)
            """,
            [
                did, organization_id, executive_report_id, title, proposal,
                json.dumps(evidence_refs or []), actor_user_id, now, now,
            ],
        )
        _audit(self._conn, action="decision.recorded", target_type="business_decision", target_id=str(did),
               actor_user_id=actor_user_id, organization_id=organization_id, request_id=request_id)
        return self.get(organization_id, did)

    def get(self, organization_id: int, decision_id: int) -> BusinessDecision:
        row = self._conn.execute(
            """
            SELECT id, organization_id, executive_report_id, title, proposal, status,
                   evidence_refs_json, created_by, created_at, updated_at, completed_at
            FROM app_business_decision WHERE id = ? AND organization_id = ?
            """,
            [decision_id, organization_id],
        ).fetchone()
        if not row:
            raise NotFoundError("Business decision not found")
        return _row_dec(row)

    def list(self, organization_id: int, *, limit: int = 50, offset: int = 0):
        total = int(self._conn.execute(
            "SELECT COUNT(*) FROM app_business_decision WHERE organization_id = ?", [organization_id]
        ).fetchone()[0])
        rows = self._conn.execute(
            """
            SELECT id, organization_id, executive_report_id, title, proposal, status,
                   evidence_refs_json, created_by, created_at, updated_at, completed_at
            FROM app_business_decision WHERE organization_id = ?
            ORDER BY id DESC LIMIT ? OFFSET ?
            """,
            [organization_id, limit, offset],
        ).fetchall()
        return [_row_dec(r) for r in rows], total

    def approve(self, *, organization_id: int, decision_id: int, actor_user_id: Optional[int] = None, request_id: Optional[str] = None) -> BusinessDecision:
        d = self.get(organization_id, decision_id)
        if d.status != "proposed":
            raise StateError("Only proposed decisions can be approved")
        now = _now()
        self._conn.execute(
            "UPDATE app_business_decision SET status = 'approved', updated_at = ? WHERE id = ?",
            [now, decision_id],
        )
        _audit(self._conn, action="decision.approved", target_type="business_decision", target_id=str(decision_id),
               actor_user_id=actor_user_id, organization_id=organization_id, request_id=request_id)
        return self.get(organization_id, decision_id)

    def add_action(
        self,
        *,
        organization_id: int,
        decision_id: int,
        title: str,
        assignee_user_id: Optional[int] = None,
        actor_user_id: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> DecisionAction:
        d = self.get(organization_id, decision_id)
        if d.status in ("completed", "canceled"):
            raise StateError("Cannot add actions to closed decision")
        now = _now()
        if d.status == "approved":
            self._conn.execute(
                "UPDATE app_business_decision SET status = 'in_progress', updated_at = ? WHERE id = ?",
                [now, decision_id],
            )
        aid = _next_id(self._conn, "app_decision_action")
        self._conn.execute(
            """
            INSERT INTO app_decision_action
                (id, decision_id, title, status, assignee_user_id, due_at, completed_at, created_at, updated_at)
            VALUES (?, ?, ?, 'planned', ?, NULL, NULL, ?, ?)
            """,
            [aid, decision_id, title.strip(), assignee_user_id, now, now],
        )
        _audit(self._conn, action="decision.action.added", target_type="decision_action", target_id=str(aid),
               actor_user_id=actor_user_id, organization_id=organization_id, request_id=request_id)
        row = self._conn.execute(
            """
            SELECT id, decision_id, title, status, assignee_user_id, due_at, completed_at, created_at, updated_at
            FROM app_decision_action WHERE id = ?
            """,
            [aid],
        ).fetchone()
        return _row_action(row)

    def update_action(
        self,
        *,
        organization_id: int,
        decision_id: int,
        action_id: int,
        status: Optional[str] = None,
        title: Optional[str] = None,
        actor_user_id: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> DecisionAction:
        self.get(organization_id, decision_id)
        row = self._conn.execute(
            """
            SELECT id, decision_id, title, status, assignee_user_id, due_at, completed_at, created_at, updated_at
            FROM app_decision_action WHERE id = ? AND decision_id = ?
            """,
            [action_id, decision_id],
        ).fetchone()
        if not row:
            raise NotFoundError("Decision action not found")
        new_status = status or row[3]
        if new_status not in ("planned", "in_progress", "completed", "canceled"):
            raise ValidationError("Invalid action status")
        now = _now()
        completed_at = now if new_status == "completed" else row[6]
        new_title = title.strip() if title else row[2]
        self._conn.execute(
            """
            UPDATE app_decision_action SET title = ?, status = ?, completed_at = ?, updated_at = ?
            WHERE id = ?
            """,
            [new_title, new_status, completed_at, now, action_id],
        )
        _audit(self._conn, action="decision.action.updated", target_type="decision_action", target_id=str(action_id),
               actor_user_id=actor_user_id, organization_id=organization_id, request_id=request_id)
        row2 = self._conn.execute(
            """
            SELECT id, decision_id, title, status, assignee_user_id, due_at, completed_at, created_at, updated_at
            FROM app_decision_action WHERE id = ?
            """,
            [action_id],
        ).fetchone()
        return _row_action(row2)

    def complete(self, *, organization_id: int, decision_id: int, actor_user_id: Optional[int] = None, request_id: Optional[str] = None) -> BusinessDecision:
        d = self.get(organization_id, decision_id)
        if d.status not in ("approved", "in_progress"):
            raise StateError("Decision must be approved or in_progress to complete")
        now = _now()
        self._conn.execute(
            "UPDATE app_business_decision SET status = 'completed', completed_at = ?, updated_at = ? WHERE id = ?",
            [now, now, decision_id],
        )
        _audit(self._conn, action="decision.completed", target_type="business_decision", target_id=str(decision_id),
               actor_user_id=actor_user_id, organization_id=organization_id, request_id=request_id)
        return self.get(organization_id, decision_id)

    def cancel(
        self,
        *,
        organization_id: int,
        decision_id: int,
        reason: Optional[str] = None,
        actor_user_id: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> BusinessDecision:
        reason = (reason or "").strip() or None
        with transactional(self._conn):
            decision = self.get(organization_id, decision_id)
            if decision.status in ("completed", "canceled"):
                raise StateError("Completed or canceled decisions cannot be canceled")

            now = _now()
            self._conn.execute(
                "UPDATE app_business_decision SET status = 'canceled', completed_at = ?, "
                "updated_at = ? WHERE id = ? AND organization_id = ?",
                [now, now, decision_id, organization_id],
            )
            self._conn.execute(
                "UPDATE app_decision_action SET status = 'canceled', updated_at = ? "
                "WHERE decision_id = ? AND status IN ('planned', 'in_progress')",
                [now, decision_id],
            )
            _audit(
                self._conn,
                action="decision.canceled",
                target_type="business_decision",
                target_id=str(decision_id),
                actor_user_id=actor_user_id,
                organization_id=organization_id,
                previous_values={"status": decision.status},
                new_values={"status": "canceled"},
                reason=reason,
                request_id=request_id,
            )

        return self.get(organization_id, decision_id)

    def add_follow_up(
        self,
        *,
        organization_id: int,
        decision_id: int,
        note: str,
        actor_user_id: Optional[int] = None,
        request_id: Optional[str] = None,
    ) -> DecisionFollowUp:
        self.get(organization_id, decision_id)
        note = (note or "").strip()
        if not note:
            raise ValidationError("note is required")
        now = _now()
        fid = _next_id(self._conn, "app_decision_follow_up")
        self._conn.execute(
            "INSERT INTO app_decision_follow_up (id, decision_id, note, created_by, created_at) VALUES (?, ?, ?, ?, ?)",
            [fid, decision_id, note, actor_user_id, now],
        )
        _audit(self._conn, action="decision.follow_up.added", target_type="decision_follow_up", target_id=str(fid),
               actor_user_id=actor_user_id, organization_id=organization_id, request_id=request_id)
        row = self._conn.execute(
            "SELECT id, decision_id, note, created_by, created_at FROM app_decision_follow_up WHERE id = ?",
            [fid],
        ).fetchone()
        return _row_fu(row)

    def list_follow_ups(self, organization_id: int, decision_id: int) -> list[DecisionFollowUp]:
        self.get(organization_id, decision_id)
        rows = self._conn.execute(
            """
            SELECT id, decision_id, note, created_by, created_at
            FROM app_decision_follow_up WHERE decision_id = ? ORDER BY id ASC
            """,
            [decision_id],
        ).fetchall()
        return [_row_fu(r) for r in rows]

    def list_actions(self, organization_id: int, decision_id: int) -> list[DecisionAction]:
        self.get(organization_id, decision_id)
        rows = self._conn.execute(
            """
            SELECT id, decision_id, title, status, assignee_user_id, due_at, completed_at, created_at, updated_at
            FROM app_decision_action WHERE decision_id = ? ORDER BY id ASC
            """,
            [decision_id],
        ).fetchall()
        return [_row_action(r) for r in rows]
