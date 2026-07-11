from __future__ import annotations

from typing import Any, Literal

StatusType = Literal["success", "error"]


def success_response(data: Any, message: str = "OK") -> dict[str, Any]:
    return {
        "status": "success",
        "data": data,
        "message": message,
    }


def error_response(message: str, data: Any = None) -> dict[str, Any]:
    return {
        "status": "error",
        "data": data,
        "message": message,
    }


def structured_error(
    message: str,
    *,
    code: str,
    details: dict[str, Any] | None = None,
    request_id: str | None = None,
    data: Any = None,
) -> dict[str, Any]:
    return {
        "status": "error",
        "message": message,
        "data": data,
        "error": {
            "code": code,
            "details": details or {},
            "request_id": request_id,
        },
    }
