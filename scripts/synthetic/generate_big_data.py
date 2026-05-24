import duckdb
import pandas as pd
import numpy as np
import os

# Configuración
MULTIPLIER = 8   # 100k x 8 = 800k

# Conexión DuckDB
con = duckdb.connect("duckdb/voxmetrik.duckdb")

print("Leyendo tabla original...")

df = con.execute("""
SELECT * FROM spotify_raw
""").fetchdf()

print(f"Registros originales: {len(df)}")

# Escalamiento
print("Generando dataset sintético...")

df_big = pd.concat([df] * MULTIPLIER, ignore_index=True)

# Randomización de columnas numéricas
np.random.seed(42)

if "popularity" in df_big.columns:
    df_big["popularity"] = np.random.randint(0, 100, len(df_big))

if "energy" in df_big.columns:
    df_big["energy"] = np.random.uniform(0, 1, len(df_big))

if "danceability" in df_big.columns:
    df_big["danceability"] = np.random.uniform(0, 1, len(df_big))

if "tempo" in df_big.columns:
    df_big["tempo"] = np.random.uniform(60, 200, len(df_big))

print(f"Nuevo tamaño: {len(df_big)}")

# Guardar en DuckDB
con.execute("""
CREATE OR REPLACE TABLE spotify_big_data AS
SELECT * FROM df_big
""")

print("Tabla spotify_big_data creada.")

# Verificación
count = con.execute("""
SELECT COUNT(*) FROM spotify_big_data
""").fetchone()[0]

print(f"Registros finales en DuckDB: {count}")

con.close()