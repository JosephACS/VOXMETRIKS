from __future__ import annotations

import duckdb

from app.core.logging import get_logger
from app.etl.connection import count_rows, execute_ddl

logger = get_logger(__name__)

SILVER_USERS_DDL = """
CREATE TABLE IF NOT EXISTS silver_users (
    id_usuario        INTEGER PRIMARY KEY,
    nombre            VARCHAR NOT NULL,
    email             VARCHAR,
    email_normalized  VARCHAR,
    pais              VARCHAR,
    plan              VARCHAR,
    is_premium        BOOLEAN,
    fecha_registro    TIMESTAMP,
    cleaned_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""


def clean_users(conn: duckdb.DuckDBPyConnection, *, source_table: str = "dim_usuario") -> dict:
    """Normalize dim_usuario → silver_users."""
    logger.info("[SILVER] Cleaning users %s → silver_users", source_table)

    tables = {r[0] for r in conn.execute("SHOW TABLES").fetchall()}
    if source_table not in tables:
        raise RuntimeError(f"Source table '{source_table}' not found")

    execute_ddl(conn, SILVER_USERS_DDL)
    rows_in = count_rows(conn, source_table)

    conn.execute("DELETE FROM silver_users")

    conn.execute(
        f"""
        INSERT INTO silver_users (
            id_usuario, nombre, email, email_normalized, pais, plan,
            is_premium, fecha_registro, cleaned_at
        )
        SELECT
            id_usuario,
            nombre,
            email,
            lower(trim(email)) AS email_normalized,
            pais,
            plan,
            (lower(trim(COALESCE(plan, ''))) = 'premium') AS is_premium,
            fecha_registro,
            CURRENT_TIMESTAMP
        FROM (
            SELECT *,
                   ROW_NUMBER() OVER (
                       PARTITION BY id_usuario ORDER BY fecha_registro DESC NULLS LAST
                   ) AS rn
            FROM {source_table}
            WHERE id_usuario IS NOT NULL
        ) ranked
        WHERE rn = 1
        """
    )

    rows_out = count_rows(conn, "silver_users")
    logger.info("[SILVER] Cleaning users → silver_users (%s rows)", rows_out)
    return {
        "source": source_table,
        "target": "silver_users",
        "rows_in": rows_in,
        "rows_out": rows_out,
        "status": "ok",
    }
