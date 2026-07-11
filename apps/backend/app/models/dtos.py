from __future__ import annotations

from pydantic import BaseModel, Field


class PaginationDTO(BaseModel):
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=50, ge=1, le=500)


class DateRangeDTO(BaseModel):
    days: int = Field(default=30, ge=1, le=365)
