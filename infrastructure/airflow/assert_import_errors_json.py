#!/usr/bin/env python3
"""Assert Airflow `dags list-import-errors --output json` reports zero errors.

Handles Airflow/CLI wrappers that emit `null` and/or trailing empty JSON values
(json.loads raises JSONDecodeError: Extra data at char 4 for payloads like `null[]`).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def parse_import_errors_payload(raw: str) -> list[Any]:
    if not raw.strip():
        raise ValueError("import-errors JSON file is empty; refusing to treat as zero errors")

    cleaned = raw.lstrip("\ufeff").strip()
    decoder = json.JSONDecoder()
    try:
        data, end = decoder.raw_decode(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"import-errors JSON parse failed: {exc}; raw={raw[:500]!r}") from exc

    values = [data]
    cursor = end
    while True:
        remainder = cleaned[cursor:].lstrip()
        if not remainder:
            break
        skipped = len(cleaned[cursor:]) - len(remainder)
        try:
            nxt, consumed = decoder.raw_decode(remainder)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"import-errors JSON trailing garbage: {exc}; "
                f"trailing={remainder[:200]!r}; raw={raw[:500]!r}"
            ) from exc
        values.append(nxt)
        cursor += skipped + consumed

    # Normalize / validate each top-level value; only empty payloads allowed.
    errors: list[Any] = []
    for value in values:
        if value is None:
            continue
        if isinstance(value, list):
            if value:
                errors.extend(value)
            continue
        if isinstance(value, dict):
            candidates = [
                value.get(k)
                for k in ("import_errors", "dags", "data", "items")
                if k in value
            ]
            seq = next((c for c in candidates if isinstance(c, list)), None)
            if seq is None:
                raise ValueError(f"Unexpected import-errors JSON object: {value!r}")
            if seq:
                errors.extend(seq)
            continue
        raise ValueError(f"Unexpected import-errors JSON type: {type(value).__name__}: {value!r}")

    return errors


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print("usage: assert_import_errors_json.py <path>", file=sys.stderr)
        return 2
    path = Path(args[0])
    if not path.is_file():
        print(f"import-errors JSON file not found: {path}", file=sys.stderr)
        return 2
    raw = path.read_text(encoding="utf-8")
    try:
        errors = parse_import_errors_payload(raw)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if errors:
        print(f"DAG import errors present ({len(errors)}): {errors!r}", file=sys.stderr)
        return 1
    print("import_errors_json_ok count=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
