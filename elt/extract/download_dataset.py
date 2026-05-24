import requests
import os

# URL del dataset en PocketBase
URL = "http://127.0.0.1:8090/api/files/datasets/cc9arh0oe73ifc5/dataset_4unz6fyld6.csv"

# Carpeta destino
OUTPUT_DIR = "data/raw"

# Nombre archivo local
OUTPUT_FILE = "spotify_dataset.csv"

# Crear carpeta si no existe
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Ruta final
output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)

print("Descargando dataset desde PocketBase...")

response = requests.get(URL)

if response.status_code == 200:
    with open(output_path, "wb") as file:
        file.write(response.content)

    print(f"Dataset guardado en: {output_path}")

else:
    print("Error descargando dataset")
    print(response.status_code)