from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class LimitQuery(BaseModel):
    limit: int = Field(default=50, ge=1, le=500, description="Maximum rows to return")

    @field_validator("limit", mode="before")
    @classmethod
    def sanitize_limit(cls, value: object) -> int:
        if value is None:
            return 50
        try:
            parsed = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("limit must be an integer") from exc
        return max(1, min(parsed, 500))


class DaysQuery(BaseModel):
    days: int = Field(default=90, ge=1, le=365, description="Number of recent days")

    @field_validator("days", mode="before")
    @classmethod
    def sanitize_days(cls, value: object) -> int:
        if value is None:
            return 90
        try:
            parsed = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("days must be an integer") from exc
        return max(1, min(parsed, 365))
