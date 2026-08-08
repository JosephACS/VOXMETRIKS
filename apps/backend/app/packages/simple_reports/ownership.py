# -*- coding: utf-8 -*-
"""Spec 040 — enterprise report ownership metadata (simple + complex).

Backend is the source of truth. Does not alter SQL or formulas.
Ownership is assigned from queried tables + business interpretation, not names alone.
Demo-backed tables (CRM/billing/royalties/campaigns/CS) keep their data but the
*owner module* is the enterprise domain that interprets the result (often control).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, Optional

# Canonical enterprise modules (product surface 040).
MODULE_ORGANIZATION = "organization"
MODULE_CATALOG_PUBLISHING = "catalog_publishing"
MODULE_CONTROL_DECISION = "control_decision"
MODULE_DATA_ENGINEERING = "data_engineering"

VALID_MODULES: FrozenSet[str] = frozenset(
    {
        MODULE_ORGANIZATION,
        MODULE_CATALOG_PUBLISHING,
        MODULE_CONTROL_DECISION,
        MODULE_DATA_ENGINEERING,
    }
)

MODULE_LABELS = {
    MODULE_ORGANIZATION: "Organización",
    MODULE_CATALOG_PUBLISHING: "Catálogo y publicación",
    MODULE_CONTROL_DECISION: "Control y decisión",
    MODULE_DATA_ENGINEERING: "Ingeniería de datos",
}

# Human categories (non-empty only when used).
VALID_CATEGORIES: FrozenSet[str] = frozenset(
    {
        "Alertas",
        "Indicadores",
        "Publicación",
        "Canciones",
        "Derechos",
        "Usuarios",
        "Organización",
        "Permisos",
        "Seguridad",
        "Resultados operativos",
        "Resultados monetarios simulados",
        "Operación",
        "Calidad de datos",
        "Cargas y trazabilidad",
        "Warehouse",
        "Consumo",
        "Suscripciones",
    }
)


@dataclass(frozen=True)
class ReportOwnership:
    business_module: str
    business_process: str
    category: str
    decision: str
    data_classification: str  # real | synthetic | simulated | demo | mixed | operational | unknown
    monetary_classification: Optional[str]  # None | simulated
    route: str
    tables: tuple[str, ...]
    demo_backend_dependency: str = ""  # empty if none
    owner_rationale: str = ""

    def __post_init__(self) -> None:
        if self.business_module not in VALID_MODULES:
            raise ValueError(f"invalid module {self.business_module}")
        if self.category not in VALID_CATEGORIES:
            raise ValueError(f"invalid category {self.category}")


def _o(
    module: str,
    process: str,
    category: str,
    decision: str,
    *,
    tables: tuple[str, ...] = (),
    data_classification: str = "operational",
    monetary_classification: Optional[str] = None,
    route: str = "",
    demo: str = "",
    rationale: str = "",
) -> ReportOwnership:
    return ReportOwnership(
        business_module=module,
        business_process=process,
        category=category,
        decision=decision,
        data_classification=data_classification,
        monetary_classification=monetary_classification,
        route=route,
        tables=tables,
        demo_backend_dependency=demo,
        owner_rationale=rationale,
    )


# ---------------------------------------------------------------------------
# 33 simple reports
# ---------------------------------------------------------------------------

SIMPLE_OWNERSHIP: Dict[str, ReportOwnership] = {
    "business-alerts-open": _o(
        MODULE_CONTROL_DECISION,
        "Supervisar desviaciones abiertas",
        "Alertas",
        "Priorizar atención sobre alertas críticas",
        tables=("app_business_alert",),
        route="/simple-reports?report=business-alerts-open&module=control_decision",
        rationale="Consulta app_business_alert; dominio Workpanel/control.",
    ),
    "kpi-last-update": _o(
        MODULE_CONTROL_DECISION,
        "Verificar frescura de indicadores",
        "Indicadores",
        "Detectar KPIs desactualizados",
        tables=("app_kpi_definition", "app_kpi_snapshot"),
        route="/simple-reports?report=kpi-last-update&module=control_decision",
        rationale="Snapshots KPI del panel de control.",
    ),
    "crm-opportunities-open": _o(
        MODULE_CONTROL_DECISION,
        "Interpretar embudo comercial (datos demo)",
        "Resultados operativos",
        "Ver oportunidades abiertas sin abrir módulo CRM",
        tables=("app_crm_opportunity",),
        data_classification="demo",
        route="/simple-reports?report=crm-opportunities-open&module=control_decision",
        demo="crm",
        rationale="Tabla CRM demo; el resultado se interpreta en Control (CRM UI fuera MVP).",
    ),
    "crm-quotations-pending": _o(
        MODULE_CONTROL_DECISION,
        "Seguimiento de aprobaciones comerciales (demo)",
        "Resultados operativos",
        "Acelerar cotizaciones pendientes",
        tables=("app_crm_approval_request", "app_crm_quotation_version"),
        data_classification="demo",
        route="/simple-reports?report=crm-quotations-pending&module=control_decision",
        demo="crm",
        rationale="Backend CRM retenido; propietario = control.",
    ),
    "campaigns-active": _o(
        MODULE_CONTROL_DECISION,
        "Supervisar campañas activas (demo)",
        "Resultados operativos",
        "Saber qué campañas están vigentes",
        tables=("app_campaign",),
        data_classification="demo",
        route="/simple-reports?report=campaigns-active&module=control_decision",
        demo="campaigns",
        rationale="Campañas fuera de menú; reporte en control.",
    ),
    "releases-pending-review": _o(
        MODULE_CATALOG_PUBLISHING,
        "Revisión de lanzamientos",
        "Publicación",
        "Priorizar cola de revisión",
        tables=("app_release_submission",),
        route="/simple-reports?report=releases-pending-review&module=catalog_publishing",
        rationale="Flujo publishing operativo MVP.",
    ),
    "release-review-issues-open": _o(
        MODULE_CATALOG_PUBLISHING,
        "Resolver observaciones de revisión",
        "Publicación",
        "Desbloquear publicaciones",
        tables=("app_release_review_issue",),
        route="/simple-reports?report=release-review-issues-open&module=catalog_publishing",
        rationale="Issues de review del mismo ciclo publishing.",
    ),
    "tracks-without-cover": _o(
        MODULE_CATALOG_PUBLISHING,
        "Completar metadatos visuales",
        "Canciones",
        "Asignar portadas faltantes",
        tables=("dim_track",),
        data_classification="mixed",
        route="/simple-reports?report=tracks-without-cover&module=catalog_publishing",
        rationale="Calidad de dim_track; audiencia engineer por access.",
    ),
    "tracks-incomplete-metadata": _o(
        MODULE_CATALOG_PUBLISHING,
        "Completar metadatos de catálogo",
        "Canciones",
        "Corregir artista/álbum/género faltantes",
        tables=("dim_track",),
        data_classification="mixed",
        route="/simple-reports?report=tracks-incomplete-metadata&module=catalog_publishing",
        rationale="Misma dimensión de catálogo.",
    ),
    "rights-contracts-active": _o(
        MODULE_CATALOG_PUBLISHING,
        "Controlar vigencia de derechos",
        "Derechos",
        "Verificar contratos activos antes de publicar",
        tables=("app_rights_contract",),
        route="/simple-reports?report=rights-contracts-active&module=catalog_publishing",
        rationale="Derechos mínimos del ciclo publishing (037).",
    ),
    "rights-conflicts-open": _o(
        MODULE_CATALOG_PUBLISHING,
        "Resolver conflictos de derechos",
        "Derechos",
        "Atender disputas abiertas",
        tables=("app_rights_conflict",),
        route="/simple-reports?report=rights-conflicts-open&module=catalog_publishing",
        rationale="Conflictos sobre activos del catálogo.",
    ),
    "rights-contracts-expiring": _o(
        MODULE_CATALOG_PUBLISHING,
        "Anticipar renovaciones de derechos",
        "Derechos",
        "Planificar renovaciones próximas",
        tables=("app_rights_contract",),
        route="/simple-reports?report=rights-contracts-expiring&module=catalog_publishing",
        rationale="Misma tabla de contratos de derechos.",
    ),
    "b2c-subscriptions-active": _o(
        MODULE_ORGANIZATION,
        "Base de suscriptores personales",
        "Usuarios",
        "Conocer usuarios con plan activo",
        tables=("personal_subscription",),
        route="/simple-reports?report=b2c-subscriptions-active&module=organization",
        rationale="Vista admin de usuarios/planes B2C; no es activity personal.",
    ),
    "b2c-subscriptions-past-due": _o(
        MODULE_ORGANIZATION,
        "Riesgo de retención B2C",
        "Usuarios",
        "Intervenir suscripciones en atraso",
        tables=("personal_subscription",),
        route="/simple-reports?report=b2c-subscriptions-past-due&module=organization",
        rationale="Misma base personal_subscription, audiencia admin.",
    ),
    "b2b-subscriptions-active": _o(
        MODULE_ORGANIZATION,
        "Cartera organizacional vigente",
        "Organización",
        "Ver orgs con suscripción activa",
        tables=("app_subscription",),
        route="/simple-reports?report=b2b-subscriptions-active&module=organization",
        rationale="Suscripciones por organization_id.",
    ),
    "b2b-subscriptions-past-due": _o(
        MODULE_ORGANIZATION,
        "Cobros y cancelaciones B2B",
        "Organización",
        "Gestionar orgs en atraso",
        tables=("app_subscription",),
        route="/simple-reports?report=b2b-subscriptions-past-due&module=organization",
        rationale="Misma tabla app_subscription.",
    ),
    "invoices-pending-overdue": _o(
        MODULE_CONTROL_DECISION,
        "Cartera pendiente (simulada)",
        "Resultados monetarios simulados",
        "Priorizar facturas vencidas sin operar pasarela",
        tables=("app_invoice",),
        data_classification="demo",
        monetary_classification="simulated",
        route="/simple-reports?report=invoices-pending-overdue&module=control_decision",
        demo="billing",
        rationale="Billing UI oculta; cifras interpretadas en control como simuladas.",
    ),
    "payment-attempts-failed": _o(
        MODULE_CONTROL_DECISION,
        "Fallos de cobro (simulados)",
        "Resultados monetarios simulados",
        "Revisar intentos fallidos",
        tables=("app_payment_attempt",),
        data_classification="demo",
        monetary_classification="simulated",
        route="/simple-reports?report=payment-attempts-failed&module=control_decision",
        demo="billing",
        rationale="Depende de backend billing demo.",
    ),
    "royalty-settlements-open": _o(
        MODULE_CONTROL_DECISION,
        "Liquidaciones abiertas (demo)",
        "Resultados monetarios simulados",
        "Cerrar liquidaciones pendientes",
        tables=("app_royalty_settlement_run",),
        data_classification="demo",
        monetary_classification="simulated",
        route="/simple-reports?report=royalty-settlements-open&module=control_decision",
        demo="royalties",
        rationale="Regalías UI fuera MVP; reporte en control.",
    ),
    "payouts-with-error": _o(
        MODULE_CONTROL_DECISION,
        "Pagos a titulares con error (demo)",
        "Resultados monetarios simulados",
        "Corregir payouts fallidos",
        tables=("app_payout_failure", "app_payout_instruction"),
        data_classification="demo",
        monetary_classification="simulated",
        route="/simple-reports?report=payouts-with-error&module=control_decision",
        demo="royalties",
        rationale="Backend payouts retenido por dependencia de reporte.",
    ),
    "support-cases-open": _o(
        MODULE_CONTROL_DECISION,
        "Casos de soporte abiertos (demo)",
        "Operación",
        "Atender backlog de soporte",
        tables=("app_support_case",),
        data_classification="demo",
        route="/simple-reports?report=support-cases-open&module=control_decision",
        demo="customer_success",
        rationale="CS UI oculta; interpretación operativa en control.",
    ),
    "cs-risks-open": _o(
        MODULE_CONTROL_DECISION,
        "Riesgos de retención (demo)",
        "Operación",
        "Intervenir riesgos abiertos",
        tables=("app_customer_risk", "app_customer_intervention"),
        data_classification="demo",
        route="/simple-reports?report=cs-risks-open&module=control_decision",
        demo="customer_success",
        rationale="Datos CS demo → control.",
    ),
    "cs-renewals-low-readiness": _o(
        MODULE_ORGANIZATION,
        "Preparación de renovación organizacional",
        "Organización",
        "Mejorar readiness de renovación",
        tables=("app_renewal_readiness",),
        data_classification="demo",
        route="/simple-reports?report=cs-renewals-low-readiness&module=organization",
        demo="customer_success",
        rationale="Filas por organization_id; proceso organizacional.",
    ),
    "playlists-empty": _o(
        MODULE_DATA_ENGINEERING,
        "Calidad de colecciones de usuario",
        "Calidad de datos",
        "Detectar playlists vacías en plataforma",
        tables=("app_playlist", "app_playlist_track"),
        route="/simple-reports?report=playlists-empty&module=data_engineering",
        rationale="access=engineer; calidad operacional de datos de app.",
    ),
    "tracks-without-audio": _o(
        MODULE_CATALOG_PUBLISHING,
        "Asegurar catálogo reproducible",
        "Canciones",
        "Asociar fuentes de audio faltantes",
        tables=("dim_track",),
        data_classification="mixed",
        route="/simple-reports?report=tracks-without-audio&module=catalog_publishing",
        rationale="Disponibilidad de reproducción del catálogo.",
    ),
    "data-quality-failed": _o(
        MODULE_DATA_ENGINEERING,
        "Controles de calidad fallidos",
        "Calidad de datos",
        "Corregir checks antes de publicar indicadores",
        tables=("app_data_quality_result",),
        route="/simple-reports?report=data-quality-failed&module=data_engineering",
        rationale="Resultados DQ de ingeniería.",
    ),
    "etl-loads-failed": _o(
        MODULE_DATA_ENGINEERING,
        "Cargas analíticas fallidas",
        "Cargas y trazabilidad",
        "Reintentar o diagnosticar jobs fallidos",
        tables=("app_job_execution",),
        route="/simple-reports?report=etl-loads-failed&module=data_engineering",
        rationale="Ejecuciones de plataforma usadas como proxy ETL.",
    ),
    "analytical-tables-refresh": _o(
        MODULE_DATA_ENGINEERING,
        "Frescura de tablas analíticas",
        "Warehouse",
        "Verificar actualización de gold/agg",
        tables=(),
        data_classification="synthetic",
        route="/simple-reports?report=analytical-tables-refresh&module=data_engineering",
        rationale="Marcas de tiempo sobre tablas analíticas del warehouse.",
    ),
    "audio-source-errors": _o(
        MODULE_CATALOG_PUBLISHING,
        "Errores de fuente de audio",
        "Canciones",
        "Reparar fuentes que fallan al reproducir",
        tables=("app_track_audio_source",),
        route="/simple-reports?report=audio-source-errors&module=catalog_publishing",
        rationale="Fuentes asociadas al catálogo playable.",
    ),
    "ops-incidents-open": _o(
        MODULE_DATA_ENGINEERING,
        "Incidentes operativos abiertos",
        "Operación",
        "Vigilar incidentes de plataforma",
        tables=("app_operational_incident",),
        route="/simple-reports?report=ops-incidents-open&module=data_engineering",
        rationale="access=engineer; operaciones técnicas.",
    ),
    "job-executions-failed": _o(
        MODULE_DATA_ENGINEERING,
        "Trabajos de plataforma fallidos",
        "Cargas y trazabilidad",
        "Corregir dead-letter / failed jobs",
        tables=("app_job_execution",),
        route="/simple-reports?report=job-executions-failed&module=data_engineering",
        rationale="Misma familia de ejecuciones que ETL.",
    ),
    "sessions-active": _o(
        MODULE_ORGANIZATION,
        "Supervisar accesos activos",
        "Seguridad",
        "Revisar sesiones vigentes (sin tokens)",
        tables=("app_session",),
        route="/simple-reports?report=sessions-active&module=organization",
        rationale="Administración de identidad/seguridad; access=admin.",
    ),
    "roles-permissions": _o(
        MODULE_ORGANIZATION,
        "Verificar roles y permisos",
        "Permisos",
        "Auditar matriz de permisos",
        tables=("app_platform_role", "app_business_role", "app_user"),
        route="/simple-reports?report=roles-permissions&module=organization",
        rationale="RBAC organizacional/plataforma.",
    ),
}


COMPLEX_OWNERSHIP: Dict[str, ReportOwnership] = {
    "income-by-month": _o(
        MODULE_CONTROL_DECISION,
        "Ingresos cobrados por mes (simulados)",
        "Resultados monetarios simulados",
        "Comparar cobros mensuales sin pasarela real",
        data_classification="demo",
        monetary_classification="simulated",
        route="/complex-reports?report=income-by-month&module=control_decision",
        demo="billing",
        rationale="Pagos registrados/conciliados demo → control.",
    ),
    "streams-by-day": _o(
        MODULE_CONTROL_DECISION,
        "Evolución diaria de reproducciones",
        "Consumo",
        "Observar tendencia de consumo",
        data_classification="synthetic",
        route="/complex-reports?report=streams-by-day&module=control_decision",
        rationale="Agregados warehouse; decisión transversal Workpanel.",
    ),
    "top-tracks-period": _o(
        MODULE_CONTROL_DECISION,
        "Ranking de canciones",
        "Consumo",
        "Identificar contenido top del periodo",
        data_classification="synthetic",
        route="/complex-reports?report=top-tracks-period&module=control_decision",
        rationale="Ranking analítico transversal (enlace secundario catálogo).",
    ),
    "top-artists-period": _o(
        MODULE_CONTROL_DECISION,
        "Ranking de artistas",
        "Consumo",
        "Identificar artistas top",
        data_classification="synthetic",
        route="/complex-reports?report=top-artists-period&module=control_decision",
        rationale="Mismo dominio de consumo analítico.",
    ),
    "top-genres-period": _o(
        MODULE_CONTROL_DECISION,
        "Comparación de géneros",
        "Consumo",
        "Ver géneros dominantes",
        data_classification="synthetic",
        route="/complex-reports?report=top-genres-period&module=control_decision",
        rationale="Consumo por género desde warehouse.",
    ),
    "opportunity-win-rate-month": _o(
        MODULE_CONTROL_DECISION,
        "Tasa de ganancia comercial (demo)",
        "Resultados operativos",
        "Evaluar efectividad de cierres",
        data_classification="demo",
        route="/complex-reports?report=opportunity-win-rate-month&module=control_decision",
        demo="crm",
        rationale="CRM demo → control.",
    ),
    "subscription-growth-month": _o(
        MODULE_ORGANIZATION,
        "Altas mensuales de suscripción",
        "Suscripciones",
        "Medir crecimiento de altas",
        data_classification="demo",
        route="/complex-reports?report=subscription-growth-month&module=organization",
        rationale="Crecimiento de base de suscripciones.",
    ),
    "releases-status-month": _o(
        MODULE_CATALOG_PUBLISHING,
        "Distribución de estados de lanzamiento",
        "Publicación",
        "Ver flujo aprobado/rechazado/pendiente",
        route="/complex-reports?report=releases-status-month&module=catalog_publishing",
        rationale="Estados del proceso publishing.",
    ),
    "campaign-roi": _o(
        MODULE_CONTROL_DECISION,
        "ROI por campaña (no disponible)",
        "Resultados operativos",
        "Comparar gasto vs ingreso atribuible",
        data_classification="demo",
        monetary_classification="simulated",
        route="/complex-reports?report=campaign-roi&module=control_decision",
        demo="campaigns",
        rationale="Marcado unavailable; propietario control.",
    ),
}


def get_simple_ownership(report_id: str) -> Optional[ReportOwnership]:
    return SIMPLE_OWNERSHIP.get(report_id)


def get_complex_ownership(report_id: str) -> Optional[ReportOwnership]:
    return COMPLEX_OWNERSHIP.get(report_id)


def validate_simple_coverage(report_ids: list[str]) -> list[str]:
    """Return list of error messages (empty if ok)."""
    errors: list[str] = []
    owned = set(SIMPLE_OWNERSHIP)
    ids = set(report_ids)
    missing = ids - owned
    extra = owned - ids
    if missing:
        errors.append(f"orphan reports without ownership: {sorted(missing)}")
    if extra:
        errors.append(f"ownership for unknown reports: {sorted(extra)}")
    if len(SIMPLE_OWNERSHIP) != len(owned):
        errors.append("duplicate ownership keys")
    for rid, o in SIMPLE_OWNERSHIP.items():
        if not o.route.startswith("/simple-reports"):
            errors.append(f"{rid}: route must be simple-reports canonical")
        if f"report={rid}" not in o.route:
            errors.append(f"{rid}: route must include report id")
    return errors


def validate_complex_coverage(report_ids: list[str]) -> list[str]:
    errors: list[str] = []
    owned = set(COMPLEX_OWNERSHIP)
    ids = set(report_ids)
    missing = ids - owned
    extra = owned - ids
    if missing:
        errors.append(f"orphan complex without ownership: {sorted(missing)}")
    if extra:
        errors.append(f"ownership for unknown complex: {sorted(extra)}")
    return errors
