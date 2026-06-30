#!/usr/bin/env python3
"""Patch Angular templates to pass lang() into the pure translate pipe."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "frontend" / "src" / "app"

PIPE_WITH_PARAMS = re.compile(
    r"\|\s*t\s*:\s*(\{[^}]+\}(?:\s*\|\s*number)?)\s*\}\}"
)
PIPE_PLAIN = re.compile(r"\|\s*t\s*\}\}")


def patch_text(text: str) -> str:
    if "| t" not in text:
        return text
    text = PIPE_WITH_PARAMS.sub(r"| t: \1:lang() }}", text)
    text = PIPE_PLAIN.sub("| t:lang() }}", text)
    return text


def ensure_lang_in_ts(ts_path: Path, text: str) -> str:
    if "| t" not in text and "TranslatePipe" not in text:
        return text
    if "readonly lang = inject(I18nService).lang" in text or "lang = inject(I18nService).lang" in text:
        return text
    if "export class" not in text:
        return text

    if "I18nService" not in text:
        if "inject(I18nService)" in text or "private i18n = inject(I18nService)" in text:
            text = text.replace(
                "private i18n = inject(I18nService);",
                "private i18n = inject(I18nService);\n  readonly lang = this.i18n.lang;",
            )
            if "readonly lang = this.i18n.lang" not in text:
                text = text.replace(
                    "inject(I18nService);",
                    "inject(I18nService);\n  readonly lang = inject(I18nService).lang;",
                    1,
                )
        else:
            text = text.replace(
                "import { Component",
                "import { I18nService } from '../../core/services/i18n.service';\nimport { Component",
                1,
            )
            # fix relative depth later - skip broken imports
    # insert lang field after first inject block in class
    if "readonly lang =" not in text:
        m = re.search(r"(export class \w+[^{]+\{)", text)
        if m:
            insert_at = m.end()
            text = (
                text[:insert_at]
                + "\n  readonly lang = inject(I18nService).lang;"
                + text[insert_at:]
            )
    if "I18nService" in text and "import { I18nService" not in text:
        # try common import paths
        for imp in (
            "import { I18nService } from '../../../core/services/i18n.service';",
            "import { I18nService } from '../../core/services/i18n.service';",
            "import { I18nService } from '../../../../core/services/i18n.service';",
        ):
            if imp.split("'")[1] in str(ts_path).replace("\\", "/"):
                pass
        depth = ts_path.relative_to(ROOT).parts
        ups = len(depth) - 1
        rel = "../" * ups + "core/services/i18n.service"
        imp_line = f"import {{ I18nService }} from '{rel}';"
        if imp_line not in text:
            text = text.replace("import { Component", imp_line + "\nimport { Component", 1)
    if "inject" in text and "import { inject" not in text and "import { Component, inject" not in text:
        text = re.sub(
            r"import \{ Component",
            "import { Component, inject",
            text,
            count=1,
        )
    return text


def main() -> None:
    for path in list(ROOT.rglob("*.html")) + list(ROOT.rglob("*.ts")):
        raw = path.read_text(encoding="utf-8")
        patched = patch_text(raw)
        if path.suffix == ".ts" and "template:" in patched:
            patched = ensure_lang_in_ts(path, patched)
        elif path.suffix == ".html":
            ts = path.with_suffix(".ts")
            if ts.exists():
                ts_text = ensure_lang_in_ts(ts, ts.read_text(encoding="utf-8"))
                if ts_text != ts.read_text(encoding="utf-8"):
                    ts.write_text(ts_text, encoding="utf-8")
        if patched != raw:
            path.write_text(patched, encoding="utf-8")
            print("patched", path.relative_to(ROOT.parent.parent))


if __name__ == "__main__":
    main()
