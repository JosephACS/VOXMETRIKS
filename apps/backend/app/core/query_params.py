"""Reusable FastAPI query dependencies — pagination, filters, sorting."""

from __future__ import annotations

from datetime import date
from typing import Any, Sequence, TypeVar

from fastapi import Query
from pydantic import BaseModel, Field, field_validator

from app.core.config import get_settings

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="1-based page number")
    page_size: int = Field(default=25, ge=1, le=200, description="Items per page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class SortParams(BaseModel):
    sort_by: str | None = Field(default=None, description="Field to sort by")
    sort_order: str = Field(default="desc", description="asc or desc")

    @field_validator("sort_order")
    @classmethod
    def normalize_order(cls, value: str) -> str:
        order = value.strip().lower()
        if order not in {"asc", "desc"}:
            raise ValueError("sort_order must be 'asc' or 'desc'")
        return order


class ListFilters(BaseModel):
    genre: str | None = Field(default=None, max_length=120)
    artist: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, max_length=80)
    platform: str | None = Field(default=None, max_length=80)
    device: str | None = Field(default=None, max_length=80)
    date_from: date | None = None
    date_to: date | None = None
    min_popularity: int | None = Field(default=None, ge=0, le=100)


def paginate_items(items: Sequence[T], pagination: PaginationParams) -> tuple[list[T], int]:
    total = len(items)
    start = pagination.offset
    end = start + pagination.page_size
    return list(items[start:end]), total


def apply_list_filters(items: list[dict[str, Any]], filters: ListFilters) -> list[dict[str, Any]]:
    """In-memory filter for already-fetched rows — additive, non-breaking."""
    result = items
    if filters.genre:
        needle = filters.genre.casefold()
        result = [r for r in result if needle in str(r.get("nombre_genero") or "").casefold()]
    if filters.artist:
        needle = filters.artist.casefold()
        result = [r for r in result if needle in str(r.get("nombre_artista") or "").casefold()]
    if filters.platform:
        needle = filters.platform.casefold()
        result = [r for r in result if needle in str(r.get("platform") or "").casefold()]
    if filters.device:
        needle = filters.device.casefold()
        result = [r for r in result if needle in str(r.get("device_type") or r.get("device") or "").casefold()]
    if filters.min_popularity is not None:
        result = [r for r in result if int(r.get("popularity") or 0) >= filters.min_popularity]
    return result


def sort_items(
    items: list[dict[str, Any]],
    sort: SortParams,
    *,
    default_field: str = "popularity",
) -> list[dict[str, Any]]:
    field = sort.sort_by or default_field
    reverse = sort.sort_order == "desc"

    def key_fn(row: dict[str, Any]) -> Any:
        value = row.get(field)
        if value is None:
            return float("-inf") if reverse else float("inf")
        return value

    return sorted(items, key=key_fn, reverse=reverse)


def get_pagination_params(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int | None = Query(
        None,
        ge=1,
        le=200,
        description="Page size; omit to use legacy limit-only mode",
    ),
) -> PaginationParams | None:
    if page_size is None:
        return None
    settings = get_settings()
    size = min(page_size, settings.pagination_max_page_size)
    return PaginationParams(page=page, page_size=size)


def get_sort_params(
    sort_by: str | None = Query(None, description="Sort field"),
    sort_order: str = Query("desc", description="asc or desc"),
) -> SortParams:
    return SortParams(sort_by=sort_by, sort_order=sort_order)


def get_list_filters(
    genre: str | None = Query(None, max_length=120),
    artist: str | None = Query(None, max_length=120),
    country: str | None = Query(None, max_length=80),
    platform: str | None = Query(None, max_length=80),
    device: str | None = Query(None, max_length=80),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    min_popularity: int | None = Query(None, ge=0, le=100),
) -> ListFilters:
    return ListFilters(
        genre=genre,
        artist=artist,
        country=country,
        platform=platform,
        device=device,
        date_from=date_from,
        date_to=date_to,
        min_popularity=min_popularity,
    )
