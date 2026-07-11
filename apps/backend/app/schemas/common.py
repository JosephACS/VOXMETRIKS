from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiMeta(BaseModel):
    count: int | None = None
    page: int | None = None
    limit: int | None = None
    page_size: int | None = None
    total: int | None = None
    source: str = "duckdb"


class ApiResponse(BaseModel, Generic[T]):
    status: str = Field(description="success | error")
    data: T | None = None
    meta: ApiMeta = Field(default_factory=ApiMeta)


class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


def success_response(
    data: Any,
    *,
    count: int | None = None,
    page: int | None = None,
    limit: int | None = None,
    page_size: int | None = None,
    total: int | None = None,
    source: str = "duckdb",
) -> dict[str, Any]:
    meta = ApiMeta(
        count=count,
        page=page,
        limit=limit,
        page_size=page_size,
        total=total,
        source=source,
    )
    return ApiResponse(status="success", data=data, meta=meta).model_dump(exclude_none=True)


def error_response(
    message: str,
    *,
    code: str = "error",
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = details or {}
    payload.setdefault("code", code)
    return ErrorResponse(status="error", message=message, details=payload).model_dump()
