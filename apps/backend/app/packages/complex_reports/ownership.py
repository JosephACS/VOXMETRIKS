# -*- coding: utf-8 -*-
"""Re-export complex ownership from consolidated 040 map."""

from app.packages.simple_reports.ownership import (
    COMPLEX_OWNERSHIP,
    MODULE_LABELS,
    VALID_MODULES,
    get_complex_ownership,
    validate_complex_coverage,
)

__all__ = [
    "COMPLEX_OWNERSHIP",
    "MODULE_LABELS",
    "VALID_MODULES",
    "get_complex_ownership",
    "validate_complex_coverage",
]
