# -*- coding: utf-8 -*-
"""Local demo Uvicorn runner with file-based graceful shutdown.

Watches ``scripts/.demo-pids/backend.shutdown.request`` (repo-relative) and sets
``server.should_exit`` so FastAPI lifespan shutdown (and DuckDB close/checkpoint)
can complete. No HTTP shutdown endpoint. Does not print secrets.
"""

from __future__ import annotations

import os
import sys
import threading
import time
from pathlib import Path

import uvicorn

_SHUTDOWN_REQUEST_NAME = "backend.shutdown.request"
_POLL_SEC = 0.25


def _backend_dir() -> Path:
    return Path(__file__).resolve().parents[1]


def _repo_root() -> Path:
    # apps/backend/scripts/this.py → parents[3] = repo root
    return Path(__file__).resolve().parents[3]


def shutdown_request_path() -> Path:
    return _repo_root() / "scripts" / ".demo-pids" / _SHUTDOWN_REQUEST_NAME


def _watch_shutdown_request(server: uvicorn.Server, path: Path) -> None:
    while not server.should_exit:
        try:
            if path.is_file():
                server.should_exit = True
                return
        except OSError:
            pass
        time.sleep(_POLL_SEC)


def main() -> int:
    backend = _backend_dir()
    os.chdir(backend)
    backend_s = str(backend)
    if backend_s not in sys.path:
        sys.path.insert(0, backend_s)

    config = uvicorn.Config(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        log_level="info",
    )
    server = uvicorn.Server(config)

    watcher = threading.Thread(
        target=_watch_shutdown_request,
        args=(server, shutdown_request_path()),
        name="demo-shutdown-watch",
        daemon=True,
    )
    watcher.start()
    # Blocks until should_exit; lifespan shutdown runs before return.
    server.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
