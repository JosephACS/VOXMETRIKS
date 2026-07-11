from __future__ import annotations


def clamp(value: float, *, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def min_max_scale(value: float, min_val: float, max_val: float, *, default: float = 0.5) -> float:
    if max_val <= min_val:
        return default
    return clamp((value - min_val) / (max_val - min_val))
