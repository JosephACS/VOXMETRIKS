"""Strip sensitive fields before optional external LLM calls."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

_SENSITIVE = frozenset({
    "password", "token", "authorization", "email", "smtp_password",
    "secret", "api_key", "session", "refresh_token",
})


def sanitize_ai_context(data: Dict[str, Any]) -> Dict[str, Any]:
    return _scrub(deepcopy(data))


def _scrub(obj: Any) -> Any:
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k.lower() in _SENSITIVE:
                continue
            if k.lower() == "username":
                out[k] = str(v)[:3] + "***" if v else v
                continue
            out[k] = _scrub(v)
        return out
    if isinstance(obj, list):
        return [_scrub(x) for x in obj[:20]]
    return obj
