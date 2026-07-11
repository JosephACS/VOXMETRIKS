from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class PipelineStageItem(BaseModel):
    id_stage: int
    run_id: int
    stage: str
    layer: str
    started_at: datetime
    duration_ms: int = 0
    rows_in: int = 0
    rows_out: int = 0
    status: str
    details: str | None = None


class PipelineLoadItem(BaseModel):
    id_carga: int
    fecha_carga: datetime
    modo: str
    registros_nuevos: int = 0
    total_raw: int = 0
    estado: str


class PipelineAuditResponse(BaseModel):
    stages: list[PipelineStageItem]
    loads: list[PipelineLoadItem]
    summary: dict


class DataQualityCheck(BaseModel):
    check_name: str
    status: str
    detail: str
    value: float | int | str | None = None


class DataQualityResponse(BaseModel):
    checks: list[DataQualityCheck]
    passed: int
    failed: int
    warnings: int


class HealthData(BaseModel):
    app: str
    version: str
    database: str
    table_count: int
    duckdb_version: str | None = None
    status: str
