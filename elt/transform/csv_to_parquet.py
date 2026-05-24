import pandas as pd
import os

# Archivo origen
INPUT_FILE = "data/raw/spotify_dataset.csv"

# Carpeta destino
OUTPUT_DIR = "data/stage"

# Archivo parquet
OUTPUT_FILE = "spotify_dataset.parquet"

# Crear carpeta si no existe
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Ruta final
output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)

print("Leyendo CSV...")

df = pd.read_csv(INPUT_FILE)

print(f"Registros encontrados: {len(df)}")

print("Convirtiendo a Parquet...")

df.to_parquet(output_path, index=False)

print(f"Parquet guardado en: {output_path}")