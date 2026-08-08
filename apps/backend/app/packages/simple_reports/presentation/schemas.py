# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ReportColumnOut(BaseModel):
    key: str
    label: str


class ReportFilterOut(BaseModel):
    key: str
    label: str
    kind: str = "text"
    options: list[str] = Field(default_factory=list)


class SimpleReportCatalogItem(BaseModel):
    id: str
    area: str
    title: str
    description: str
    objective: str
    access: str
    org_scoped: bool
    implementation: str
    pending_reason: str = ""
    columns: list[ReportColumnOut]
    filters: list[ReportFilterOut]
    # Spec 040 — enterprise ownership (backend source of truth)
    business_module: str = ""
    business_module_label: str = ""
    business_process: str = ""
    category: str = ""
    decision: str = ""
    data_classification: str = "unknown"
    monetary_classification: Optional[str] = None
    route: str = ""
    demo_backend_dependency: str = ""
    report_type: str = "simple"


class SimpleReportCatalogResponse(BaseModel):
    items: list[SimpleReportCatalogItem]
    total: int
    modules: list[dict[str, str]] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)

class SimpleReportDataResponse(BaseModel):
    report_id: str
    title: str
    description: str
    columns: list[ReportColumnOut]
    items: list[dict[str, Any]]
    page: int
    page_size: int
    total: int
    implementation: str
    empty_message: str = "No se encontraron resultados para los filtros seleccionados."
    data_classification: str = "unknown"
    monetary_classification: Optional[str] = None
    classification_note: Optional[str] = None
