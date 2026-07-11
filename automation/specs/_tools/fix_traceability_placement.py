#!/usr/bin/env python3
"""Fix traceability block placement: must follow Trazabilidad Empresarial, precede Actores."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BLOCK_START = "## Matriz CU → HU → FR → CA"
BLOCK_END_MARKERS = ("## Actores", "## Casos de Uso")


def fix_spec(path: Path):
    text = path.read_text(encoding="utf-8")
    if BLOCK_START not in text:
        return
    # Extract matrix block (from BLOCK_START through granular matrix table)
    m = re.search(
        rf"({re.escape(BLOCK_START)}.*?)(\n\*Nota:|\n## Actores|\n## Casos de Uso)",
        text,
        flags=re.DOTALL,
    )
    if not m:
        return
    block = m.group(1).strip()
    text_wo = text[: m.start()] + text[m.start(2) :]

    # Remove duplicate block if still present elsewhere
    text_wo = re.sub(re.escape(block) + r"\s*", "", text_wo, count=1)

    # Insert after Trazabilidad eslabón table (before ## Actores)
    text_wo = re.sub(
        r"(## Trazabilidad Empresarial.*?)(\n## Actores)",
        r"\1\n\n" + block + r"\2",
        text_wo,
        count=1,
        flags=re.DOTALL,
    )
    path.write_text(text_wo, encoding="utf-8")
    print(f"Fixed placement: {path}")


if __name__ == "__main__":
    for spec in ROOT.glob("*/spec.md"):
        if spec.parent.name.startswith(("0", "TRACE")):
            fix_spec(spec)
