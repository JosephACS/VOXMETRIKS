#!/usr/bin/env python3
"""Remove StatusLabelPipe / LocaleMoneyPipe / LocaleDatePipe when unused in template."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path("apps/frontend/src/app/packages")
PIPES = [
    ("StatusLabelPipe", "statusLabel"),
    ("LocaleMoneyPipe", "localeMoney"),
    ("LocaleDatePipe", "localeDate"),
]


def process(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    m = re.search(r"template:\s*`(.*?)`\s*,", text, re.S)
    tpl = m.group(1) if m else ""
    original = text

    for pipe, needle in PIPES:
        if pipe not in text:
            continue
        if needle in tpl:
            continue
        # remove from imports array
        text = re.sub(rf",\s*{pipe}\b", "", text)
        text = re.sub(rf"\b{pipe}\s*,\s*", "", text)
        # remove import lines that only import this pipe (or trim from multi-import)
        text = re.sub(
            rf"^import \{{\s*{pipe}\s*\}} from .+?;\s*\n",
            "",
            text,
            flags=re.M,
        )
        # LocaleDatePipe, LocaleMoneyPipe shared import
        text = re.sub(
            r"import \{\s*LocaleDatePipe,\s*LocaleMoneyPipe\s*\} from ([^\n]+)\n",
            lambda mm: (
                ""
                if "LocaleMoneyPipe" not in text[text.find("imports:") : text.find("imports:") + 400]
                and "LocaleDatePipe" not in text[text.find("imports:") : text.find("imports:") + 400]
                else mm.group(0)
            ),
            text,
            count=1,
        )

    # Clean shared locale-format import if neither pipe remains in imports array
    imports_block = re.search(r"imports:\s*\[([^\]]*)\]", text)
    if imports_block:
        block = imports_block.group(1)
        if "LocaleMoneyPipe" not in block and "LocaleDatePipe" not in block:
            text = re.sub(
                r"^import \{\s*LocaleDatePipe,\s*LocaleMoneyPipe\s*\} from .+?;\s*\n",
                "",
                text,
                flags=re.M,
            )
            text = re.sub(
                r"^import \{\s*LocaleMoneyPipe,\s*LocaleDatePipe\s*\} from .+?;\s*\n",
                "",
                text,
                flags=re.M,
            )
        elif "LocaleMoneyPipe" not in block and "LocaleDatePipe" in block:
            text = re.sub(
                r"import \{\s*LocaleDatePipe,\s*LocaleMoneyPipe\s*\}",
                "import { LocaleDatePipe }",
                text,
            )
            text = re.sub(
                r"import \{\s*LocaleMoneyPipe,\s*LocaleDatePipe\s*\}",
                "import { LocaleDatePipe }",
                text,
            )
        elif "LocaleDatePipe" not in block and "LocaleMoneyPipe" in block:
            text = re.sub(
                r"import \{\s*LocaleDatePipe,\s*LocaleMoneyPipe\s*\}",
                "import { LocaleMoneyPipe }",
                text,
            )
            text = re.sub(
                r"import \{\s*LocaleMoneyPipe,\s*LocaleDatePipe\s*\}",
                "import { LocaleMoneyPipe }",
                text,
            )

    if "StatusLabelPipe" not in (imports_block.group(1) if imports_block else ""):
        # re-check after edits
        ib = re.search(r"imports:\s*\[([^\]]*)\]", text)
        if ib and "StatusLabelPipe" not in ib.group(1):
            text = re.sub(
                r"^import \{\s*StatusLabelPipe\s*\} from .+?;\s*\n",
                "",
                text,
                flags=re.M,
            )

    # tidy double commas / spaces in imports
    text = re.sub(r"imports:\s*\[([^\]]*)\]", lambda m: "imports: [" + re.sub(r",\s*,", ", ", m.group(1)).replace(" ,", ",") + "]", text, count=1)

    if text != original:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main() -> None:
    n = 0
    for path in sorted(ROOT.rglob("*.ts")):
        if path.name.endswith(".spec.ts"):
            continue
        if process(path):
            n += 1
            print(path)
    print(f"cleaned {n} files")


if __name__ == "__main__":
    main()
