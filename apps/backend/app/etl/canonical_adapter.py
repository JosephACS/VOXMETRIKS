"""Spec 014 Phase E — bridge between backend boot and canonical analytics/elt.

Roles
-----
* **CANONICAL_ANALYTICS_ELT** — ``analytics/elt/pipelines/elt_pipeline.py``
  (extract → bronze/silver parquet → dims/facts → enterprise analytics → DuckDB).
* **BACKEND_ONLY_RUNTIME** — ``app.etl.pipelines.run_full_etl`` refreshes
  bronze/silver/gold *aggregations* when ``raw_spotify`` already exists in the
  warehouse. It is **not** a second full warehouse builder.
* **BACKEND_ADAPTER** — this module: resolve the canonical script and optionally
  invoke it as a subprocess (ops / missing-warehouse bootstrap only).

Parity gap (documented, not papered over)
----------------------------------------
Full replacement of ``app.etl`` by invoking analytics/elt on every boot is
**not** demonstrable: different inputs (PocketBase/parquet vs in-DB
``raw_spotify``), different duration (often minutes+), and API boot must not
block on a full rebuild. Debt: async/worker orchestration → future spec.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("voxmetrik.elt.canonical")

CANONICAL_RELATIVE = Path("analytics") / "elt" / "pipelines" / "elt_pipeline.py"
# Docker image copies analytics/elt → /app/elt (see infrastructure/docker/Dockerfile).
DOCKER_RELATIVE = Path("elt") / "pipelines" / "elt_pipeline.py"


def project_root() -> Path:
    """Monorepo root (parent of ``apps/`` / ``data/``)."""
    settings = get_settings()
    # data_root is typically <repo>/data — parent is project root.
    root = settings.data_root.parent
    if (root / "apps" / "backend").is_dir() or (root / "analytics" / "elt").is_dir():
        return root
    # Fallback: walk up from this file (apps/backend/app/etl/canonical_adapter.py)
    here = Path(__file__).resolve()
    for candidate in here.parents:
        if (candidate / "analytics" / "elt" / "pipelines" / "elt_pipeline.py").is_file():
            return candidate
        if (candidate / "elt" / "pipelines" / "elt_pipeline.py").is_file():
            return candidate
    return root


def resolve_canonical_script(root: Path | None = None) -> Path | None:
    """Return path to the canonical ELT entrypoint if present."""
    base = root or project_root()
    for rel in (CANONICAL_RELATIVE, DOCKER_RELATIVE):
        candidate = base / rel
        if candidate.is_file():
            return candidate
    return None


def invoke_canonical_elt(
    *,
    timeout_s: int = 3600,
    db_path: Path | str | None = None,
    cwd: Path | None = None,
) -> dict[str, Any]:
    """Run canonical analytics/elt as a subprocess.

    Never call this from the default API boot path when the warehouse already
    exists — use ``RUN_ETL_ON_BOOT=always`` + missing warehouse, or ``make pipeline``.
    """
    root = cwd or project_root()
    script = resolve_canonical_script(root)
    if script is None:
        return {
            "status": "error",
            "errors": ["canonical_elt_script_not_found"],
            "script": None,
        }

    env = os.environ.copy()
    analytics_root = root / "analytics"
    path_parts = [str(root), str(root / "apps" / "backend")]
    if analytics_root.is_dir():
        path_parts.insert(0, str(analytics_root))
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join(path_parts + ([existing] if existing else []))

    if db_path is not None:
        env["DB_PATH"] = str(db_path)

    logger.info("[CANONICAL_ELT] Starting script=%s db=%s", script, env.get("DB_PATH", "(default)"))
    try:
        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(root),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        logger.error("[CANONICAL_ELT] Timed out after %ss", timeout_s)
        return {"status": "error", "errors": [f"timeout:{timeout_s}"], "script": str(script)}
    except Exception as exc:
        logger.exception("[CANONICAL_ELT] Failed to start")
        return {"status": "error", "errors": [str(exc)], "script": str(script)}

    ok = result.returncode == 0
    if not ok:
        logger.error(
            "[CANONICAL_ELT] Failed code=%s stderr=%s",
            result.returncode,
            (result.stderr or "")[-800:],
        )
    else:
        logger.info("[CANONICAL_ELT] Completed ok")

    return {
        "status": "ok" if ok else "error",
        "returncode": result.returncode,
        "script": str(script),
        "stdout_tail": (result.stdout or "")[-500:],
        "stderr_tail": (result.stderr or "")[-500:],
        "errors": [] if ok else [f"exit:{result.returncode}"],
    }
