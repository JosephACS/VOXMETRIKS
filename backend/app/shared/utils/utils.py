"""
VOXMETRIK_V2 - Utilities
Helpers used across the application.
"""
import math
from typing import Any, Dict, List


def sanitize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Replace NaN / Infinity float values with None so JSON serialization
    never raises ValueError.
    """
    clean: Dict[str, Any] = {}
    for key, val in row.items():
        if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
            clean[key] = None
        else:
            clean[key] = val
    return clean


def sanitize_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [sanitize_row(r) for r in rows]


def clamp(value: int, minimum: int, maximum: int) -> int:
    """Clamp value between minimum and maximum."""
    return max(minimum, min(maximum, value))
