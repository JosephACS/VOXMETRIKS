"""Test S1: Customer success schema — Spec 025."""

from app.core.database import using_write_conn
from app.packages.customer_success.infrastructure.schema import CS_TABLES


def test_cs_tables_exist():
    with using_write_conn() as conn:
        for table in CS_TABLES:
            conn.execute(f"SELECT id FROM {table} LIMIT 0")
