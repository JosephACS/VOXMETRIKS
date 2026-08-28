# -*- coding: utf-8 -*-
"""DEPRECATED: use run_backend.py."""

from __future__ import annotations

import sys
from pathlib import Path

print(
    "DEPRECATED: run_demo_backend.py -> use run_backend.py",
    file=sys.stderr,
)

_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from run_backend import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
