#!/usr/bin/env python3
"""Compare enterprise ES/EN keys."""
import re
from pathlib import Path

root = Path("apps/frontend/src/app/core/i18n/locales")


def keys(p: Path) -> set[str]:
    return set(re.findall(r"'([^']+)':", p.read_text(encoding="utf-8")))


es = keys(root / "enterprise.es.ts")
en = keys(root / "enterprise.en.ts")
only_es = sorted(es - en)
only_en = sorted(en - es)
print(f"enterprise es={len(es)} en={len(en)}")
print(f"only_es={len(only_es)}")
for k in only_es:
    print("  ES", k)
print(f"only_en={len(only_en)}")
for k in only_en:
    print("  EN", k)
