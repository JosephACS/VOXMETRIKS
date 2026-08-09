"""
VOXMETRIKS Medallion ELT DAG — Spec 048.

Airflow coordinates; analytics/elt/pipelines/elt_pipeline.py remains authoritative.
Tasks run isolated subprocesses — no DataFrames via XCom, no work at parse time.

Airflow 3 public imports:
  airflow.sdk.DAG
  airflow.providers.standard.operators.bash.BashOperator
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

# Parse-time constants only — no DuckDB / pipeline I/O here.
_STAGE_SCRIPT = "/opt/voxmetriks/analytics/elt/pipelines/orchestrated_pipeline.py"
_STAGES = (
    "preflight",
    "extract_bronze",
    "transform_silver",
    "load_staging",
    "build_gold_and_aggregates",
    "export_gold",
    "validate_warehouse",
    "finalize_run",
)

_DEFAULT_ARGS = {
    "owner": "voxmetriks",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
    "execution_timeout": timedelta(hours=2),
}


def _stage_command(stage: str) -> str:
    # Fixed shell command — dag_run id arrives via env VOXMETRIKS_DAG_RUN_ID (templated).
    return (
        f'python {_STAGE_SCRIPT} {stage} --dag-run-id "$VOXMETRIKS_DAG_RUN_ID"'
    )


with DAG(
    dag_id="voxmetriks_elt",
    description="VOXMETRIKS Medallion ELT (Bronze→Silver→Staging→Gold→AGG→Validate)",
    default_args=_DEFAULT_ARGS,
    schedule=None,
    catchup=False,
    max_active_runs=1,
    max_active_tasks=1,
    tags=["voxmetriks", "elt", "medallion", "spec-048"],
) as dag:
    previous = None
    for stage in _STAGES:
        task = BashOperator(
            task_id=stage,
            bash_command=_stage_command(stage),
            do_xcom_push=False,
            cwd="/opt/voxmetriks",
            env={
                "VOXMETRIKS_DATA_DIR": "/opt/voxmetriks/data",
                "DB_PATH": "/opt/voxmetriks/data/warehouse/voxmetrik.duckdb",
                "PYTHONPATH": "/opt/voxmetriks/analytics",
                # Jinja expands at task runtime into the process env (not shell string interp).
                "VOXMETRIKS_DAG_RUN_ID": "{{ run_id }}",
            },
            append_env=True,
        )
        if previous is not None:
            previous >> task
        previous = task

# Sanity for static tests (path string only; no I/O).
assert Path(_STAGE_SCRIPT).as_posix().endswith("orchestrated_pipeline.py")
