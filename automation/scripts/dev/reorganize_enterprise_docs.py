#!/usr/bin/env python3
"""
One-shot enterprise documentation reorganization.
Moves docs only — does not modify application code.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DOCS = ROOT / "docs"

# flat docs/*.md → numbered section (lowercase kebab filenames)
DOC_MOVES: dict[str, str] = {
    "QUICKSTART.md": "01-introduction/quickstart.md",
    "FAQ.md": "01-introduction/faq.md",
    "CONTRIBUTING.md": "01-introduction/contributing.md",
    "WINDOWS_SETUP.md": "01-introduction/windows-setup.md",
    "ARCHITECTURE.md": "02-architecture/architecture.md",
    "STRUCTURE.md": "02-architecture/structure.md",
    "DATABASE.md": "03-database/database.md",
    "BACKEND.md": "04-backend/backend.md",
    "FRONTEND.md": "05-frontend/frontend.md",
    "ETL.md": "06-elt/elt.md",
    "API.md": "07-api/api.md",
    "TESTING.md": "08-testing/testing.md",
    "DEPLOYMENT.md": "09-deployment/deployment.md",
    "SECURITY.md": "10-security/security.md",
    "PERFORMANCE.md": "11-performance/performance.md",
    "AUDIT_REPORT.md": "12-audit/audit-report.md",
    "V2-DELIVERY-CLOSURE.md": "12-audit/v2-delivery-closure.md",
    "PRESENTATION_GUIDE.md": "13-presentation/presentation-guide.md",
    "ROADMAP.md": "14-roadmap/roadmap.md",
    "PORTFOLIO.md": "15-portfolio/portfolio.md",
}

UML_MOVES: dict[str, str] = {
    "01-use-cases.puml": "use-cases/01-use-cases.puml",
    "02-components.puml": "components/02-components.puml",
    "02-components-detailed.puml": "components/02-components-detailed.puml",
    "02a-components-frontend.puml": "components/02a-components-frontend.puml",
    "02b-components-backend-datos.puml": "components/02b-components-backend-datos.puml",
    "03-architecture.puml": "architecture/03-architecture.puml",
    "03-architecture-detailed.puml": "architecture/03-architecture-detailed.puml",
    "04-elt-flow.puml": "elt/04-elt-flow.puml",
    "05-classes-core.puml": "classes/05-classes-core.puml",
    "06-classes-warehouse.puml": "classes/06-classes-warehouse.puml",
    "07-seq-login.puml": "sequence/07-seq-login.puml",
    "08-seq-play.puml": "sequence/08-seq-play.puml",
    "09-seq-recommendations.puml": "sequence/09-seq-recommendations.puml",
    "10-packages.puml": "context/10-packages.puml",
}

SCREENSHOT_DIRS = [
    "frontend",
    "backend",
    "dashboard",
    "elt",
    "database",
    "api",
]


def move_doc_files() -> list[tuple[str, str]]:
    moved: list[tuple[str, str]] = []
    for src_name, dest_rel in DOC_MOVES.items():
        src = DOCS / src_name
        dest = DOCS / dest_rel
        if not src.exists():
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
        moved.append((f"docs/{src_name}", f"docs/{dest_rel}"))
    return moved


def move_uml_files() -> list[tuple[str, str]]:
    moved: list[tuple[str, str]] = []
    uml = DOCS / "uml"
    pkg_src = uml / "packages"
    pkg_dest = uml / "use-cases" / "packages"
    if pkg_src.exists():
        pkg_dest.mkdir(parents=True, exist_ok=True)
        for f in pkg_src.glob("*.puml"):
            target = pkg_dest / f.name
            shutil.move(str(f), str(target))
            moved.append((f"docs/uml/packages/{f.name}", f"docs/uml/use-cases/packages/{f.name}"))
        if not any(pkg_src.iterdir()):
            pkg_src.rmdir()

    for src_name, dest_rel in UML_MOVES.items():
        src = uml / src_name
        dest = uml / dest_rel
        if not src.exists():
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
        moved.append((f"docs/uml/{src_name}", f"docs/uml/{dest_rel}"))

    rendered = uml / "_rendered"
    if rendered.exists():
        for png in list(rendered.glob("*.png")):
            stem = png.stem
            sub = None
            if stem.startswith("uc-"):
                sub = "use-cases"
            elif stem.startswith(("07-seq", "08-seq", "09-seq")):
                sub = "sequence"
            elif stem.startswith(("05-classes", "06-classes")):
                sub = "classes"
            if sub:
                target_dir = rendered / sub
                target_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(png), str(target_dir / png.name))
                moved.append((f"docs/uml/_rendered/{png.name}", f"docs/uml/_rendered/{sub}/{png.name}"))
    return moved


def create_screenshot_dirs() -> list[str]:
    created: list[str] = []
    base = DOCS / "screenshots"
    for name in SCREENSHOT_DIRS:
        d = base / name
        d.mkdir(parents=True, exist_ok=True)
        created.append(f"docs/screenshots/{name}/")
    return created


def build_link_replacements() -> list[tuple[str, str]]:
    reps: list[tuple[str, str]] = []
    for old_name, dest_rel in DOC_MOVES.items():
        old_lower = old_name.lower()
        new_path = f"docs/{dest_rel}"
        reps.extend([
            (f"docs/{old_name}", new_path),
            (f"docs/{old_lower}", new_path),
            (old_name, dest_rel.split("/")[-1]),
        ])
    # ETL → ELT naming in documentation paths only
    reps.extend([
        ("ETL.md", "elt.md"),
        ("docs/ETL.md", "docs/06-elt/elt.md"),
        ("[ETL]", "[ELT]"),
        ("# ETL", "# ELT"),
        ("## ETL", "## ELT"),
        ("Pipeline ETL", "Pipeline ELT"),
        ("Pipeline Medallion ETL", "Pipeline Medallion ELT"),
    ])
    # UML path updates
    for src_name, dest_rel in UML_MOVES.items():
        reps.append((f"docs/uml/{src_name}", f"docs/uml/{dest_rel}"))
        reps.append((f"uml/{src_name}", f"uml/{dest_rel}"))
    reps.append(("docs/uml/packages/", "docs/uml/use-cases/packages/"))
    reps.append(("uml/packages/", "uml/use-cases/packages/"))
    reps.append(("docs/uml/*.puml", "docs/uml/**/*.puml"))
    return reps


def update_markdown_links() -> int:
    reps = build_link_replacements()
    # longest first to avoid partial replacements
    reps.sort(key=lambda x: len(x[0]), reverse=True)
    updated = 0
    for path in ROOT.rglob("*"):
        if path.suffix.lower() not in {".md", ".mdc"}:
            continue
        if "node_modules" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        original = text
        for old, new in reps:
            text = text.replace(old, new)
        # Fix relative links between docs that used sibling filenames
        for old_name, dest_rel in DOC_MOVES.items():
            base = old_name.replace(".md", "")
            new_file = dest_rel.split("/")[-1]
            text = re.sub(
                rf"\]\(({re.escape(base)}|{re.escape(old_name)})\)",
                f"]({new_file})",
                text,
                flags=re.IGNORECASE,
            )
        if text != original:
            path.write_text(text, encoding="utf-8")
            updated += 1
    return updated


def main() -> None:
    moved_docs = move_doc_files()
    moved_uml = move_uml_files()
    created = create_screenshot_dirs()
    updated_files = update_markdown_links()
    print("MOVED_DOCS", len(moved_docs))
    for a, b in moved_docs:
        print(f"  {a} -> {b}")
    print("MOVED_UML", len(moved_uml))
    for a, b in moved_uml:
        print(f"  {a} -> {b}")
    print("SCREENSHOT_DIRS", len(created))
    print("UPDATED_MD_FILES", updated_files)


if __name__ == "__main__":
    main()
