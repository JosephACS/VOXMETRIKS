from __future__ import annotations

import functools
import time
from typing import Any, Callable, TypeVar

from app.core.logging import get_logger

logger = get_logger(__name__)
F = TypeVar("F", bound=Callable[..., Any])


def timed(label: str | None = None) -> Callable[[F], F]:
    """Log execution time for service/ETL callables."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            name = label or func.__qualname__
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
                logger.debug("timed name=%s elapsed_ms=%s", name, elapsed_ms)

        return wrapper  # type: ignore[misc]

    return decorator
