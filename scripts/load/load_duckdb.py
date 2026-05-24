import duckdb
import os

# Crear carpeta duckdb
os.makedirs("duckdb", exist_ok=True)

# Conexión DuckDB
con = duckdb.connect("duckdb/voxmetrik.duckdb")

# Ruta parquet
PARQUET_FILE = "data/stage/spotify_dataset.parquet"

print("Cargando parquet en DuckDB...")

# Crear tabla
con.execute(f"""
CREATE OR REPLACE TABLE spotify_raw AS
SELECT *
FROM read_parquet('{PARQUET_FILE}')
""")

# Contar registros
count = con.execute("""
SELECT COUNT(*) FROM spotify_raw
""").fetchone()[0]

print(f"Registros cargados: {count}")

# Cerrar conexión
con.close()

print("Carga completada.")