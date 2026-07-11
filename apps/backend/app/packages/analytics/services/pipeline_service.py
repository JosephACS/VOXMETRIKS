"""Run the PocketBase → DuckDB ELT pipeline from the API layer."""

from __future__ import annotations

import os
import sys
import threading
from pathlib import Path
from typing import Any, Dict

from app.core.config import get_settings

# Serialize pipeline runs with API writes (same lock as get_write_conn)
_pipeline_lock = threading.Lock()

_PROJECT_ROOT = Path(__file__).resolve().parents[6]


def run_pocketbase_import() -> Dict[str, Any]:
    """
    Pull the ~100k Spotify CSV from PocketBase and rebuild the Gold warehouse.
    Requires POCKETBASE_EMAIL/PASSWORD and a running PocketBase instance.
    """
    settings = get_settings()
    if not settings.pocketbase_email.strip() or not settings.pocketbase_password.strip():
        raise ValueError(
            "PocketBase credentials missing. Set POCKETBASE_EMAIL and "
            "POCKETBASE_PASSWORD in .env before importing."
        )

    if str(_PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(_PROJECT_ROOT))

    os.environ["POCKETBASE_URL"] = settings.pocketbase_url
    os.environ["POCKETBASE_EMAIL"] = settings.pocketbase_email
    os.environ["POCKETBASE_PASSWORD"] = settings.pocketbase_password

    with _pipeline_lock:
        from elt.pipelines.elt_pipeline import run_pipeline

        return run_pipeline()
