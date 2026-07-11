from __future__ import annotations

from typing import Any, Callable

from app.utils.response_wrapper import success_response


def dispatch_service(service_call: Callable[[], dict]) -> dict[str, Any]:
    """Execute service layer; exceptions handled by global FastAPI handlers."""
    payload = service_call()
    message = payload.get("insight", "OK") if isinstance(payload, dict) else "OK"
    return success_response(payload, message)
