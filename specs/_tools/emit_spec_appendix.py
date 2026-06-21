#!/usr/bin/env python3
"""Emit per-spec traceability appendix (CU→HU→FR→CA) for insertion into spec.md files."""
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("gen", ROOT / "_tools" / "generate_traceability.py")
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def appendix(spec_id: str) -> str:
    seen = set()
    rows = []
    for r in gen.ROWS:
        if r["spec"] != spec_id:
            continue
        key = (r["cu"], r["hu"], r["fr"], r["ca"])
        if key in seen:
            continue
        seen.add(key)
        rows.append(r)
    lines = [
        "## Matriz CU → HU → FR → CA",
        "",
        "Subconjunto de [`TRACEABILITY-MASTER.md`](../TRACEABILITY-MASTER.md) (Constitución §12).",
        "",
        "| CU | HU | FR | CA |",
        "|----|----|----|-----|",
    ]
    for r in rows:
        lines.append(f"| {r['cu']} | {r['hu']} | {r['fr']} | {r['ca']} |")
    lines.append("")
    return "\n".join(lines)


def granular_matrix(spec_id: str) -> str:
    seen = set()
    lines = [
        "### Matriz de trazabilidad (granular)",
        "",
        "| OE | OT | OO | Meta | Dept | Paquete | CU | HU | Spec | Impl |",
        "|----|----|----|------|------|---------|----|----|------|------|",
    ]
    for r in gen.ROWS:
        if r["spec"] != spec_id:
            continue
        key = (r["oe"], r["ot"], r["oo"], r["meta"], r["cu"], r["hu"])
        if key in seen:
            continue
        seen.add(key)
        lines.append(
            f"| {r['oe']} | {r['ot']} | {r['oo']} | {r['meta']} | {r['dept']} | {r['pkg']} | {r['cu']} | {r['hu']} | {spec_id} | Pendiente |"
        )
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    for sid in ["001", "002", "003", "004", "005", "006"]:
        dirs = list(ROOT.glob(f"{sid}-*"))
        if not dirs:
            continue
        d = dirs[0]
        (d / "traceability-appendix.md").write_text(
            appendix(sid) + "\n" + granular_matrix(sid),
            encoding="utf-8",
        )
        print(f"Wrote {d / 'traceability-appendix.md'}")
