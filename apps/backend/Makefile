# ============================================================
# VOXMETRIKS_V2 - Backend quality scripts
# Mirrors the frontend npm scripts: lint, lint:fix, test, build, check
# Usage: make lint | make lint-fix | make test | make build | make check
# ============================================================

PY ?= python

.PHONY: lint lint-fix format test build check coverage install-dev

lint:
	ruff check .

lint-fix:
	ruff check . --fix

format:
	ruff format .

test:
	$(PY) -m pytest

coverage:
	$(PY) -m pytest --cov=app --cov-report=term-missing

build:
	$(PY) -c "import compileall, sys; sys.exit(0 if compileall.compile_dir('app', quiet=1) else 1)"

check: lint test

install-dev:
	$(PY) -m pip install -r requirements.txt
