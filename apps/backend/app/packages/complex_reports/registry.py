# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class ComplexReportDef:
    id: str
    area: str
    title: str
    question: str
    description: str
    calculation: str
    chart_type: str  # line | bar | hbar | table | card
    access: str = "staff"  # staff | engineer | admin | authenticated (personal only)
    available: bool = True
    unavailable_reason: str = ""
    filters: tuple[str, ...] = ("from", "to")


# Spec 037: enterprise complex reports are staff-only; listeners get 403.
ACCESS_ROLES = {
    "staff": {"admin", "engineer"},
    "authenticated": {"admin", "engineer"},
    "engineer": {"admin", "engineer"},
    "admin": {"admin"},
}

REPORTS: dict[str, ComplexReportDef] = {}


def _reg(r: ComplexReportDef) -> ComplexReportDef:
    REPORTS[r.id] = r
    return r


def all_reports() -> list[ComplexReportDef]:
    return list(REPORTS.values())


def get_report(report_id: str) -> Optional[ComplexReportDef]:
    return REPORTS.get(report_id)


_reg(ComplexReportDef(
    id="income-by-month",
    area="Finanzas",
    title="Ingresos cobrados por mes",
    question="¿Cuánto dinero se cobró cada mes?",
    description="Total de pagos registrados o conciliados agrupados por mes.",
    calculation="Se suman los importes de pagos con estado registrado o conciliado y se agrupan por mes de liquidación o creación.",
    chart_type="bar",
    access="admin",
))

_reg(ComplexReportDef(
    id="streams-by-day",
    area="Consumo musical",
    title="Reproducciones por día",
    question="¿Cuántas reproducciones ocurren cada día?",
    description="Evolución diaria del total de reproducciones.",
    calculation="Se suma el total de reproducciones de cada día en el periodo.",
    chart_type="line",
))

_reg(ComplexReportDef(
    id="top-tracks-period",
    area="Consumo musical",
    title="Canciones con más reproducciones",
    question="¿Qué canciones se reprodujeron más en el periodo?",
    description="Ranking de canciones según reproducciones.",
    calculation="Se agrupan los eventos de reproducción por canción, se suman y se ordenan de mayor a menor.",
    chart_type="hbar",
))

_reg(ComplexReportDef(
    id="top-artists-period",
    area="Consumo musical",
    title="Artistas con más reproducciones",
    question="¿Qué artistas concentran más reproducciones en el periodo?",
    description="Ranking de artistas según reproducciones.",
    calculation="Se suman las reproducciones por artista en el periodo y se ordenan de mayor a menor.",
    chart_type="hbar",
))

_reg(ComplexReportDef(
    id="top-genres-period",
    area="Consumo musical",
    title="Géneros más escuchados",
    question="¿Qué géneros se escuchan más en el periodo?",
    description="Comparación de reproducciones por género.",
    calculation="Se suman las reproducciones asociadas a cada género y se ordenan.",
    chart_type="bar",
))

_reg(ComplexReportDef(
    id="opportunity-win-rate-month",
    area="Comercial",
    title="Porcentaje de oportunidades ganadas por mes",
    question="¿Qué proporción de cierres se ganan cada mes?",
    description="De las oportunidades cerradas, qué porcentaje terminó ganada.",
    calculation="Se cuentan ganadas y cerradas por mes; el porcentaje es ganadas / cerradas × 100.",
    chart_type="line",
    access="admin",
))

_reg(ComplexReportDef(
    id="subscription-growth-month",
    area="Suscripciones",
    title="Crecimiento mensual de suscripciones",
    question="¿Cuántas suscripciones nuevas hay cada mes?",
    description="Altas de suscripciones agrupadas por mes.",
    calculation="Se cuentan las suscripciones según el mes de su fecha de alta.",
    chart_type="bar",
    access="admin",
))

_reg(ComplexReportDef(
    id="releases-status-month",
    area="Publicación",
    title="Lanzamientos por estado y mes",
    question="¿Cómo se distribuyen aprobados, rechazados y pendientes por mes?",
    description="Conteo de envíos de lanzamiento agrupados por mes y estado.",
    calculation="Se agrupan los envíos por mes y estado final, y se cuenta cada grupo.",
    chart_type="bar",
    access="engineer",
))

_reg(ComplexReportDef(
    id="campaign-roi",
    area="Marketing",
    title="Retorno de inversión por campaña",
    question="¿Qué campañas recuperaron la inversión?",
    description="Comparación de gasto e ingreso atribuible por campaña.",
    calculation="Requiere registro continuo de ingresos atribuibles a campañas.",
    chart_type="table",
    access="admin",
    available=False,
    unavailable_reason="faltan ingresos atribuibles directamente a cada campaña.",
))

assert len(REPORTS) >= 8
