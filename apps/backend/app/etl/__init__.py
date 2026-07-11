"""Medallion ELT package.

Spec 014 Phase E
----------------
* Canonical warehouse builder: ``analytics/elt`` (see ``canonical_adapter``).
* This package remains the **backend runtime** Bronze→Silver→Gold refresh used
  by tests and optional boot when ``raw_spotify`` already exists.
* Do not delete these modules while consumers (tests, boot, synthetic) remain.
"""

from app.etl.pipelines import run_full_etl, run_full_pipeline

__all__ = ["run_full_etl", "run_full_pipeline"]
