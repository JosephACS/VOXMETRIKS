"""Test R2: Reporting use cases — Spec 024."""

from __future__ import annotations

import json

from app.core.database import using_write_conn
from app.core.time_util import utc_now
from app.packages.reporting.application.use_cases import (
    BusinessDecisionUseCases,
    ExecutiveReportUseCases,
    ReportDefinitionUseCases,
    ReportGenerationUseCases,
    ReportSnapshotUseCases,
)


ORG_ID = 9240


def _ensure_org(conn, org_id: int = ORG_ID) -> None:
    now = utc_now()
    if not conn.execute("SELECT id FROM app_organization WHERE id = ?", [org_id]).fetchone():
        conn.execute(
            """
            INSERT INTO app_organization
                (id, display_name, slug, organization_type, country_code, timezone,
                 default_currency, status, created_by, created_at, updated_at)
            VALUES (?, 'Reporting R2 Org', 'reporting-r2-org', 'label', 'US', 'UTC',
                    'USD', 'active', 1, ?, ?)
            """,
            [org_id, now, now],
        )


def test_immutable_snapshot_and_decision_lifecycle():
    with using_write_conn() as conn:
        _ensure_org(conn)
        defs = ReportDefinitionUseCases(conn)
        gens = ReportGenerationUseCases(conn)
        snaps = ReportSnapshotUseCases(conn)
        execs = ExecutiveReportUseCases(conn)
        decisions = BusinessDecisionUseCases(conn)

        d = defs.create(
            organization_id=ORG_ID, code="exec-monthly", title="Monthly Executive",
            actor_user_id=1,
        )
        g = gens.request(organization_id=ORG_ID, definition_id=d.id, actor_user_id=1)
        gen2, snap, exe = gens.generate_snapshot(
            organization_id=ORG_ID, generation_id=g.id, actor_user_id=1,
        )
        assert gen2.status == "ready"
        assert snap.id == gen2.snapshot_id
        frozen = snap.payload_json

        # Mutate KPI catalog if present — snapshot must stay frozen
        try:
            conn.execute(
                "UPDATE app_kpi_definition SET name = name || ' CHANGED' WHERE id = ("
                "SELECT id FROM app_kpi_definition LIMIT 1)"
            )
        except Exception:
            pass

        again = snaps.get(ORG_ID, snap.id)
        assert again.payload_json == frozen

        exe = execs.approve(organization_id=ORG_ID, report_id=exe.id, actor_user_id=1)
        assert exe.status == "approved"
        exe = execs.publish(organization_id=ORG_ID, report_id=exe.id, actor_user_id=1)
        assert exe.status == "published"
        csv_text = execs.export_csv(organization_id=ORG_ID, report_id=exe.id)
        assert "Not a certified export" in csv_text

        unavailable = json.loads(snap.unavailable_sources_json)
        assert isinstance(unavailable, list)

        dec = decisions.create(
            organization_id=ORG_ID,
            title="Increase campaign budget",
            proposal="Raise Q budget 10%",
            executive_report_id=exe.id,
            actor_user_id=1,
        )
        assert dec.status == "proposed"
        dec = decisions.approve(organization_id=ORG_ID, decision_id=dec.id, actor_user_id=1)
        action = decisions.add_action(
            organization_id=ORG_ID, decision_id=dec.id, title="Notify marketing", actor_user_id=1,
        )
        decisions.update_action(
            organization_id=ORG_ID, decision_id=dec.id, action_id=action.id,
            status="completed", actor_user_id=1,
        )
        decisions.add_follow_up(
            organization_id=ORG_ID, decision_id=dec.id, note="Reviewed in weekly", actor_user_id=1,
        )
        dec = decisions.complete(organization_id=ORG_ID, decision_id=dec.id, actor_user_id=1)
        assert dec.status == "completed"
        fus = decisions.list_follow_ups(ORG_ID, dec.id)
        assert len(fus) >= 1
