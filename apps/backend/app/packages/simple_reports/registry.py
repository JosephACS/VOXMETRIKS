# -*- coding: utf-8 -*-
"""Simple operational reports — Tarea 11 (BDR listings, no analytical aggregations)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass(frozen=True)
class ReportColumn:
    key: str
    label: str


@dataclass(frozen=True)
class ReportFilter:
    key: str
    label: str
    kind: str = "text"  # text | select | date
    options: tuple[str, ...] = ()


@dataclass(frozen=True)
class SimpleReportDef:
    id: str
    area: str
    title: str
    description: str
    objective: str
    columns: tuple[ReportColumn, ...]
    filters: tuple[ReportFilter, ...] = ()
    access: str = "staff"  # staff | engineer | admin | authenticated (personal only)
    org_scoped: bool = False
    implementation: str = "implemented"  # implemented | implemented_with_adjustment | pending
    pending_reason: str = ""
    sort_default: str = ""


# Access roles that may see each access level (spec 037: deny listener on enterprise).
# ``staff`` = operational enterprise reports (admin + engineer).
# ``authenticated`` reserved for genuinely personal reports (none in this registry).
ACCESS_ROLES = {
    "staff": {"admin", "engineer"},
    "authenticated": {"admin", "engineer"},  # no longer grants listener enterprise data
    "engineer": {"admin", "engineer"},
    "admin": {"admin"},
}


REPORTS: dict[str, SimpleReportDef] = {}


def _reg(r: SimpleReportDef) -> SimpleReportDef:
    REPORTS[r.id] = r
    return r


def all_reports() -> list[SimpleReportDef]:
    return list(REPORTS.values())


def get_report(report_id: str) -> Optional[SimpleReportDef]:
    return REPORTS.get(report_id)


# ---------------------------------------------------------------------------
# Registry — 33 simple reports from Tarea 11
# ---------------------------------------------------------------------------

_reg(SimpleReportDef(
    id="business-alerts-open",
    area="Dirección y control",
    title="Listado de alertas de negocio abiertas",
    description="Alertas todavía abiertas, con prioridad y fecha de generación.",
    objective="Detectar desviaciones de negocio que requieren atención inmediata.",
    columns=(
        ReportColumn("id", "ID"),
        ReportColumn("severity", "Prioridad"),
        ReportColumn("title", "Título"),
        ReportColumn("status", "Estado"),
        ReportColumn("created_at", "Fecha"),
    ),
    filters=(ReportFilter("severity", "Prioridad", "select", ("info", "warning", "critical")),),
    org_scoped=True,
    sort_default="created_at",
))

_reg(SimpleReportDef(
    id="kpi-last-update",
    area="Dirección y control",
    title="Fecha de última actualización de cada indicador",
    description="Cada indicador con la fecha de su última actualización registrada.",
    objective="Verificar si los tableros se actualizaron a tiempo.",
    columns=(
        ReportColumn("kpi_code", "Indicador"),
        ReportColumn("kpi_name", "Nombre"),
        ReportColumn("last_updated_at", "Última actualización"),
        ReportColumn("period", "Periodo"),
        ReportColumn("quality_status", "Calidad"),
    ),
    org_scoped=True,
    implementation="implemented_with_adjustment",
    pending_reason="Se usa la fecha del último snapshot de KPI como actualización del indicador.",
))

_reg(SimpleReportDef(
    id="crm-opportunities-open",
    area="Comercial y CRM",
    title="Listado de oportunidades comerciales abiertas",
    description="Oportunidades no cerradas, con etapa, responsable y valor estimado.",
    objective="Controlar la evolución del embudo comercial.",
    columns=(
        ReportColumn("id", "ID"),
        ReportColumn("stage", "Etapa"),
        ReportColumn("owner_user_id", "Responsable"),
        ReportColumn("expected_close_date", "Cierre esperado"),
        ReportColumn("updated_at", "Actualizado"),
    ),
    filters=(ReportFilter("stage", "Etapa", "text"),),
    org_scoped=True,
))

_reg(SimpleReportDef(
    id="crm-quotations-pending",
    area="Comercial y CRM",
    title="Listado de cotizaciones pendientes de aprobación",
    description="Cotizaciones o versiones que esperan aprobación.",
    objective="Acelerar las aprobaciones comerciales pendientes.",
    columns=(
        ReportColumn("id", "ID"),
        ReportColumn("object_type", "Tipo"),
        ReportColumn("object_id", "Objeto"),
        ReportColumn("status", "Estado"),
        ReportColumn("requested_at", "Solicitado"),
    ),
    org_scoped=True,
))

_reg(SimpleReportDef(
    id="campaigns-active",
    area="Marketing y campañas",
    title="Listado de campañas actualmente activas",
    description="Campañas con estado activo y fechas de vigencia.",
    objective="Supervisar qué campañas están en marcha.",
    columns=(
        ReportColumn("id", "ID"),
        ReportColumn("name", "Nombre"),
        ReportColumn("status", "Estado"),
        ReportColumn("start_date", "Inicio"),
        ReportColumn("end_date", "Fin"),
    ),
    org_scoped=True,
))

_reg(SimpleReportDef(
    id="releases-pending-review",
    area="Gestión artística y publicación",
    title="Listado de lanzamientos pendientes de revisión",
    description="Envíos en revisión o pendientes de decisión.",
    objective="Controlar el flujo de revisión y publicación.",
    columns=(
        ReportColumn("id", "ID"),
        ReportColumn("status", "Estado"),
        ReportColumn("reviewer_id", "Revisor"),
        ReportColumn("updated_at", "Actualizado"),
    ),
    filters=(ReportFilter("status", "Estado", "text"),),
    org_scoped=True,
))

_reg(SimpleReportDef(
    id="release-review-issues-open",
    area="Gestión artística y publicación",
    title="Listado de observaciones de revisión todavía abiertas",
    description="Observaciones o correcciones pendientes que bloquean la publicación.",
    objective="Controlar el flujo de revisión y publicación.",
    columns=(
        ReportColumn("id", "ID"),
        ReportColumn("submission_id", "Envío"),
        ReportColumn("severity", "Severidad"),
        ReportColumn("message", "Mensaje"),
        ReportColumn("resolved", "Resuelto"),
    ),
    org_scoped=True,
    implementation="implemented_with_adjustment",
    pending_reason="Se listan issues con resolved = false en app_release_review_issue.",
))

_reg(SimpleReportDef(
    id="tracks-without-cover",
    area="Catálogo y metadatos musicales",
    title="Listado de canciones sin portada",
    description="Canciones sin imagen de portada válida.",
    objective="Completar metadatos visuales del catálogo.",
    columns=(
        ReportColumn("track_id", "ID canción"),
        ReportColumn("track_name", "Canción"),
        ReportColumn("cover_status", "Estado portada"),
    ),
    access="engineer",
))

_reg(SimpleReportDef(
    id="tracks-incomplete-metadata",
    area="Catálogo y metadatos musicales",
    title="Listado de canciones con metadatos incompletos",
    description="Canciones a las que les falta artista, álbum o género.",
    objective="Completar metadatos del catálogo.",
    columns=(
        ReportColumn("track_id", "ID"),
        ReportColumn("track_name", "Canción"),
        ReportColumn("id_artista", "Artista"),
        ReportColumn("id_album", "Álbum"),
        ReportColumn("id_genero", "Género"),
    ),
    access="engineer",
))

_reg(SimpleReportDef(
    id="rights-contracts-active",
    area="Derechos musicales y contratos",
    title="Listado de contratos de derechos vigentes",
    description="Contratos activos con vigencia y tipo de derecho.",
    objective="Controlar la vigencia de los derechos.",
    columns=(
        ReportColumn("id", "ID"),
        ReportColumn("rights_type", "Tipo"),
        ReportColumn("status", "Estado"),
        ReportColumn("valid_from", "Desde"),
        ReportColumn("valid_to", "Hasta"),
    ),
    org_scoped=True,
))

_reg(SimpleReportDef(
    id="rights-conflicts-open",
    area="Derechos musicales y contratos",
    title="Listado de conflictos de derechos abiertos",
    description="Conflictos todavía abiertos sobre activos.",
    objective="Resolver disputas de derechos.",
    columns=(
        ReportColumn("id", "ID"),
        ReportColumn("asset_id", "Activo"),
        ReportColumn("rights_type", "Tipo"),
        ReportColumn("status", "Estado"),
        ReportColumn("territory_code", "Territorio"),
    ),
    org_scoped=True,
))

_reg(SimpleReportDef(
    id="rights-contracts-expiring",
    area="Derechos musicales y contratos",
    title="Listado de contratos próximos a vencer",
    description="Contratos vigentes cuya fecha de fin está próxima.",
    objective="Anticipar renovaciones de derechos.",
    columns=(
        ReportColumn("id", "ID"),
        ReportColumn("rights_type", "Tipo"),
        ReportColumn("status", "Estado"),
        ReportColumn("valid_to", "Vence"),
        ReportColumn("days_remaining", "Días restantes"),
    ),
    org_scoped=True,
    filters=(ReportFilter("within_days", "Días (máx.)", "text"),),
))

_reg(SimpleReportDef(
    id="b2c-subscriptions-active",
    area="Suscripciones B2C",
    title="Listado de usuarios con suscripción personal activa",
    description="Suscripciones personales en estado activo.",
    objective="Controlar la base de suscriptores personales.",
    columns=(
        ReportColumn("id", "ID"),
        ReportColumn("user_id", "Usuario"),
        ReportColumn("plan_id", "Plan"),
        ReportColumn("status", "Estado"),
        ReportColumn("current_period_end", "Fin periodo"),
    ),
    access="admin",
))

_reg(SimpleReportDef(
    id="b2c-subscriptions-past-due",
    area="Suscripciones B2C",
    title="Listado de suscripciones personales en atraso o con cancelación pendiente",
    description="Suscripciones en atraso o marcadas para cancelación.",
    objective="Recuperar o retener suscriptores en riesgo.",
    columns=(
        ReportColumn("id", "ID"),
        ReportColumn("user_id", "Usuario"),
        ReportColumn("status", "Estado"),
        ReportColumn("access_state", "Acceso"),
        ReportColumn("current_period_end", "Fin periodo"),
    ),
    access="admin",
))

_reg(SimpleReportDef(
    id="b2b-subscriptions-active",
    area="Suscripciones B2B",
    title="Listado de organizaciones con suscripción empresarial vigente",
    description="Suscripciones empresariales trialing o active.",
    objective="Controlar la cartera B2B vigente.",
    columns=(
        ReportColumn("id", "ID"),
        ReportColumn("organization_id", "Organización"),
        ReportColumn("plan_id", "Plan"),
        ReportColumn("status", "Estado"),
        ReportColumn("current_period_end", "Fin periodo"),
    ),
    access="admin",
))

_reg(SimpleReportDef(
    id="b2b-subscriptions-past-due",
    area="Suscripciones B2B",
    title="Listado de suscripciones empresariales en atraso o con cancelación pendiente",
    description="Suscripciones B2B en past_due o canceled pendientes.",
    objective="Gestionar cobros y cancelaciones empresariales.",
    columns=(
        ReportColumn("id", "ID"),
        ReportColumn("organization_id", "Organización"),
        ReportColumn("status", "Estado"),
        ReportColumn("access_state", "Acceso"),
        ReportColumn("current_period_end", "Fin periodo"),
    ),
    access="admin",
))

_reg(SimpleReportDef(
    id="invoices-pending-overdue",
    area="Finanzas y facturación",
    title="Listado de facturas pendientes y vencidas, ordenadas por fecha de vencimiento",
    description="Facturas emitidas, parcialmente pagadas o vencidas.",
    objective="Controlar la cartera y la recaudación.",
    columns=(
        ReportColumn("id", "ID"),
        ReportColumn("invoice_number", "Número"),
        ReportColumn("status", "Estado"),
        ReportColumn("total", "Importe"),
        ReportColumn("due_date", "Vencimiento"),
        ReportColumn("organization_id", "Cliente/Org"),
    ),
    filters=(ReportFilter("status", "Estado", "select", ("issued", "partially_paid", "past_due")),),
    org_scoped=True,
))

_reg(SimpleReportDef(
    id="payment-attempts-failed",
    area="Finanzas y facturación",
    title="Listado de intentos de pago fallidos",
    description="Intentos de pago con estado fallido y motivo.",
    objective="Controlar la cartera y la recaudación.",
    columns=(
        ReportColumn("id", "ID"),
        ReportColumn("invoice_id", "Factura"),
        ReportColumn("status", "Estado"),
        ReportColumn("failure_reason", "Motivo"),
        ReportColumn("created_at", "Fecha"),
    ),
    org_scoped=True,
))

_reg(SimpleReportDef(
    id="royalty-settlements-open",
    area="Regalías y pagos",
    title="Listado de liquidaciones todavía no finalizadas",
    description="Liquidaciones cuyo estado no es finalized ni reversed.",
    objective="Cerrar liquidaciones pendientes.",
    columns=(
        ReportColumn("id", "ID"),
        ReportColumn("status", "Estado"),
        ReportColumn("period_start", "Inicio"),
        ReportColumn("period_end", "Fin"),
        ReportColumn("updated_at", "Actualizado"),
    ),
    org_scoped=True,
))

_reg(SimpleReportDef(
    id="payouts-with-error",
    area="Regalías y pagos",
    title="Listado de pagos a titulares con error",
    description="Instrucciones o fallos de pago a titulares.",
    objective="Corregir pagos fallidos a titulares.",
    columns=(
        ReportColumn("id", "ID"),
        ReportColumn("instruction_id", "Instrucción"),
        ReportColumn("failure_code", "Código"),
        ReportColumn("message", "Mensaje"),
        ReportColumn("created_at", "Fecha"),
    ),
    org_scoped=False,
))

_reg(SimpleReportDef(
    id="support-cases-open",
    area="Soporte al cliente",
    title="Listado de casos de soporte sin resolver",
    description="Casos que aún no están resueltos ni cerrados.",
    objective="Atender casos que siguen sin resolver.",
    columns=(
        ReportColumn("id", "ID"),
        ReportColumn("priority", "Prioridad"),
        ReportColumn("status", "Estado"),
        ReportColumn("subject", "Asunto"),
        ReportColumn("created_at", "Creado"),
    ),
    filters=(ReportFilter("priority", "Prioridad", "text"),),
    org_scoped=True,
))

_reg(SimpleReportDef(
    id="cs-risks-open",
    area="Éxito y retención del cliente",
    title="Listado de riesgos e intervenciones de acompañamiento y retención del cliente todavía abiertos",
    description="Riesgos abiertos e intervenciones en curso.",
    objective="Reducir la pérdida de clientes empresariales.",
    columns=(
        ReportColumn("id", "ID"),
        ReportColumn("kind", "Tipo"),
        ReportColumn("status", "Estado"),
        ReportColumn("severity", "Severidad"),
        ReportColumn("organization_id", "Organización"),
        ReportColumn("updated_at", "Actualizado"),
    ),
    org_scoped=True,
))

_reg(SimpleReportDef(
    id="cs-renewals-low-readiness",
    area="Éxito y retención del cliente",
    title="Listado de organizaciones con renovación próxima y baja preparación",
    description="Renovaciones próximas con preparación baja.",
    objective="Mejorar la preparación para renovar.",
    columns=(
        ReportColumn("id", "ID"),
        ReportColumn("organization_id", "Organización"),
        ReportColumn("readiness_state", "Preparación"),
        ReportColumn("score", "Puntaje"),
        ReportColumn("evaluated_at", "Evaluado"),
    ),
    org_scoped=True,
))

_reg(SimpleReportDef(
    id="playlists-empty",
    area="Experiencia del usuario",
    title="Listado de playlists vacías",
    description="Playlists que no tienen canciones asociadas.",
    objective="Mejorar el uso de playlists.",
    columns=(
        ReportColumn("id", "ID"),
        ReportColumn("name", "Nombre"),
        ReportColumn("user_id", "Usuario"),
        ReportColumn("created_at", "Creada"),
    ),
    access="engineer",
))

_reg(SimpleReportDef(
    id="tracks-without-audio",
    area="Reproducción y consumo",
    title="Listado de canciones sin una fuente de audio disponible",
    description="Canciones del catálogo sin fuente de audio asociada.",
    objective="Asegurar que el catálogo sea reproducible.",
    columns=(
        ReportColumn("track_id", "ID"),
        ReportColumn("track_name", "Canción"),
    ),
    access="engineer",
))

_reg(SimpleReportDef(
    id="data-quality-failed",
    area="Analítica e inteligencia de negocio",
    title="Listado de controles de calidad de datos que fallaron",
    description="Resultados de calidad con estado fallido.",
    objective="Corregir fallos de calidad antes de publicar indicadores.",
    columns=(
        ReportColumn("id", "ID"),
        ReportColumn("check_code", "Control"),
        ReportColumn("status", "Estado"),
        ReportColumn("details", "Detalle"),
        ReportColumn("measured_at", "Medido"),
    ),
    access="engineer",
    org_scoped=False,
))

_reg(SimpleReportDef(
    id="etl-loads-failed",
    area="Ingeniería de datos",
    title="Listado de cargas ETL fallidas",
    description="Ejecuciones de trabajos de carga o ETL con fallo.",
    objective="Controlar la ejecución de las cargas analíticas.",
    columns=(
        ReportColumn("id", "ID"),
        ReportColumn("job_id", "Trabajo"),
        ReportColumn("job_code", "Código"),
        ReportColumn("status", "Estado"),
        ReportColumn("error_message", "Error"),
        ReportColumn("finished_at", "Fin"),
    ),
    access="engineer",
    implementation="implemented_with_adjustment",
    pending_reason="No existe tabla ETL dedicada; se usan ejecuciones fallidas de trabajos de plataforma.",
))

_reg(SimpleReportDef(
    id="analytical-tables-refresh",
    area="Ingeniería de datos",
    title="Fecha de última actualización de cada tabla analítica",
    description="Tablas analíticas conocidas con su marca de tiempo más reciente disponible.",
    objective="Verificar la actualización de tablas analíticas.",
    columns=(
        ReportColumn("table_name", "Tabla"),
        ReportColumn("last_updated_at", "Última actualización"),
        ReportColumn("source", "Fuente de fecha"),
    ),
    access="engineer",
    implementation="implemented_with_adjustment",
    pending_reason="Se consulta marca de tiempo disponible (computed_at / max fecha) en tablas gold conocidas.",
))

_reg(SimpleReportDef(
    id="audio-source-errors",
    area="Operaciones de la plataforma",
    title="Listado de canciones con errores de fuente de audio",
    description="Fuentes asociadas que fallan al reproducirse.",
    objective="Detectar canciones que fallan al reproducirse aunque tengan fuente asociada.",
    columns=(
        ReportColumn("track_id", "ID"),
        ReportColumn("track_name", "Canción"),
        ReportColumn("provider", "Proveedor"),
        ReportColumn("status", "Estado"),
        ReportColumn("failure_count", "Fallos"),
    ),
    access="engineer",
))

_reg(SimpleReportDef(
    id="ops-incidents-open",
    area="Operaciones de la plataforma",
    title="Listado de incidentes operativos abiertos",
    description="Incidentes con estado abierto o en investigación.",
    objective="Vigilar incidentes operativos abiertos.",
    columns=(
        ReportColumn("id", "ID"),
        ReportColumn("title", "Título"),
        ReportColumn("severity", "Severidad"),
        ReportColumn("status", "Estado"),
        ReportColumn("reported_at", "Reportado"),
    ),
    access="engineer",
))

_reg(SimpleReportDef(
    id="job-executions-failed",
    area="Operaciones de la plataforma",
    title="Listado de ejecuciones de trabajos con fallo",
    description="Ejecuciones de trabajos en failed o dead_letter.",
    objective="Corregir trabajos fallidos de la plataforma.",
    columns=(
        ReportColumn("id", "ID"),
        ReportColumn("job_id", "Trabajo"),
        ReportColumn("status", "Estado"),
        ReportColumn("error_message", "Error"),
        ReportColumn("finished_at", "Fin"),
    ),
    access="engineer",
))

_reg(SimpleReportDef(
    id="sessions-active",
    area="Administración y seguridad",
    title="Listado de sesiones de usuario vigentes",
    description="Sesiones no expiradas (sin exponer el token).",
    objective="Supervisar accesos activos.",
    columns=(
        ReportColumn("user_id", "Usuario"),
        ReportColumn("email", "Correo"),
        ReportColumn("created_at", "Inicio"),
        ReportColumn("expires_at", "Expira"),
    ),
    access="admin",
))

_reg(SimpleReportDef(
    id="roles-permissions",
    area="Administración y seguridad",
    title="Listado de roles y permisos del sistema",
    description="Roles configurados y permisos asociados.",
    objective="Verificar roles y permisos definidos en la plataforma.",
    columns=(
        ReportColumn("role_code", "Rol"),
        ReportColumn("role_name", "Nombre"),
        ReportColumn("permission_code", "Permiso"),
        ReportColumn("scope", "Ámbito"),
    ),
    access="admin",
))


assert len(REPORTS) == 33, f"Expected 33 simple reports, got {len(REPORTS)}"
