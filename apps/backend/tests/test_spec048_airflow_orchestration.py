"""Spec 048 — directed tests for Airflow-orchestrated Medallion ELT."""

from __future__ import annotations

import ast
import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

import duckdb
import pandas as pd
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[3]
ORCH = ROOT / "analytics" / "elt" / "pipelines" / "orchestrated_pipeline.py"
ELT = ROOT / "analytics" / "elt" / "pipelines" / "elt_pipeline.py"
DAG = ROOT / "infrastructure" / "airflow" / "dags" / "voxmetriks_elt.py"
AIRFLOW_COMPOSE = ROOT / "infrastructure" / "airflow" / "compose.yml"
ROOT_COMPOSE = ROOT / "compose.yml"
ENV_EXAMPLE = ROOT / "infrastructure" / "airflow" / ".env.example"
DOCKERFILE = ROOT / "infrastructure" / "airflow" / "Dockerfile"
AIRFLOW_REQ = ROOT / "infrastructure" / "airflow" / "requirements.txt"
MAKEFILE_INFRA = ROOT / "infrastructure" / "Makefile"

STAGES = [
    "preflight",
    "extract_bronze",
    "transform_silver",
    "load_staging",
    "build_gold_and_aggregates",
    "export_gold",
    "validate_warehouse",
    "finalize_run",
]

REQUIRED_BEFORE_FINALIZE = [
    "extract_bronze",
    "transform_silver",
    "load_staging",
    "build_gold_and_aggregates",
    "export_gold",
    "validate_warehouse",
]


def _run_orch(stage: str, env: dict, dag_run_id: str = "test-run") -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(ORCH), stage, "--dag-run-id", dag_run_id]
    return subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True)


def _isolated_env(tmp_path: Path) -> dict:
    data = tmp_path / "data"
    for sub in ("bronze", "silver", "gold", "warehouse"):
        (data / sub).mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["VOXMETRIKS_DATA_DIR"] = str(data)
    env["DB_PATH"] = str(data / "warehouse" / "voxmetrik.duckdb")
    env["PYTHONPATH"] = os.pathsep.join(
        [str(ROOT), str(ROOT / "analytics"), env.get("PYTHONPATH", "")]
    )
    env.pop("POCKETBASE_EMAIL", None)
    env.pop("POCKETBASE_PASSWORD", None)
    return env


def _seed_bronze(env: dict, rows: int = 80) -> Path:
    data = Path(env["VOXMETRIKS_DATA_DIR"])
    bronze = data / "bronze" / "raw_spotify.parquet"
    df = pd.DataFrame(
        {
            "id": list(range(1, rows + 1)),
            "track_id": [f"t{i}" for i in range(rows)],
            "artists": [f"Artist {i % 5}" for i in range(rows)],
            "album_name": [f"Album {i % 3}" for i in range(rows)],
            "track_name": [f"Track {i}" for i in range(rows)],
            "popularity": [i % 100 for i in range(rows)],
            "duration_ms": [180000 + i for i in range(rows)],
            "explicit": [False] * rows,
            "danceability": [0.5] * rows,
            "energy": [0.5] * rows,
            "key": [1] * rows,
            "loudness": [-5.0] * rows,
            "mode": [1] * rows,
            "speechiness": [0.1] * rows,
            "acousticness": [0.2] * rows,
            "instrumentalness": [0.0] * rows,
            "liveness": [0.1] * rows,
            "valence": [0.5] * rows,
            "tempo": [120.0] * rows,
            "time_signature": [4] * rows,
            "track_genre": ["pop"] * rows,
        }
    )
    df.to_parquet(bronze, index=False)
    return bronze


def _load_orch_module(env: dict, module_key: str, monkeypatch):
    """Load a fresh orchestrated_pipeline bound to the isolated env paths."""
    for key in (
        "VOXMETRIKS_DATA_DIR",
        "DB_PATH",
        "POCKETBASE_EMAIL",
        "POCKETBASE_PASSWORD",
        "POCKETBASE_URL",
    ):
        if key in env and env[key] is not None:
            monkeypatch.setenv(key, env[key])
        elif key.startswith("POCKETBASE"):
            monkeypatch.delenv(key, raising=False)
    # Drop prior ELT modules so path constants re-resolve.
    drop = [
        name
        for name in list(sys.modules)
        if name in {"elt_pipeline_orch", "enterprise_analytics_orch"}
        or name.endswith("orchestrated_pipeline")
        or name == "elt.pipelines.elt_pipeline"
        or name.startswith("elt.pipelines")
        or name.startswith("elt.transform")
    ]
    for name in drop:
        del sys.modules[name]
    analytics = str(ROOT / "analytics")
    if analytics not in sys.path:
        sys.path.insert(0, analytics)
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location(module_key, ORCH)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_key] = mod
    spec.loader.exec_module(mod)
    return mod


def _ensure_ctl_schema(db_path: str) -> None:
    conn = duckdb.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ctl_pipeline_stages (
            id_stage INTEGER PRIMARY KEY,
            run_id INTEGER NOT NULL,
            stage VARCHAR NOT NULL,
            layer VARCHAR NOT NULL,
            started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            duration_ms INTEGER DEFAULT 0,
            rows_in INTEGER DEFAULT 0,
            rows_out INTEGER DEFAULT 0,
            status VARCHAR NOT NULL DEFAULT 'OK',
            details VARCHAR
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ctl_carga_dataset (
            id_carga INTEGER PRIMARY KEY,
            fecha_carga TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            modo VARCHAR,
            registros_nuevos INTEGER,
            total_raw INTEGER,
            estado VARCHAR
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ctl_auditoria (
            id_auditoria INTEGER PRIMARY KEY,
            accion VARCHAR NOT NULL,
            tabla_afectada VARCHAR,
            fecha_evento TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            detalles VARCHAR
        )
        """
    )
    conn.close()


def _insert_ctl(db_path: str, ctl_run_id: int, stage: str, status: str = "OK") -> None:
    conn = duckdb.connect(db_path)
    next_id = conn.execute(
        "SELECT COALESCE(MAX(id_stage), 0) + 1 FROM ctl_pipeline_stages"
    ).fetchone()[0]
    conn.execute(
        """
        INSERT INTO ctl_pipeline_stages
        (id_stage, run_id, stage, layer, duration_ms, rows_in, rows_out, status, details)
        VALUES (?, ?, ?, 'Gold', 1, 0, 0, ?, ?)
        """,
        [next_id, ctl_run_id, stage, status, f"dag_run_id=seed; stage={stage}"],
    )
    conn.close()


def test_dag_stage_order_and_dependencies():
    src = DAG.read_text(encoding="utf-8")
    tree = ast.parse(src)
    stages = None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "_STAGES":
                    stages = ast.literal_eval(node.value)
    assert list(stages) == STAGES
    assert "previous >> task" in src
    assert "max_active_runs=1" in src
    assert "max_active_tasks=1" in src
    assert "schedule=None" in src
    assert "catchup=False" in src


def test_dag_public_airflow3_imports_and_run_id_via_env():
    src = DAG.read_text(encoding="utf-8")
    assert "from airflow.sdk import DAG" in src
    assert "from airflow.providers.standard.operators.bash import BashOperator" in src
    assert "VOXMETRIKS_DAG_RUN_ID" in src
    assert "$VOXMETRIKS_DAG_RUN_ID" in src
    assert "bash_command" in src
    # Jinja may appear in env mapping; must not be shell-interpolated inside bash_command builders.
    tree = ast.parse(src)

    def _const(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None

    bash_literals: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            for kw in node.keywords:
                if kw.arg == "bash_command":
                    lit = _const(kw.value)
                    if lit is not None:
                        bash_literals.append(lit)
                    elif isinstance(kw.value, ast.Call):
                        # _stage_command("…") — inspect function body returns
                        pass
    # From _stage_command f-string returns
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "_stage_command":
            for sub in ast.walk(node):
                if isinstance(sub, ast.JoinedStr):
                    text = "".join(
                        (v.value if isinstance(v, ast.Constant) else "{" + "expr" + "}")
                        for v in sub.values
                    )
                    bash_literals.append(text)
                lit = _const(sub)
                if lit:
                    bash_literals.append(lit)
    joined = "\n".join(bash_literals)
    assert "{{ run_id }}" not in joined
    assert "$VOXMETRIKS_DAG_RUN_ID" in joined
    # Env carries the Jinja token.
    assert '"VOXMETRIKS_DAG_RUN_ID": "{{ run_id }}"' in src or "'{{ run_id }}'" in src


def test_dag_no_work_at_import_parse():
    src = DAG.read_text(encoding="utf-8")
    for token in (
        "duckdb.connect",
        "run_pipeline(",
        "bronze_extract(",
        "gold_load_staging(",
        "orchestrated_pipeline.main",
    ):
        assert token not in src
    assert "BashOperator" in src
    assert "do_xcom_push=False" in src


def test_dag_no_dataframe_xcom():
    src = DAG.read_text(encoding="utf-8")
    assert "do_xcom_push=False" in src
    assert "pd.DataFrame" not in src
    assert "pandas.DataFrame" not in src


def test_compose_airflow_yaml_contract():
    data = yaml.safe_load(AIRFLOW_COMPOSE.read_text(encoding="utf-8"))
    services = data["services"]
    assert "postgres" in services
    assert "airflow-init" in services
    assert "airflow-api-server" in services
    assert "airflow-scheduler" in services
    assert "airflow-dag-processor" in services
    assert "redis" not in services
    assert "airflow-worker" not in services
    common_env = data["x-airflow-common"]["environment"]
    assert common_env["AIRFLOW__CORE__EXECUTOR"] == "LocalExecutor"
    assert (
        common_env["AIRFLOW__CORE__EXECUTION_API_SERVER_URL"]
        == "http://airflow-api-server:8080/execution/"
    )
    assert "localhost" in str(common_env["AIRFLOW__API__BASE_URL"])
    assert "8081" in str(common_env["AIRFLOW__API__BASE_URL"])
    assert "postgresql+psycopg2" in str(common_env["AIRFLOW__DATABASE__SQL_ALCHEMY_CONN"])
    blob = yaml.dump(data).lower()
    assert "redis" not in blob
    assert "celery" not in blob


def test_root_compose_only_backend_frontend():
    data = yaml.safe_load(ROOT_COMPOSE.read_text(encoding="utf-8"))
    services = set(data.get("services", {}))
    assert services == {"backend", "frontend"}


def test_env_example_has_placeholders_not_real_secrets():
    text = ENV_EXAMPLE.read_text(encoding="utf-8")
    assert "replace-me" in text
    assert "calderon" not in text.lower()
    assert "sk-" not in text


def test_makefile_airflow_up_refuses_placeholders():
    text = MAKEFILE_INFRA.read_text(encoding="utf-8")
    assert "replace-me" in text
    assert "exit 1" in text
    assert "airflow-up:" in text


def test_dockerfile_pins_and_verifies_imports():
    text = DOCKERFILE.read_text(encoding="utf-8")
    req = AIRFLOW_REQ.read_text(encoding="utf-8")
    assert "apache/airflow:3.3.0-python3.12" in text
    assert "constraints-3.3.0/constraints-3.12.txt" in text
    assert "--constraint" in text
    assert "pip check" in text
    assert "from airflow.sdk import DAG" in text
    assert "airflow.providers.standard.operators.bash" in text
    assert "FabAuthManager" in text
    assert "apache-airflow-providers-standard==1.15.0" in req
    assert "apache-airflow-providers-fab==3.7.1" in req
    assert "duckdb==1.1.3" in req
    # Airflow image runtime matrix (constraints-3.3.0 / py3.12) — not backend requirements.
    assert "pandas==2.1.4" in req
    assert "pyarrow==24.0.0" in req
    assert "httpx==0.28.1" in req
    assert "python-dotenv==1.2.2" in req
    assert "pandas==2.2.2" not in req
    assert "pyarrow==16.1.0" not in req
    assert "httpx==0.27.0" not in req


def test_airflow_image_constraints_and_workflow_isolation_contract():
    docker = DOCKERFILE.read_text(encoding="utf-8")
    req = AIRFLOW_REQ.read_text(encoding="utf-8")
    wf = (ROOT / ".github" / "workflows" / "airflow-elt.yml").read_text(encoding="utf-8")
    # Airflow/Python stay pinned.
    assert "3.3.0-python3.12" in docker
    assert "apache-airflow==${AIRFLOW_VERSION}" in docker or 'apache-airflow=="${AIRFLOW_VERSION}"' in docker
    # Official constraints required for image install.
    assert (
        "https://raw.githubusercontent.com/apache/airflow/constraints-3.3.0/constraints-3.12.txt"
        in docker
    )
    assert "pip check" in docker
    # Approved Airflow-image runtime pins.
    for pin in (
        "apache-airflow-providers-standard==1.15.0",
        "apache-airflow-providers-fab==3.7.1",
        "duckdb==1.1.3",
        "pandas==2.1.4",
        "pyarrow==24.0.0",
        "httpx==0.28.1",
        "python-dotenv==1.2.2",
    ):
        assert pin in req
    # Workflow never mounts canonical checkout data/.
    assert "VOXMETRIKS_DATA_DIR: /tmp/voxmetriks-airflow-smoke-data" in wf
    assert "/tmp/voxmetriks-airflow-smoke-data" in wf
    assert "never the checkout data/" in wf or "smoke must not mount it" in wf
    assert "../../data" not in wf
    assert "./data" not in wf


def test_deterministic_ctl_run_id_integer(tmp_path, monkeypatch):
    env = _isolated_env(tmp_path)
    mod = _load_orch_module(env, "orch_ctl_hash", monkeypatch)
    a = mod.dag_run_id_to_ctl_run_id("manual__2026-08-09T00:00:00+00:00")
    b = mod.dag_run_id_to_ctl_run_id("manual__2026-08-09T00:00:00+00:00")
    c = mod.dag_run_id_to_ctl_run_id("other-run")
    assert a == b and a != c
    assert isinstance(a, int) and 0 < a < 2**31


def test_cli_preflight_ok_with_bronze(tmp_path):
    env = _isolated_env(tmp_path)
    _seed_bronze(env)
    proc = _run_orch("preflight", env, "cli-preflight")
    assert proc.returncode == 0, proc.stderr + proc.stdout


def test_cli_missing_bronze_extract_fails(tmp_path):
    env = _isolated_env(tmp_path)
    proc = _run_orch("extract_bronze", env, "cli-nobronze")
    assert proc.returncode != 0


def test_cli_missing_silver_load_fails(tmp_path):
    env = _isolated_env(tmp_path)
    _seed_bronze(env)
    proc = _run_orch("load_staging", env, "cli-nosilver")
    assert proc.returncode != 0
    assert "Silver" in (proc.stderr + proc.stdout)


def test_cli_empty_silver_fails(tmp_path):
    env = _isolated_env(tmp_path)
    data = Path(env["VOXMETRIKS_DATA_DIR"])
    pd.DataFrame().to_parquet(data / "silver" / "silver_spotify.parquet", index=False)
    proc = _run_orch("load_staging", env, "cli-emptysilver")
    assert proc.returncode != 0


def test_validate_false_nonzero_exit(tmp_path):
    env = _isolated_env(tmp_path)
    proc = _run_orch("validate_warehouse", env, "cli-validate-false")
    assert proc.returncode != 0


def test_finalize_blocked_when_prior_failed(tmp_path, monkeypatch):
    env = _isolated_env(tmp_path)
    mod = _load_orch_module(env, "orch_finalize_block", monkeypatch)
    dag_run_id = "finalize-block"
    ctl = mod.dag_run_id_to_ctl_run_id(dag_run_id)
    _ensure_ctl_schema(env["DB_PATH"])
    _insert_ctl(env["DB_PATH"], ctl, "extract_bronze", status="ERROR")
    proc = _run_orch("finalize_run", env, dag_run_id)
    assert proc.returncode != 0


@pytest.mark.parametrize("missing", REQUIRED_BEFORE_FINALIZE)
def test_finalize_rejects_missing_required_stage(tmp_path, missing, monkeypatch):
    env = _isolated_env(tmp_path)
    mod = _load_orch_module(env, f"orch_missing_{missing}", monkeypatch)
    dag_run_id = f"missing-{missing}"
    ctl = mod.dag_run_id_to_ctl_run_id(dag_run_id)
    _ensure_ctl_schema(env["DB_PATH"])
    for stage in REQUIRED_BEFORE_FINALIZE:
        if stage == missing:
            continue
        _insert_ctl(env["DB_PATH"], ctl, stage, status="OK")
    # Also seed raw_spotify so finalize does not fail for unrelated reasons.
    conn = duckdb.connect(env["DB_PATH"])
    conn.execute("CREATE TABLE IF NOT EXISTS raw_spotify (id INTEGER, track_id VARCHAR)")
    conn.execute("INSERT INTO raw_spotify VALUES (1, 'x')")
    conn.close()
    with pytest.raises(RuntimeError, match="missing required OK stages|Cannot finalize"):
        mod.stage_finalize_run(dag_run_id=dag_run_id, ctl_run_id=ctl)


def test_export_gold_strict_missing_tables_nonzero_and_no_ok_ctl(tmp_path, monkeypatch):
    env = _isolated_env(tmp_path)
    mod = _load_orch_module(env, "orch_export_fail", monkeypatch)
    dag_run_id = "export-fail"
    ctl = mod.dag_run_id_to_ctl_run_id(dag_run_id)
    # Empty warehouse — no gold tables.
    duckdb.connect(env["DB_PATH"]).close()
    with pytest.raises(Exception):
        mod.stage_export_gold(dag_run_id=dag_run_id, ctl_run_id=ctl)
    conn = duckdb.connect(env["DB_PATH"], read_only=True)
    try:
        n = conn.execute(
            """
            SELECT COUNT(*) FROM ctl_pipeline_stages
            WHERE run_id = ? AND stage = 'export_gold' AND status = 'OK'
            """,
            [ctl],
        ).fetchone()[0]
    except Exception:
        n = 0
    finally:
        conn.close()
    assert n == 0
    proc = _run_orch("export_gold", env, dag_run_id)
    assert proc.returncode != 0


def test_load_staging_rolls_back_when_ctl_record_fails(tmp_path, monkeypatch):
    env = _isolated_env(tmp_path)
    _seed_bronze(env)
    assert _run_orch("transform_silver", env, "rb-load-prep").returncode == 0
    mod = _load_orch_module(env, "orch_rb_load", monkeypatch)
    dag_run_id = "rb-load"
    ctl = mod.dag_run_id_to_ctl_run_id(dag_run_id)

    def boom(*_a, **_k):
        raise RuntimeError("injected ctl failure after load")

    monkeypatch.setattr(mod, "_record_stage_on_conn", boom)
    with pytest.raises(RuntimeError, match="injected ctl failure"):
        mod.stage_load_staging(dag_run_id=dag_run_id, ctl_run_id=ctl)

    conn = duckdb.connect(env["DB_PATH"], read_only=True)
    try:
        raw_n = conn.execute("SELECT COUNT(*) FROM raw_spotify").fetchone()[0]
    except Exception:
        raw_n = 0
    try:
        ctl_n = conn.execute(
            "SELECT COUNT(*) FROM ctl_pipeline_stages WHERE run_id = ? AND stage = 'load_staging'",
            [ctl],
        ).fetchone()[0]
    except Exception:
        ctl_n = 0
    conn.close()
    assert raw_n == 0
    assert ctl_n == 0


def test_build_gold_rolls_back_when_ctl_record_fails(tmp_path, monkeypatch):
    env = _isolated_env(tmp_path)
    _seed_bronze(env)
    assert _run_orch("transform_silver", env, "rb-build-prep").returncode == 0
    assert _run_orch("load_staging", env, "rb-build-prep").returncode == 0
    mod = _load_orch_module(env, "orch_rb_build", monkeypatch)
    dag_run_id = "rb-build"
    ctl = mod.dag_run_id_to_ctl_run_id(dag_run_id)

    before = duckdb.connect(env["DB_PATH"], read_only=True)
    before_fact = 0
    try:
        before_fact = before.execute("SELECT COUNT(*) FROM fact_streaming").fetchone()[0]
    except Exception:
        before_fact = 0
    before.close()

    def boom(*_a, **_k):
        raise RuntimeError("injected ctl failure after build")

    monkeypatch.setattr(mod, "_record_stage_on_conn", boom)
    with pytest.raises(RuntimeError, match="injected ctl failure"):
        mod.stage_build_gold_and_aggregates(dag_run_id=dag_run_id, ctl_run_id=ctl)

    after = duckdb.connect(env["DB_PATH"], read_only=True)
    try:
        after_fact = after.execute("SELECT COUNT(*) FROM fact_streaming").fetchone()[0]
    except Exception:
        after_fact = 0
    try:
        ctl_n = after.execute(
            "SELECT COUNT(*) FROM ctl_pipeline_stages WHERE run_id = ? AND stage = 'build_gold_and_aggregates'",
            [ctl],
        ).fetchone()[0]
    except Exception:
        ctl_n = 0
    after.close()
    assert after_fact == before_fact
    assert ctl_n == 0


def test_finalize_rolls_back_when_audit_fails(tmp_path, monkeypatch):
    env = _isolated_env(tmp_path)
    mod = _load_orch_module(env, "orch_rb_finalize", monkeypatch)
    dag_run_id = "rb-finalize"
    ctl = mod.dag_run_id_to_ctl_run_id(dag_run_id)
    _ensure_ctl_schema(env["DB_PATH"])
    for stage in REQUIRED_BEFORE_FINALIZE:
        _insert_ctl(env["DB_PATH"], ctl, stage, status="OK")
    conn = duckdb.connect(env["DB_PATH"])
    conn.execute(
        "CREATE TABLE IF NOT EXISTS raw_spotify (id INTEGER, track_id VARCHAR, track_name VARCHAR)"
    )
    conn.execute("INSERT INTO raw_spotify VALUES (1, 'x', 'y')")
    conn.close()

    def boom_audit(*_a, **_k):
        raise RuntimeError("injected audit failure")

    monkeypatch.setattr(mod.elt, "_audit", boom_audit)
    with pytest.raises(RuntimeError, match="injected audit failure"):
        mod.stage_finalize_run(dag_run_id=dag_run_id, ctl_run_id=ctl)

    conn = duckdb.connect(env["DB_PATH"], read_only=True)
    loads = conn.execute("SELECT COUNT(*) FROM ctl_carga_dataset").fetchone()[0]
    finals = conn.execute(
        "SELECT COUNT(*) FROM ctl_pipeline_stages WHERE run_id = ? AND stage = 'finalize_run'",
        [ctl],
    ).fetchone()[0]
    conn.close()
    assert loads == 0
    assert finals == 0


def test_ctl_pipeline_stages_records_dag_run_id(tmp_path):
    env = _isolated_env(tmp_path)
    _seed_bronze(env)
    dag_run_id = "ctl-details-run"
    proc = _run_orch("extract_bronze", env, dag_run_id)
    assert proc.returncode == 0, proc.stderr + proc.stdout
    conn = duckdb.connect(env["DB_PATH"], read_only=True)
    rows = conn.execute(
        "SELECT details, run_id FROM ctl_pipeline_stages WHERE stage = 'extract_bronze'"
    ).fetchall()
    conn.close()
    assert rows
    assert any(dag_run_id in (r[0] or "") for r in rows)


def test_full_eight_stage_cli_on_temp_data(tmp_path):
    env = _isolated_env(tmp_path)
    # Never touch canonical warehouse.
    assert "voxmetriks\\data\\warehouse" not in env["DB_PATH"].lower().replace("/", "\\")
    assert Path(env["DB_PATH"]).resolve() != (ROOT / "data" / "warehouse" / "voxmetrik.duckdb").resolve()
    _seed_bronze(env)
    dag_run_id = "full-eight-stages"
    for stage in STAGES:
        proc = _run_orch(stage, env, dag_run_id)
        assert proc.returncode == 0, f"{stage} failed: {proc.stderr}\n{proc.stdout}"

    db = Path(env["DB_PATH"])
    assert db.exists()
    conn = duckdb.connect(str(db), read_only=True)
    assert conn.execute("SELECT COUNT(*) FROM fact_streaming").fetchone()[0] > 0
    stages = {
        r[0]
        for r in conn.execute(
            "SELECT DISTINCT stage FROM ctl_pipeline_stages WHERE status = 'OK'"
        ).fetchall()
    }
    for required in REQUIRED_BEFORE_FINALIZE + ["finalize_run"]:
        assert required in stages
    assert conn.execute(
        "SELECT COUNT(*) FROM ctl_pipeline_stages WHERE stage = 'finalize_run' AND status = 'OK'"
    ).fetchone()[0] >= 1
    conn.close()

    gold = Path(env["VOXMETRIKS_DATA_DIR"]) / "gold"
    expected = [
        "dim_track.parquet",
        "fact_streaming.parquet",
        "agg_daily_streams.parquet",
    ]
    for name in expected:
        path = gold / name
        assert path.exists() and path.stat().st_size > 0
        pd.read_parquet(path)


def test_traditional_run_pipeline_entrypoint_exists():
    src = ELT.read_text(encoding="utf-8")
    assert "def run_pipeline()" in src
    assert 'if __name__ == "__main__"' in src
    assert "strict: bool = False" in src


def test_airflow_not_in_backend_requirements():
    req = (ROOT / "apps" / "backend" / "requirements.txt").read_text(encoding="utf-8").lower()
    assert "apache-airflow" not in req


def test_orchestrated_pipeline_no_app_table_writes():
    src = ORCH.read_text(encoding="utf-8")
    assert not re.search(r"(INSERT|UPDATE|DELETE|DROP)\s+.*\bapp_", src, re.I)


def test_idempotent_transform_silver_rewrites_parquet(tmp_path):
    env = _isolated_env(tmp_path)
    _seed_bronze(env)
    p1 = _run_orch("transform_silver", env, "idem-1")
    assert p1.returncode == 0, p1.stderr + p1.stdout
    silver = Path(env["VOXMETRIKS_DATA_DIR"]) / "silver" / "silver_spotify.parquet"
    assert silver.exists()
    mtime1 = silver.stat().st_mtime
    p2 = _run_orch("transform_silver", env, "idem-2")
    assert p2.returncode == 0, p2.stderr + p2.stdout
    assert silver.exists()
    assert silver.stat().st_mtime >= mtime1


def test_required_stages_constant_matches_contract(tmp_path, monkeypatch):
    env = _isolated_env(tmp_path)
    mod = _load_orch_module(env, "orch_required_const", monkeypatch)
    assert list(mod.REQUIRED_STAGES_BEFORE_FINALIZE) == REQUIRED_BEFORE_FINALIZE


def test_finalize_second_call_is_idempotent(tmp_path, monkeypatch):
    env = _isolated_env(tmp_path)
    mod = _load_orch_module(env, "orch_finalize_idem", monkeypatch)
    dag_run_id = "finalize-idem"
    ctl = mod.dag_run_id_to_ctl_run_id(dag_run_id)
    _ensure_ctl_schema(env["DB_PATH"])
    for stage in REQUIRED_BEFORE_FINALIZE:
        _insert_ctl(env["DB_PATH"], ctl, stage, status="OK")
    conn = duckdb.connect(env["DB_PATH"])
    conn.execute(
        "CREATE TABLE IF NOT EXISTS raw_spotify (id INTEGER, track_id VARCHAR, track_name VARCHAR)"
    )
    conn.execute("INSERT INTO raw_spotify VALUES (1, 'x', 'y')")
    conn.close()

    first = mod.stage_finalize_run(dag_run_id=dag_run_id, ctl_run_id=ctl)
    assert first["status"] == "OK"
    assert first.get("already_finalized") is False

    conn = duckdb.connect(env["DB_PATH"], read_only=True)
    loads_1 = conn.execute("SELECT COUNT(*) FROM ctl_carga_dataset").fetchone()[0]
    audits_1 = conn.execute("SELECT COUNT(*) FROM ctl_auditoria").fetchone()[0]
    finals_1 = conn.execute(
        "SELECT COUNT(*) FROM ctl_pipeline_stages WHERE run_id = ? AND stage = 'finalize_run' AND status = 'OK'",
        [ctl],
    ).fetchone()[0]
    conn.close()
    assert loads_1 == 1 and audits_1 == 1 and finals_1 == 1

    second = mod.stage_finalize_run(dag_run_id=dag_run_id, ctl_run_id=ctl)
    assert second["status"] == "OK"
    assert second.get("already_finalized") is True

    conn = duckdb.connect(env["DB_PATH"], read_only=True)
    loads_2 = conn.execute("SELECT COUNT(*) FROM ctl_carga_dataset").fetchone()[0]
    audits_2 = conn.execute("SELECT COUNT(*) FROM ctl_auditoria").fetchone()[0]
    finals_2 = conn.execute(
        "SELECT COUNT(*) FROM ctl_pipeline_stages WHERE run_id = ? AND stage = 'finalize_run' AND status = 'OK'",
        [ctl],
    ).fetchone()[0]
    conn.close()
    assert loads_2 == loads_1
    assert audits_2 == audits_1
    assert finals_2 == finals_1


def test_finalize_rejects_unknown_ok_stage_contamination(tmp_path, monkeypatch):
    env = _isolated_env(tmp_path)
    mod = _load_orch_module(env, "orch_finalize_unknown", monkeypatch)
    dag_run_id = "finalize-unknown"
    ctl = mod.dag_run_id_to_ctl_run_id(dag_run_id)
    _ensure_ctl_schema(env["DB_PATH"])
    for stage in REQUIRED_BEFORE_FINALIZE:
        _insert_ctl(env["DB_PATH"], ctl, stage, status="OK")
    _insert_ctl(env["DB_PATH"], ctl, "rogue_extra_stage", status="OK")
    conn = duckdb.connect(env["DB_PATH"])
    conn.execute("CREATE TABLE IF NOT EXISTS raw_spotify (id INTEGER, track_id VARCHAR)")
    conn.execute("INSERT INTO raw_spotify VALUES (1, 'x')")
    conn.close()
    with pytest.raises(RuntimeError, match="unknown OK stages contaminate"):
        mod.stage_finalize_run(dag_run_id=dag_run_id, ctl_run_id=ctl)


def test_finalize_rejects_post_finalize_contamination_or_error(tmp_path, monkeypatch):
    env = _isolated_env(tmp_path)
    mod = _load_orch_module(env, "orch_finalize_post_contam", monkeypatch)
    dag_run_id = "finalize-post-contam"
    ctl = mod.dag_run_id_to_ctl_run_id(dag_run_id)
    _ensure_ctl_schema(env["DB_PATH"])
    for stage in REQUIRED_BEFORE_FINALIZE:
        _insert_ctl(env["DB_PATH"], ctl, stage, status="OK")
    conn = duckdb.connect(env["DB_PATH"])
    conn.execute(
        "CREATE TABLE IF NOT EXISTS raw_spotify (id INTEGER, track_id VARCHAR, track_name VARCHAR)"
    )
    conn.execute("INSERT INTO raw_spotify VALUES (1, 'x', 'y')")
    conn.close()

    first = mod.stage_finalize_run(dag_run_id=dag_run_id, ctl_run_id=ctl)
    assert first["status"] == "OK" and first.get("already_finalized") is False

    _insert_ctl(env["DB_PATH"], ctl, "rogue_after_finalize", status="OK")
    with pytest.raises(RuntimeError, match="unknown OK stages contaminate"):
        mod.stage_finalize_run(dag_run_id=dag_run_id, ctl_run_id=ctl)

    # Clean the rogue row, then inject ERROR on a required stage — still reject.
    conn = duckdb.connect(env["DB_PATH"])
    conn.execute(
        "DELETE FROM ctl_pipeline_stages WHERE run_id = ? AND stage = 'rogue_after_finalize'",
        [ctl],
    )
    conn.execute(
        """
        UPDATE ctl_pipeline_stages
        SET status = 'ERROR'
        WHERE run_id = ? AND stage = 'validate_warehouse'
        """,
        [ctl],
    )
    conn.close()
    with pytest.raises(RuntimeError, match="non-OK stages"):
        mod.stage_finalize_run(dag_run_id=dag_run_id, ctl_run_id=ctl)


def test_workflow_reproducible_host_and_dag_wait_contract():
    text = (ROOT / ".github" / "workflows" / "airflow-elt.yml").read_text(encoding="utf-8")
    assert "actions/setup-python@v5" in text
    assert 'python-version: "3.12"' in text
    assert "duckdb==1.1.3" in text
    assert "pandas==2.2.2" in text
    assert "pyarrow==16.1.0" in text
    assert "chown -R 50000:0" in text
    assert "Wait until voxmetriks_elt is listed" in text
    assert "list-import-errors --output json" in text
    assert "assert_import_errors_json.py" in text
    assert "if: always()" in text
    assert "down -v" in text
    # Must not install Airflow on the GitHub runner host.
    assert "pip install apache-airflow" not in text
    assert "apache-airflow==" not in text.split("Install host smoke dependencies")[1].split("Prepare isolated")[0]


def test_assert_import_errors_json_handles_null_with_extra_empty_payload(tmp_path):
    """Literal CI failure: JSONDecodeError Extra data at char 4 (e.g. null[])."""
    import importlib.util

    script = ROOT / "infrastructure" / "airflow" / "assert_import_errors_json.py"
    spec = importlib.util.spec_from_file_location("assert_import_errors_json", script)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)

    assert mod.parse_import_errors_payload("[]") == []
    assert mod.parse_import_errors_payload("null") == []
    assert mod.parse_import_errors_payload("null[]") == []
    assert mod.parse_import_errors_payload("[]\nnull\n") == []
    with pytest.raises(ValueError, match="empty"):
        mod.parse_import_errors_payload("   ")
    rows = mod.parse_import_errors_payload('[{"filename": "x.py"}]')
    assert rows == [{"filename": "x.py"}]
    assert mod.main([str(tmp_path / "missing")]) == 2
    bad = tmp_path / "errs.json"
    bad.write_text('[{"filename": "broken.py"}]', encoding="utf-8")
    assert mod.main([str(bad)]) == 1
    good = tmp_path / "ok.json"
    good.write_text("null[]", encoding="utf-8")
    assert mod.main([str(good)]) == 0
