#!/usr/bin/env python3
"""CLI entry point for V2 Bronze/Silver ETL."""

from app.etl.pipelines import main

if __name__ == "__main__":
    raise SystemExit(main())
