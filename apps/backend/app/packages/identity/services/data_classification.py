# -*- coding: utf-8 -*-
"""Shared data provenance labels (spec 037).

Canonical values — do not invent parallel taxonomies:
  real | synthetic | simulated | demo | mixed | unknown
"""

from __future__ import annotations

from typing import Any, Optional

import duckdb

REAL = "real"
SYNTHETIC = "synthetic"
SIMULATED = "simulated"
DEMO = "demo"
MIXED = "mixed"
UNKNOWN = "unknown"

CANONICAL = frozenset({REAL, SYNTHETIC, SIMULATED, DEMO, MIXED, UNKNOWN})


def classify_warehouse_activity(conn: duckdb.DuckDBPyConnection) -> str:
    """Reuse events inventory classification for warehouse-backed metrics."""
    try:
        from app.packages.analytics.services.stats.events_inventory import (
            classify_activity_facts,
        )

        value = classify_activity_facts(conn)
        return value if value in CANONICAL else UNKNOWN
    except Exception:
        return UNKNOWN


def workpanel_classifications(
    conn: duckdb.DuckDBPyConnection,
    *,
    includes_synthetic_events: bool,
) -> dict[str, Any]:
    """Metadata for Workpanel responses — numbers unchanged."""
    warehouse = classify_warehouse_activity(conn)
    if includes_synthetic_events or warehouse == SYNTHETIC:
        data_classification = SYNTHETIC if warehouse == SYNTHETIC else MIXED
    else:
        data_classification = warehouse if warehouse != UNKNOWN else MIXED
    return {
        "data_classification": data_classification,
        "monetary_classification": SIMULATED,
        "classification_note": (
            "Indicadores analíticos pueden incluir eventos de warehouse sintéticos; "
            "importes monetarios del panel son de demostración o estimación académica, "
            "no dinero efectivamente cobrado."
        ),
    }


def report_data_classification(
    *,
    includes_synthetic_events: bool = False,
    monetary: bool = False,
) -> dict[str, Any]:
    data_classification = SYNTHETIC if includes_synthetic_events else UNKNOWN
    if monetary:
        return {
            "data_classification": data_classification,
            "monetary_classification": SIMULATED,
            "classification_note": (
                "Valores generados para análisis académico. No representan cobros reales."
            ),
        }
    if includes_synthetic_events:
        return {
            "data_classification": SYNTHETIC,
            "monetary_classification": None,
            "classification_note": (
                "Este resultado incluye o deriva de eventos sintéticos del warehouse."
            ),
        }
    return {
        "data_classification": data_classification,
        "monetary_classification": None,
        "classification_note": None,
    }
