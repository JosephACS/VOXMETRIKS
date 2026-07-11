from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from app.core.config import get_settings


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        for key in ("request_id", "method", "path", "status", "elapsed_ms", "user", "sql_label"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload, ensure_ascii=False, default=str)


def _build_formatter(settings) -> logging.Formatter:
    if settings.log_json:
        return StructuredFormatter()
    return logging.Formatter(
        "[%(asctime)s] [%(levelname)-8s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def _add_rotating_handler(
    logger: logging.Logger,
    path: Path,
    *,
    level: int,
    formatter: logging.Formatter,
    max_bytes: int,
    backup_count: int,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    handler.setLevel(level)
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def setup_logging() -> None:
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)

    formatter = _build_formatter(settings)

    stdout = logging.StreamHandler(sys.stdout)
    stdout.setFormatter(formatter)
    root.addHandler(stdout)

    if settings.log_to_files:
        log_dir = settings.log_dir_resolved
        _add_rotating_handler(
            logging.getLogger("voxmetrik.api"),
            log_dir / settings.log_file_api,
            level=level,
            formatter=formatter,
            max_bytes=settings.log_max_bytes,
            backup_count=settings.log_backup_count,
        )
        _add_rotating_handler(
            logging.getLogger("voxmetrik.errors"),
            log_dir / settings.log_file_errors,
            level=logging.WARNING,
            formatter=formatter,
            max_bytes=settings.log_max_bytes,
            backup_count=settings.log_backup_count,
        )
        _add_rotating_handler(
            logging.getLogger("voxmetrik.database"),
            log_dir / settings.log_file_database,
            level=logging.DEBUG,
            formatter=formatter,
            max_bytes=settings.log_max_bytes,
            backup_count=settings.log_backup_count,
        )

    for noisy in ("httpx", "httpcore", "uvicorn.access"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
