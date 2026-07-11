#!/usr/bin/env python3
"""
Enterprise monorepo restructure — physical moves + config/path reference updates.
Does NOT alter business logic in services, routes, or Angular components.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path


def _repo_root() -> Path:
    start = Path(__file__).resolve()
    for candidate in [start, *start.parents]:
        if (candidate / "README.md").exists() and (candidate / "data").is_dir():
            return candidate
    return start.parents[2]


ROOT = _repo_root()

# ── Physical moves: (src relative to ROOT, dest relative to ROOT) ─────────────
DIR_MOVES: list[tuple[str, str]] = [
    ("backend", "apps/backend"),
    ("frontend", "apps/frontend"),
    ("elt", "analytics/elt"),
    ("scripts", "automation/scripts"),
    ("e2e", "automation/e2e"),
    ("specs", "automation/specs"),
    ("pocketbase", "infrastructure/pocketbase"),
    (".githooks", "infrastructure/hooks"),
]

FILE_MOVES: list[tuple[str, str]] = [
    ("Dockerfile", "infrastructure/docker/Dockerfile"),
    ("docker-compose.yml", "infrastructure/docker/docker-compose.yml"),
    (".dockerignore", "infrastructure/docker/.dockerignore"),
    (".env.example", "infrastructure/environments/.env.example"),
    ("package.json", "automation/playwright/package.json"),
    ("package-lock.json", "automation/playwright/package-lock.json"),
    ("playwright.config.ts", "automation/playwright/playwright.config.ts"),
    ("Makefile", "infrastructure/Makefile"),
]

# Docs: numbered → category layout
DOC_MOVES: dict[str, str] = {
    "docs/01-introduction/quickstart.md": "docs/quickstart.md",
    "docs/01-introduction/faq.md": "docs/faq.md",
    "docs/01-introduction/contributing.md": "docs/contributing.md",
    "docs/01-introduction/windows-setup.md": "docs/deployment/windows-setup.md",
    "docs/02-architecture/architecture.md": "docs/architecture/architecture.md",
    "docs/02-architecture/structure.md": "docs/architecture/structure.md",
    "docs/03-database/database.md": "docs/database/database.md",
    "docs/04-backend/backend.md": "docs/backend/backend.md",
    "docs/05-frontend/frontend.md": "docs/frontend/frontend.md",
    "docs/06-elt/elt.md": "docs/architecture/elt.md",
    "docs/07-api/api.md": "docs/api/api.md",
    "docs/08-testing/testing.md": "docs/testing/testing.md",
    "docs/09-deployment/deployment.md": "docs/deployment/deployment.md",
    "docs/10-security/security.md": "docs/security/security.md",
    "docs/11-performance/performance.md": "docs/performance/performance.md",
    "docs/12-audit/audit-report.md": "docs/archive/audit-report.md",
    "docs/12-audit/v2-delivery-closure.md": "docs/archive/v2-delivery-closure.md",
    "docs/12-audit/enterprise-reorganization.md": "docs/archive/enterprise-reorganization.md",
    "docs/13-presentation/presentation-guide.md": "docs/presentation/presentation-guide.md",
    "docs/14-roadmap/roadmap.md": "docs/roadmap/roadmap.md",
    "docs/15-portfolio/portfolio.md": "docs/portfolio/portfolio.md",
}

# Text replacements (order: longest patterns first when applied)
TEXT_REPLACEMENTS: list[tuple[str, str]] = [
    # Apps
    ("cd backend &&", "cd apps/backend &&"),
    ("cd backend\n", "cd apps/backend\n"),
    ("cd frontend &&", "cd apps/frontend &&"),
    ("cd frontend\n", "cd apps/frontend\n"),
    ("--prefix backend", "--prefix apps/backend"),
    ("--prefix frontend", "--prefix apps/frontend"),
    ("cwd: 'backend'", "cwd: '../../apps/backend'"),
    ("cwd: 'frontend'", "cwd: '../../apps/frontend'"),
    ("./frontend", "./apps/frontend"),
    ("context: ./frontend", "context: ./apps/frontend"),
    ("COPY backend/", "COPY apps/backend/"),
    ("COPY backend\\", "COPY apps/backend\\"),
    ("COPY frontend/", "COPY apps/frontend/"),
    ("WORKDIR /app/backend", "WORKDIR /app/backend"),
    ("PYTHONPATH: /app/backend:/app", "PYTHONPATH: /app/backend:/app"),
    ("PYTHONPATH: /app:/app/backend", "PYTHONPATH: /app:/app/backend"),
    ("npm --prefix backend", "npm --prefix apps/backend"),
    ("npm start --prefix frontend", "npm start --prefix apps/frontend"),
    ("pip install -r apps/backend/requirements.txt", "pip install -r apps/backend/requirements.txt"),
    ("apps/apps/backend", "apps/backend"),
    # Host paths only — Docker container keeps /app/backend and /app/elt internally
    ("COPY apps/backend/requirements.txt", "COPY apps/backend/requirements.txt"),
    ("COPY apps/backend/ ./backend/", "COPY apps/backend/ ./backend/"),
    ("COPY analytics/elt/ ./elt/", "COPY analytics/elt/ ./elt/"),
    ("backend/tests/", "apps/backend/tests/"),
    ("backend/.env", "apps/backend/.env"),
    ("backend/.env.e2e.example", "apps/backend/.env.e2e.example"),
    ("backend/README.md", "apps/backend/README.md"),
    ("backend/app/", "apps/backend/app/"),
    ("backend\\requirements.txt", "apps/backend\\requirements.txt"),
    ("backend\\", "apps/backend\\"),
    ("../backend/", "../apps/backend/"),
    ("../../backend/", "../../apps/backend/"),
    ("`backend/`", "`apps/backend/`"),
    ("`frontend/`", "`apps/frontend/`"),
    # Analytics / ELT
    ("python elt/pipelines", "python analytics/elt/pipelines"),
    ("python analytics/elt/pipelines/elt_pipeline.py", "python analytics/elt/pipelines/elt_pipeline.py"),
    ("COPY elt/", "COPY analytics/elt/"),
    ("../analytics/elt/", "../analytics/elt/"),
    ("`analytics/elt/`", "`analytics/elt/`"),
    ("analytics/elt/pipelines/", "analytics/elt/pipelines/"),
    # Automation
    ("./e2e/", "./automation/e2e/"),
    ("'./e2e/", "'../e2e/"),
    ("testDir: './e2e/tests'", "testDir: '../e2e/tests'"),
    ("globalSetup: './e2e/global-setup.ts'", "globalSetup: '../e2e/global-setup.ts'"),
    ("from './e2e/fixtures", "from '../e2e/fixtures"),
    ("python scripts/", "python automation/scripts/"),
    ("python automation/scripts/", "python automation/scripts/"),
    ("`scripts/`", "`automation/scripts/`"),
    ("../scripts/", "../automation/scripts/"),
    ("../../scripts/", "../../automation/scripts/"),
    ("specs/_tools", "automation/specs/_tools"),
    ("specs/_archive", "automation/specs/_archive"),
    ("specs/TRACEABILITY", "automation/specs/TRACEABILITY"),
    ("specs/DELIVERY", "automation/specs/DELIVERY"),
    ("specs/README", "automation/specs/README"),
    ("../specs/", "../automation/specs/"),
    ("../../specs/", "../../automation/specs/"),
    ('"feature_directory": "automation/specs/', '"feature_directory": "automation/specs/'),
    ("specs/01", "automation/specs/01"),
    ("specs/0", "automation/specs/0"),
    ("specs/1", "automation/specs/1"),
    ("e2e/.auth/", "automation/e2e/.auth/"),
    # Infrastructure
    ("./pocketbase/", "./infrastructure/pocketbase/"),
    ("pocketbase/pb_data", "infrastructure/pocketbase/pb_data"),
    ("pocketbase/pb_migrations", "infrastructure/pocketbase/pb_migrations"),
    ("docker compose up", "docker compose -f infrastructure/docker/docker-compose.yml up"),
    ("docker compose down", "docker compose -f infrastructure/docker/docker-compose.yml down"),
    ("docker compose logs", "docker compose -f infrastructure/docker/docker-compose.yml logs"),
    ("docker-compose.yml", "infrastructure/docker/docker-compose.yml"),
    # Docs paths (numbered → category)
    ("docs/01-introduction/quickstart.md", "docs/quickstart.md"),
    ("docs/02-architecture/structure.md", "docs/architecture/structure.md"),
    ("docs/02-architecture/architecture.md", "docs/architecture/architecture.md"),
    ("docs/03-database/database.md", "docs/database/database.md"),
    ("docs/04-backend/backend.md", "docs/backend/backend.md"),
    ("docs/05-frontend/frontend.md", "docs/frontend/frontend.md"),
    ("docs/06-elt/elt.md", "docs/architecture/elt.md"),
    ("docs/07-api/api.md", "docs/api/api.md"),
    ("docs/08-testing/testing.md", "docs/testing/testing.md"),
    ("docs/09-deployment/deployment.md", "docs/deployment/deployment.md"),
    ("docs/10-security/security.md", "docs/security/security.md"),
    ("docs/11-performance/performance.md", "docs/performance/performance.md"),
    ("docs/12-audit/", "docs/archive/"),
    ("docs/13-presentation/presentation-guide.md", "docs/presentation/presentation-guide.md"),
    ("docs/14-roadmap/roadmap.md", "docs/roadmap/roadmap.md"),
    ("docs/15-portfolio/portfolio.md", "docs/portfolio/portfolio.md"),
    # Playwright reports → archive
    ("playwright-report/", "archive/generated/playwright-report/"),
    ("test-results/", "archive/generated/test-results/"),
]

SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".angular", "dist", "archive/generated",
    "apps", "analytics", "automation", "infrastructure",
}


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def move_if_exists(src_rel: str, dest_rel: str, log: list) -> None:
    src, dest = ROOT / src_rel, ROOT / dest_rel
    if not src.exists():
        return
    if dest.exists():
        # Already migrated — drop empty leftover source dir
        if src.is_dir() and not any(src.iterdir()):
            try:
                src.rmdir()
            except OSError:
                pass
        return
    ensure_parent(dest)
    shutil.move(str(src), str(dest))
    log.append((src_rel, dest_rel))


def remove_empty_numbered_doc_dirs() -> None:
    for i in range(1, 16):
        prefix = f"{i:02d}-"
        for d in (ROOT / "docs").glob(f"{prefix}*"):
            if d.is_dir():
                try:
                    d.rmdir()
                except OSError:
                    pass


def apply_text_replacements() -> int:
    count = 0
    reps = sorted(TEXT_REPLACEMENTS, key=lambda x: len(x[0]), reverse=True)
    docker_files = {
        "infrastructure/docker/docker-compose.yml",
        "infrastructure/docker/Dockerfile",
    }
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT).as_posix()
        if rel in docker_files:
            continue
        if any(s in path.parts for s in SKIP_DIRS):
            continue
        if path.suffix.lower() not in {
            ".md", ".mdc", ".py", ".ts", ".json", ".yml", ".yaml", ".bat",
            ".sh", ".ps1", ".toml", ".html", ".css", ".env", ".example",
        } and path.name not in {"Makefile", "Dockerfile", ".dockerignore"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue
        original = text
        for old, new in reps:
            text = text.replace(old, new)
        if text != original:
            path.write_text(text, encoding="utf-8")
            count += 1
    return count


def fix_config_py() -> None:
    cfg = ROOT / "apps/backend/app/core/config.py"
    if not cfg.exists():
        return
    text = cfg.read_text(encoding="utf-8")
    old_block = '''# Load .env from backend/ first, then project root
_HERE = Path(__file__).resolve().parent          # backend/app/core/
_BACKEND = _HERE.parent.parent                   # backend/
_PROJECT_ROOT = _BACKEND.parent                  # VOXMETRIK_V2/

# Load backend/.env first, then project root (root wins on duplicate keys)
if (_BACKEND / ".env").exists():
    load_dotenv(dotenv_path=str(_BACKEND / ".env"), override=False)
if (_PROJECT_ROOT / ".env").exists():
    load_dotenv(dotenv_path=str(_PROJECT_ROOT / ".env"), override=True)

_ENV_FILES = tuple(
    str(p)
    for p in (_BACKEND / ".env", _PROJECT_ROOT / ".env")
    if p.exists()
)'''
    new_block = '''# Load .env from apps/backend first, then repo root / infrastructure/environments
_HERE = Path(__file__).resolve().parent          # apps/backend/app/core/
_BACKEND = _HERE.parent.parent                   # apps/backend/


def _find_project_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "data" / "warehouse").is_dir():
            return candidate
        if (candidate / "apps" / "apps" / "backend").is_dir() and (candidate / "data").is_dir():
            return candidate
    return start.parent.parent


_PROJECT_ROOT = _find_project_root(_BACKEND)

_env_candidates = [
    _BACKEND / ".env",
    _PROJECT_ROOT / ".env",
    _PROJECT_ROOT / "infrastructure" / "environments" / ".env",
]
for _env_path in _env_candidates:
    if _env_path.exists():
        load_dotenv(dotenv_path=str(_env_path), override=False)
if (_PROJECT_ROOT / ".env").exists():
    load_dotenv(dotenv_path=str(_PROJECT_ROOT / ".env"), override=True)

_ENV_FILES = tuple(str(p) for p in _env_candidates if p.exists())'''
    if old_block in text:
        cfg.write_text(text.replace(old_block, new_block), encoding="utf-8")


def fix_paths_py() -> None:
    p = ROOT / "apps/backend/app/packages/analytics/services/paths.py"
    if not p.exists():
        return
    p.write_text(
        '''"""Medallion layer paths for warehouse status."""

from pathlib import Path

from app.core.config import get_settings


def _project_root() -> Path:
    return get_settings().data_root.parent


PROJECT_ROOT = _project_root()
BRONZE_PARQUET = PROJECT_ROOT / "data" / "bronze" / "raw_spotify.parquet"
SILVER_PARQUET = PROJECT_ROOT / "data" / "silver" / "silver_spotify.parquet"
GOLD_DIR = PROJECT_ROOT / "data" / "gold"
''',
        encoding="utf-8",
    )


def fix_elt_project_roots() -> None:
    """Update parent[N] depth for analytics/elt modules."""
    fixes = [
        (
            ROOT / "analytics/elt/pipelines/elt_pipeline.py",
            "_PROJECT_ROOT = Path(__file__).resolve().parents[2]",
            "_PROJECT_ROOT = Path(__file__).resolve().parents[3]",
        ),
        (
            ROOT / "analytics/elt/load/load_duckdb.py",
            "ROOT = Path(__file__).resolve().parents[2]",
            "ROOT = Path(__file__).resolve().parents[3]",
        ),
        (
            ROOT / "analytics/elt/extract/download_dataset.py",
            "ROOT = Path(__file__).resolve().parents[2]",
            "ROOT = Path(__file__).resolve().parents[3]",
        ),
        (
            ROOT / "analytics/elt/transform/csv_to_parquet.py",
            "ROOT = Path(__file__).resolve().parents[2]",
            "ROOT = Path(__file__).resolve().parents[3]",
        ),
    ]
    for path, old, new in fixes:
        if path.exists():
            t = path.read_text(encoding="utf-8")
            if old in t:
                path.write_text(t.replace(old, new), encoding="utf-8")


def fix_script_roots() -> None:
    for py in (ROOT / "automation/scripts").rglob("*.py"):
        t = py.read_text(encoding="utf-8")
        orig = t
        t = t.replace('parents[2]', 'parents[3]') if "reorganize" in py.name else t
        t = re.sub(
            r'ROOT = Path\(__file__\)\.resolve\(\)\.parent\.parent\b',
            'ROOT = Path(__file__).resolve().parents[2]',
            t,
        )
        t = re.sub(
            r'ROOT = Path\(__file__\)\.resolve\(\)\.parents\[1\]',
            'ROOT = Path(__file__).resolve().parents[2]',
            t,
        )
        t = t.replace(' / "apps" / "backend"', ' / "apps" / "apps" / "backend"')
        t = t.replace('sys.path.insert(0, str(ROOT / "apps" / "backend"))', 'sys.path.insert(0, str(ROOT / "apps" / "apps" / "backend"))')
        t = t.replace('sys.path.insert(0, str(ROOT))\n', 'sys.path.insert(0, str(ROOT))\nsys.path.insert(0, str(ROOT / "analytics"))\n')
        if t != orig:
            py.write_text(t, encoding="utf-8")


def fix_synthetic_dimensions() -> None:
    p = ROOT / "apps/backend/app/packages/analytics/services/synthetic/dimensions.py"
    if not p.exists():
        return
    t = p.read_text(encoding="utf-8")
    t = t.replace("parents[6]", "parents[7]")
    p.write_text(t, encoding="utf-8")


def fix_pipeline_service() -> None:
    p = ROOT / "apps/backend/app/packages/analytics/services/pipeline_service.py"
    if not p.exists():
        return
    t = p.read_text(encoding="utf-8")
    t = t.replace("parents[5]", "parents[6]")
    p.write_text(t, encoding="utf-8")


def fix_test_warehouse_path() -> None:
    p = ROOT / "apps/backend/tests/test_enterprise_api.py"
    if not p.exists():
        return
    t = p.read_text(encoding="utf-8")
    t = t.replace("parents[2]", "parents[3]")
    p.write_text(t, encoding="utf-8")


def write_root_makefile() -> None:
    (ROOT / "Makefile").write_text(
        """# Voxmetriks — root Makefile (delegates to infrastructure/)
.PHONY: help up down logs etl dev test install pipeline lint

help:
\t@$(MAKE) -f infrastructure/Makefile help

up down logs etl dev test install pipeline lint:
\t@$(MAKE) -f infrastructure/Makefile $@
""",
        encoding="utf-8",
    )


def write_root_package_json() -> None:
    (ROOT / "package.json").write_text(
        """{
  "name": "voxmetriks",
  "private": true,
  "scripts": {
    "e2e": "npm --prefix automation/playwright run e2e",
    "e2e:ui": "npm --prefix automation/playwright run e2e:ui",
    "e2e:install": "npm --prefix automation/playwright run e2e:install",
    "e2e:backend": "npm --prefix automation/playwright run e2e:backend",
    "e2e:frontend": "npm --prefix automation/playwright run e2e:frontend"
  }
}
""",
        encoding="utf-8",
    )


def update_playwright_config() -> None:
    p = ROOT / "automation/playwright/playwright.config.ts"
    if not p.exists():
        return
    t = p.read_text(encoding="utf-8")
    t = t.replace(
        "reporter: [['list'], ['html', { open: 'never' }]],",
        "reporter: [['list'], ['html', { open: 'never', outputFolder: '../../archive/generated/playwright-report' }]],",
    )
    t = t.replace(
        "video: 'retain-on-failure',",
        "video: 'retain-on-failure',\n    outputDir: '../../archive/generated/test-results',",
    )
    p.write_text(t, encoding="utf-8")


def update_gitignore() -> None:
    p = ROOT / ".gitignore"
    t = p.read_text(encoding="utf-8")
    replacements = [
        ("frontend/dist/", "apps/frontend/dist/"),
        ("frontend/.angular/", "apps/frontend/.angular/"),
        ("backend/tests/.pytest_db/", "apps/backend/tests/.pytest_db/"),
        ("e2e/.auth/", "automation/e2e/.auth/"),
        ("playwright-report/", "archive/generated/playwright-report/"),
        ("test-results/", "archive/generated/test-results/"),
    ]
    for old, new in replacements:
        if old in t and new not in t:
            t = t.replace(old, new)
    if "archive/generated/" not in t:
        t += "\n# Generated artifacts (enterprise layout)\narchive/generated/\n"
    p.write_text(t, encoding="utf-8")


def update_docker_compose() -> None:
    p = ROOT / "infrastructure/docker/docker-compose.yml"
    if not p.exists():
        return
    t = p.read_text(encoding="utf-8")
    t = t.replace("context: .", "context: ../..")
    t = t.replace("dockerfile: Dockerfile", "dockerfile: infrastructure/docker/Dockerfile")
    t = t.replace("./data:", "../../data:")
    t = t.replace("./.env:", "../../.env:")
    t = t.replace("./infrastructure/pocketbase/", "../../infrastructure/pocketbase/")
    t = t.replace("context: ./apps/frontend", "context: ../../apps/frontend")
    t = t.replace(
        "command: python analytics/elt/pipelines/elt_pipeline.py",
        "command: python analytics/elt/pipelines/elt_pipeline.py",
    )
  # PYTHONPATH for container
    t = t.replace(
        "PYTHONPATH: /app/apps/backend:/app/analytics:/app",
        "PYTHONPATH: /app/apps/backend:/app/analytics:/app",
    )
    p.write_text(t, encoding="utf-8")


def update_dockerfile() -> None:
    p = ROOT / "infrastructure/docker/Dockerfile"
    if not p.exists():
        return
    t = p.read_text(encoding="utf-8")
    t = t.replace("COPY backend/requirements.txt", "COPY apps/backend/requirements.txt")
    t = t.replace(
        "COPY --chown=voxmetrik:voxmetrik backend/ ./backend/",
        "COPY --chown=voxmetrik:voxmetrik apps/backend/ ./backend/",
    )
    t = t.replace(
        "COPY --chown=voxmetrik:voxmetrik elt/     ./elt/",
        "COPY --chown=voxmetrik:voxmetrik analytics/elt/ ./elt/",
    )
    t = t.replace(
        "COPY --chown=voxmetrik:voxmetrik .env.example .",
        "COPY --chown=voxmetrik:voxmetrik infrastructure/environments/.env.example .env.example",
    )
    p.write_text(t, encoding="utf-8")


def update_infrastructure_makefile() -> None:
    p = ROOT / "infrastructure/Makefile"
    if not p.exists():
        return
    root_var = "ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/..)\nexport PYTHONPATH := $(ROOT)/apps/backend:$(ROOT):$(ROOT)/analytics\n\n"
    t = p.read_text(encoding="utf-8")
    if "ROOT :=" not in t:
        t = root_var + t
    t = t.replace("cd apps/backend &&", "cd $(ROOT)/apps/backend &&")
    t = t.replace("cd backend &&", "cd $(ROOT)/apps/backend &&")
    t = t.replace(
        "python analytics/elt/pipelines/elt_pipeline.py",
        "cd $(ROOT) && python analytics/elt/pipelines/elt_pipeline.py",
    )
    t = t.replace(
        "python elt/pipelines/elt_pipeline.py",
        "cd $(ROOT) && python analytics/elt/pipelines/elt_pipeline.py",
    )
    t = t.replace(
        "docker compose -f infrastructure/docker/docker-compose.yml up",
        "docker compose -f $(ROOT)/infrastructure/docker/docker-compose.yml --project-directory $(ROOT) up",
    )
    t = t.replace(
        "docker compose -f infrastructure/docker/docker-compose.yml down",
        "docker compose -f $(ROOT)/infrastructure/docker/docker-compose.yml --project-directory $(ROOT) down",
    )
    t = t.replace(
        "docker compose -f infrastructure/docker/docker-compose.yml logs",
        "docker compose -f $(ROOT)/infrastructure/docker/docker-compose.yml --project-directory $(ROOT) logs",
    )
    p.write_text(t, encoding="utf-8")


def update_specify_feature_json() -> None:
    p = ROOT / ".specify/feature.json"
    if p.exists():
        t = p.read_text(encoding="utf-8").replace('"specs/', '"automation/specs/')
        p.write_text(t, encoding="utf-8")


def update_cursor_rules() -> None:
    p = ROOT / ".cursor/rules/specify-rules.mdc"
    if p.exists():
        t = p.read_text(encoding="utf-8").replace("specs/", "automation/specs/")
        p.write_text(t, encoding="utf-8")


def move_generated_artifacts() -> None:
    gen = ROOT / "archive/generated"
    gen.mkdir(parents=True, exist_ok=True)
    for name in ("playwright-report", "test-results"):
        src = ROOT / name
        if src.exists():
            dest = gen / name
            if dest.exists():
                shutil.rmtree(dest)
            shutil.move(str(src), str(dest))


def write_docs_readme() -> None:
    (ROOT / "docs/README.md").write_text(
        """# Voxmetriks — Documentación

| Sección | Enlace |
|---------|--------|
| Arranque | [quickstart.md](quickstart.md) |
| FAQ | [faq.md](faq.md) |
| Contribuir | [contributing.md](contributing.md) |
| Arquitectura | [architecture/](architecture/) |
| Backend | [backend/](backend/) |
| Frontend | [frontend/](frontend/) |
| Base de datos | [database/](database/) |
| API | [api/](api/) |
| ELT | [architecture/elt.md](architecture/elt.md) |
| Tests | [testing/](testing/) |
| Despliegue | [deployment/](deployment/) |
| Seguridad | [security/](security/) |
| Rendimiento | [performance/](performance/) |
| Presentación | [presentation/](presentation/) |
| Roadmap | [roadmap/](roadmap/) |
| Portafolio | [portfolio/](portfolio/) |
| UML | [uml/](uml/) |
| Screenshots | [screenshots/](screenshots/) |
| Archivo | [archive/](archive/) |
| Specs SDD | [automation/specs/](../automation/specs/README.md) |
""",
        encoding="utf-8",
    )


def write_migration_report(moved: list, docs_moved: list, text_files: int) -> None:
    report = ROOT / "docs/archive/enterprise-monorepo-migration.md"
    lines = [
        "# Migración Enterprise Monorepo",
        "",
        "## Árbol objetivo",
        "",
        "```",
        "voxmetriks/",
        "├── apps/{backend,frontend}/",
        "├── analytics/elt/",
        "├── automation/{scripts,e2e,specs,playwright}/",
        "├── infrastructure/{docker,pocketbase,hooks,environments}/",
        "├── docs/{architecture,backend,...}/",
        "├── data/",
        "├── archive/{generated}/",
        "├── Makefile          # delega a infrastructure/",
        "├── package.json      # delega e2e a automation/playwright/",
        "└── README.md",
        "```",
        "",
        f"## Directorios movidos ({len(moved)})",
        "",
    ]
    for a, b in moved:
        lines.append(f"- `{a}` → `{b}`")
    lines.extend(["", f"## Documentos movidos ({len(docs_moved)})", ""])
    for a, b in docs_moved:
        lines.append(f"- `{a}` → `{b}`")
    lines.extend([
        "",
        f"## Archivos con rutas actualizadas: {text_files}",
        "",
        "## Cambios de path en código (solo resolución de rutas)",
        "- `apps/backend/app/core/config.py` — detección dinámica de repo root",
        "- `apps/backend/app/packages/analytics/services/paths.py` — usa `get_settings().data_root`",
        "- `analytics/elt/*` — depth `parents[3]` para repo root",
        "- `automation/scripts/*` — ROOT depth + PYTHONPATH analytics",
        "",
        "**Lógica de negocio, APIs e imports de dominio: sin cambios.**",
    ])
    report.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    moved: list[tuple[str, str]] = []
    for src, dest in DIR_MOVES:
        move_if_exists(src, dest, moved)
    for src, dest in FILE_MOVES:
        move_if_exists(src, dest, moved)

    docs_log: list[tuple[str, str]] = []
    for src, dest in DOC_MOVES.items():
        move_if_exists(src, dest, docs_log)

    remove_empty_numbered_doc_dirs()
    move_generated_artifacts()

    fix_config_py()
    fix_paths_py()
    fix_elt_project_roots()
    fix_script_roots()
    fix_synthetic_dimensions()
    fix_pipeline_service()
    fix_test_warehouse_path()

    text_count = apply_text_replacements()
    update_docker_compose()
    update_dockerfile()
    update_infrastructure_makefile()
    update_gitignore()
    update_playwright_config()
    update_specify_feature_json()
    update_cursor_rules()
    write_root_makefile()
    write_root_package_json()
    write_docs_readme()
    write_migration_report(moved, docs_log, text_count)

    print("MOVED_DIRS", len(moved))
    print("MOVED_DOCS", len(docs_log))
    print("TEXT_FILES_UPDATED", text_count)


if __name__ == "__main__":
    main()
