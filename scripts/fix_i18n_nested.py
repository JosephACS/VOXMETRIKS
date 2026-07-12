#!/usr/bin/env python3
"""Fix invalid nested {{ }} replacements inside Angular expressions."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path("apps/frontend/src/app/packages")

# || '{{ 'key' | t:lang() }}'  →  || ('key' | t:lang())
# ? '{{ 'key' | t:lang() }}'   →  ? ('key' | t:lang())
# : '{{ 'key' | t:lang() }}'   →  : ('key' | t:lang())
# ?? '{{ 'key' | t:lang() }}'  →  ?? ('key' | t:lang())
PAT = re.compile(
    r"( \|\|| \?\?| \?| :) '\{\{ '([^']+)' \| t:lang\(\) \}\}'"
)


def fix_text(text: str) -> str:
    def repl(m: re.Match[str]) -> str:
        op = m.group(1)
        key = m.group(2)
        return f"{op} ('{key}' | t:lang())"

    return PAT.sub(repl, text)


def main() -> None:
    n = 0
    for path in ROOT.rglob("*.ts"):
        original = path.read_text(encoding="utf-8")
        updated = fix_text(original)
        # org-create: submitting() ? 'Creando…' : ('organizations.create.title' | t:lang())
        # leave as-is after regex; also fix remaining broken academic dashboard string
        updated = updated.replace(
            "|| ('customerSuccess.dashboard.title' | t:lang()) academic dashboard'",
            "|| ('customerSuccess.dashboard.title' | t:lang())",
        )
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            n += 1
            print(path)
    print(f"fixed {n} files")


if __name__ == "__main__":
    main()
