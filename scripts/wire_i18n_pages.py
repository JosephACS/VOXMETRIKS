#!/usr/bin/env python3
"""Wire known UI strings inside Angular @Component template literals to | t:lang()."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "apps" / "frontend" / "src" / "app" / "packages"

REPLACEMENTS: list[tuple[str, str]] = [
    ("Past due — settle outstanding balance to restore full subscription access.",
     "{{ 'billing.invoiceDetail.pastDueAlert' | t:lang() }}"),
    ("← Invoices", "{{ 'billing.invoiceDetail.back' | t:lang() }}"),
    ("Invoice not found.", "{{ 'billing.invoiceDetail.notFound' | t:lang() }}"),
    ("No invoices found.", "{{ 'billing.invoices.empty' | t:lang() }}"),
    ("No payment attempts found.", "{{ 'billing.paymentAttempts.empty' | t:lang() }}"),
    ("No payments to reconcile.", "{{ 'billing.reconciliation.empty' | t:lang() }}"),
    ("No refunds issued.", "{{ 'billing.refunds.empty' | t:lang() }}"),
    ("Record Manual Transfer", "{{ 'billing.manualTransfer.title' | t:lang() }}"),
    ("Create Credit Note", "{{ 'billing.creditNotes.create' | t:lang() }}"),
    ("Billing Profile", "{{ 'billing.profile.title' | t:lang() }}"),
    ("Billing Ledger", "{{ 'billing.ledger.title' | t:lang() }}"),
    ("Payment Attempts", "{{ 'billing.paymentAttempts.title' | t:lang() }}"),
    ("All statuses", "{{ 'billing.invoices.allStatuses' | t:lang() }}"),
    ("Issue Refund", "{{ 'billing.refunds.issue' | t:lang() }}"),
    ("Credit Notes", "{{ 'billing.creditNotes.title' | t:lang() }}"),
    ("Legal Name", "{{ 'billing.profile.legalName' | t:lang() }}"),
    ("Reconciliation", "{{ 'billing.reconciliation.title' | t:lang() }}"),
    ("Invoices", "{{ 'billing.invoices.title' | t:lang() }}"),
    ("Refunds", "{{ 'billing.refunds.title' | t:lang() }}"),
    ("Sin organización empresarial", "{{ 'organizations.none.title' | t:lang() }}"),
    ("Seguir en modo personal", "{{ 'organizations.none.personal' | t:lang() }}"),
    ("No hay organizaciones", "{{ 'organizations.selector.empty' | t:lang() }}"),
    ("Selector de organización", "{{ 'organizations.selector.title' | t:lang() }}"),
    ("Crear organización", "{{ 'organizations.create.title' | t:lang() }}"),
    ("Onboarding inicial", "{{ 'organizations.onboarding.title' | t:lang() }}"),
    ("Perfil de organización", "{{ 'organizations.settings.title' | t:lang() }}"),
    ("Cerrar organización", "{{ 'organizations.settings.closeOrg' | t:lang() }}"),
    ("Roles y permisos", "{{ 'organizations.roles.title' | t:lang() }}"),
    ("Aceptar invitación", "{{ 'organizations.acceptInvite.title' | t:lang() }}"),
    ("Organización suspendida", "{{ 'organizations.suspended.title' | t:lang() }}"),
    ("Organización cerrada", "{{ 'organizations.closed.title' | t:lang() }}"),
    ("Sin eventos de auditoría", "{{ 'organizations.audit.empty' | t:lang() }}"),
    ("Pipeline de oportunidades", "{{ 'crm.opportunities.board' | t:lang() }}"),
    ("Aprobaciones pendientes", "{{ 'crm.approvals.title' | t:lang() }}"),
    ("Acceso CRM no autorizado", "{{ 'crm.accessDenied.title' | t:lang() }}"),
    ("Auditoría CRM", "{{ 'crm.audit.title' | t:lang() }}"),
    ("Sin prospectos", "{{ 'crm.prospects.empty' | t:lang() }}"),
    ("Sin contactos", "{{ 'crm.contacts.empty' | t:lang() }}"),
    ("Sin oportunidades", "{{ 'crm.opportunities.empty' | t:lang() }}"),
    ("Panel CRM", "{{ 'crm.dashboard.title' | t:lang() }}"),
    ("Catálogo de Planes", "{{ 'subscriptions.plans.title' | t:lang() }}"),
    ("Catálogo de planes", "{{ 'subscriptions.plans.title' | t:lang() }}"),
    ("Mi Suscripción", "{{ 'subscriptions.overview.title' | t:lang() }}"),
    ("Mi suscripción", "{{ 'subscriptions.overview.title' | t:lang() }}"),
    ("Cancelar Suscripción", "{{ 'subscriptions.cancel.title' | t:lang() }}"),
    ("Addons de Suscripción", "{{ 'subscriptions.addons.title' | t:lang() }}"),
    ("Uso de Suscripción", "{{ 'subscriptions.usage.title' | t:lang() }}"),
    ("Sin precios configurados", "{{ 'subscriptions.planDetail.noPrices' | t:lang() }}"),
    ("Iniciar Trial", "{{ 'subscriptions.trial.title' | t:lang() }}"),
    ("Iniciar trial", "{{ 'subscriptions.selectPlan.startTrial' | t:lang() }}"),
    ("No artist profiles yet.", "{{ 'artists.list.empty' | t:lang() }}"),
    ("Artist Profiles", "{{ 'artists.list.title' | t:lang() }}"),
    ("Not linked to catalog", "{{ 'artists.detail.notLinked' | t:lang() }}"),
    ("Back to list", "{{ 'artists.detail.back' | t:lang() }}"),
    ("Manage Team", "{{ 'artists.detail.team' | t:lang() }}"),
    ("Team & Assignments", "{{ 'artists.team.title' | t:lang() }}"),
    ("No status changes recorded yet.", "{{ 'artists.history.empty' | t:lang() }}"),
    ("Status History", "{{ 'artists.history.title' | t:lang() }}"),
    ("No catalog assets yet.", "{{ 'catalogRights.assets.empty' | t:lang() }}"),
    ("Catalog Assets", "{{ 'catalogRights.assets.title' | t:lang() }}"),
    ("No releases yet.", "{{ 'catalogRights.releases.empty' | t:lang() }}"),
    ("Catalog Releases", "{{ 'catalogRights.releases.title' | t:lang() }}"),
    ("No rights contracts yet.", "{{ 'catalogRights.contracts.empty' | t:lang() }}"),
    ("Rights Contracts", "{{ 'catalogRights.contracts.title' | t:lang() }}"),
    ("Rights Conflicts", "{{ 'catalogRights.conflicts.title' | t:lang() }}"),
    ("Contract Parties", "{{ 'catalogRights.contractDetail.parties' | t:lang() }}"),
    ("Submit for Approval", "{{ 'catalogRights.contractDetail.submit' | t:lang() }}"),
    ("No campaigns yet.", "{{ 'campaigns.list.empty' | t:lang() }}"),
    ("Create Campaign", "{{ 'campaigns.list.create' | t:lang() }}"),
    ("Compute ROI", "{{ 'campaigns.detail.roi' | t:lang() }}"),
    ("Set Budget", "{{ 'campaigns.detail.budget' | t:lang() }}"),
    ("Request approval", "{{ 'campaigns.detail.requestApproval' | t:lang() }}"),
    ("Campaigns", "{{ 'campaigns.list.title' | t:lang() }}"),
    ("Enterprise Analytics", "{{ 'businessAnalytics.dashboard.title' | t:lang() }}"),
    ("KPI Explorer", "{{ 'businessAnalytics.kpis.title' | t:lang() }}"),
    ("Business Alerts", "{{ 'businessAnalytics.alerts.title' | t:lang() }}"),
    ("No alerts.", "{{ 'businessAnalytics.alerts.empty' | t:lang() }}"),
    ("Data Quality", "{{ 'businessAnalytics.quality.title' | t:lang() }}"),
    ("Rule-Based Recommendations", "{{ 'businessAnalytics.recommendations.title' | t:lang() }}"),
    ("Customer Success", "{{ 'customerSuccess.dashboard.title' | t:lang() }}"),
    ("No risks.", "{{ 'customerSuccess.dashboard.noRisks' | t:lang() }}"),
    ("No support cases yet.", "{{ 'support.list.empty' | t:lang() }}"),
    ("Create ticket", "{{ 'support.list.create' | t:lang() }}"),
    ("Internal note", "{{ 'support.detail.internalNote' | t:lang() }}"),
    ("Privacy Center", "{{ 'compliance.privacy.title' | t:lang() }}"),
    ("Compliance Admin", "{{ 'compliance.admin.title' | t:lang() }}"),
    ("Platform Operations", "{{ 'platformOps.dashboard.title' | t:lang() }}"),
    ("No providers configured.", "{{ 'platformOps.dashboard.noProviders' | t:lang() }}"),
    ("No executive reports yet.", "{{ 'reporting.list.empty' | t:lang() }}"),
    ("Executive Reports", "{{ 'reporting.list.title' | t:lang() }}"),
    ("Business Decisions", "{{ 'decisions.list.title' | t:lang() }}"),
    ("Record decision", "{{ 'decisions.list.record' | t:lang() }}"),
    ("No decisions yet.", "{{ 'decisions.list.empty' | t:lang() }}"),
    ("Export CSV", "{{ 'reporting.detail.exportCsv' | t:lang() }}"),
    ("Acceso denegado", "{{ 'organizations.accessDenied.title' | t:lang() }}"),
    ("Invitaciones", "{{ 'organizations.invitations.title' | t:lang() }}"),
    ("Prospectos", "{{ 'crm.prospects.title' | t:lang() }}"),
    ("Contactos", "{{ 'crm.contacts.title' | t:lang() }}"),
    ("Miembros", "{{ 'organizations.members.title' | t:lang() }}"),
    ("Auditoría", "{{ 'organizations.audit.title' | t:lang() }}"),
    ("Soporte", "{{ 'support.list.title' | t:lang() }}"),
    ("Support", "{{ 'support.list.title' | t:lang() }}"),
    ("Loading…", "{{ 'common.loading' | t:lang() }}"),
    ("Loading...", "{{ 'common.loading' | t:lang() }}"),
    ("Cargando...", "{{ 'common.loading' | t:lang() }}"),
    ("Cargando…", "{{ 'common.loading' | t:lang() }}"),
    ("No disponible", "{{ 'common.notAvailable' | t:lang() }}"),
]

TS_REPLACEMENTS: list[tuple[str, str]] = [
    ("'Select an organization context.'", "this.i18n.t('common.orgRequiredContext')"),
    ('"Select an organization context."', "this.i18n.t('common.orgRequiredContext')"),
    ("'Select an organization'", "this.i18n.t('common.orgRequired')"),
    ('"Select an organization"', "this.i18n.t('common.orgRequired')"),
    ("'No active organization selected.'", "this.i18n.t('common.orgRequiredContext')"),
]

PACKAGES = [
    "billing", "organizations", "crm", "subscriptions", "artists",
    "catalog-rights", "campaigns", "business-analytics", "customer-success",
    "compliance", "platform-ops", "reporting",
]


def path_prefixes(file: Path) -> tuple[str, str]:
    depth = len(file.relative_to(ROOT).parts) - 1
    up = "../" * depth
    return f"{up}../core", f"{up}../shared"


def ensure_inject_import(content: str) -> str:
    m = re.search(r"import \{([^}]*)\} from '@angular/core'", content)
    if not m:
        return "import { Component, inject } from '@angular/core';\n" + content
    if "inject" in m.group(1):
        return content
    return content[: m.start(1)] + m.group(1).rstrip().rstrip(",") + ", inject" + content[m.end(1) :]


def inject_i18n(content: str, file: Path) -> str:
    core, shared = path_prefixes(file)
    if "TranslatePipe" not in content:
        imports = (
            f"import {{ I18nService }} from '{core}/services/i18n.service';\n"
            f"import {{ TranslatePipe }} from '{shared}/pipes/translate.pipe';\n"
            f"import {{ StatusLabelPipe }} from '{shared}/pipes/status-label.pipe';\n"
            f"import {{ LocaleDatePipe, LocaleMoneyPipe }} from '{shared}/pipes/locale-format.pipe';\n"
        )
        last = None
        for m in re.finditer(r"^import .+?;\s*$", content, re.M):
            last = m
        if last:
            content = content[: last.end()] + "\n" + imports + content[last.end() :]
        else:
            content = imports + content
    content = ensure_inject_import(content)
    content = re.sub(
        r"imports:\s*\[([^\]]*)\]",
        lambda m: m.group(0)
        if "TranslatePipe" in m.group(1)
        else "imports: ["
        + m.group(1).rstrip().rstrip(",")
        + ", TranslatePipe, StatusLabelPipe, LocaleMoneyPipe, LocaleDatePipe]",
        content,
        count=1,
    )
    if "readonly lang" not in content and "export class" in content:
        content = re.sub(
            r"(export class \w+[^{]*\{)",
            r"\1\n  private i18n = inject(I18nService);\n  readonly lang = this.i18n.lang;\n",
            content,
            count=1,
        )
    return content


def process(path: Path) -> bool:
    original = path.read_text(encoding="utf-8")
    content = re.sub(r'\s+i18n="[^"]*"', "", original)
    m = re.search(r"(template:\s*`)(.*?)(`\s*,)", content, re.S)
    tpl_changed = False
    if m:
        tpl = m.group(2)
        new_tpl = tpl
        for old, new in REPLACEMENTS:
            if old in new_tpl:
                new_tpl = new_tpl.replace(old, new)
        new_tpl = re.sub(
            r"\{\{\s*'\{\{\s*'([^']+)'\s*\|\s*t:lang\(\)\s*\}\}'\s*\|\s*t:lang\(\)\s*\}\}",
            r"{{ '\1' | t:lang() }}",
            new_tpl,
        )
        if new_tpl != tpl:
            content = content[: m.start(2)] + new_tpl + content[m.end(2) :]
            tpl_changed = True

    # class body TS replacements (after template)
    m2 = re.search(r"template:\s*`.*?`\s*,", content, re.S)
    if m2:
        head, tail = content[: m2.end()], content[m2.end() :]
        new_tail = tail
        for old, new in TS_REPLACEMENTS:
            if old in new_tail:
                new_tail = new_tail.replace(old, new)
        content = head + new_tail

    needs_pipe = "| t:lang()" in content or "this.i18n.t(" in content
    if needs_pipe:
        content = inject_i18n(content, path)

    if content != original:
        path.write_text(content, encoding="utf-8")
        return True
    return False


def main() -> None:
    changed: list[str] = []
    for pkg in PACKAGES:
        base = ROOT / pkg
        if not base.exists():
            continue
        for path in sorted(base.rglob("*.ts")):
            if path.name.endswith(".spec.ts"):
                continue
            if not (
                path.name.endswith(".page.ts")
                or "selector" in path.name
                or path.name.endswith(".component.ts")
            ):
                continue
            if process(path):
                changed.append(str(path.relative_to(ROOT)))
    print(f"Updated {len(changed)} files")
    for c in changed:
        print(c)


if __name__ == "__main__":
    main()
