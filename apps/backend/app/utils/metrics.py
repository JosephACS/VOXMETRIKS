from __future__ import annotations

from typing import Any


def build_metrics(**kwargs: Any) -> dict[str, Any]:
    """Standard metrics envelope for service responses."""
    return {k: v for k, v in kwargs.items() if v is not None}


def ok_payload(module: str, *, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    data = {"module": module, "ready": True}
    if extra:
        data.update(extra)
    return data
