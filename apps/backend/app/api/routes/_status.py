from __future__ import annotations

from typing import Any


def module_status(name: str) -> dict[str, Any]:
    return {"status": "success", "module": name}
