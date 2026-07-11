"""
VOXMETRIK_V2 - Logging Configuration
Professional, structured logging for production and development.
"""
import logging
import logging.config
from typing import Optional

from app.core.config import get_settings

settings = get_settings()

# ── Format strings ────────────────────────────────────────────────────────────
_CONSOLE_FORMAT = "[%(asctime)s] [%(levelname)-8s] %(name)s — %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ── Logging config dict ───────────────────────────────────────────────────────
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": _CONSOLE_FORMAT,
            "datefmt": _DATE_FORMAT,
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": settings.log_level,
            "formatter": "console",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "voxmetrik": {
            "level": "DEBUG",
            "handlers": ["console"],
            "propagate": False,
        },
        "uvicorn": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "uvicorn.error": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "uvicorn.access": {
            "level": "WARNING",
            "handlers": ["console"],
            "propagate": False,
        },
        "fastapi": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
    },
    "root": {
        "level": settings.log_level,
        "handlers": ["console"],
    },
}


def setup_logging() -> None:
    """Apply logging configuration. Call once at application startup."""
    logging.config.dictConfig(LOGGING_CONFIG)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Return a logger under the 'voxmetrik' namespace.

    Usage:
        logger = get_logger(__name__)
    """
    if name:
        return logging.getLogger(f"voxmetrik.{name}")
    return logging.getLogger("voxmetrik")
