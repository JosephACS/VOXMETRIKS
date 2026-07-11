from __future__ import annotations

from pydantic import BaseModel, Field


class TableSummaryItem(BaseModel):
    table_name: str
    row_count: int = 0
    estimated_size: int | None = None
    layer: str | None = None


class QueryLatencyProbe(BaseModel):
    label: str
    latency_ms: float


class DatabaseHealth(BaseModel):
    status: str
    path: str
    size_mb: float
    duckdb_version: str | None = None
    table_count: int = 0


class PipelineHealthSummary(BaseModel):
    healthy: bool
    total_runs: int = 0
    failed_stages: int = 0
    last_stage: str | None = None
    last_status: str | None = None
    bottleneck_stage: str | None = None


class DataQualitySummary(BaseModel):
    healthy: bool
    passed: int = 0
    warnings: int = 0
    failed: int = 0


class FullHealthResponse(BaseModel):
    status: str
    environment: str
    database: DatabaseHealth
    pipeline: PipelineHealthSummary
    data_quality: DataQualitySummary
    query_latency: list[QueryLatencyProbe]
    tables: list[TableSummaryItem]
    total_latency_ms: float = Field(description="End-to-end health probe duration")
