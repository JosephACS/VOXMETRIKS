from __future__ import annotations

from typing import Any


def service_result(insight: str, data: list[Any] | dict[str, Any], metrics: dict[str, Any]) -> dict[str, Any]:
    """Standard service payload — no HTTP concerns."""
    return {
        "insight": insight,
        "data": data,
        "metrics": metrics,
    }
