# VOXMETRIK_V2 - Guía de Instalación en Windows

## 🪟 Instalación Paso a Paso en Windows

### Paso 1: Verificar Python instalado

Abre **PowerShell** o **CMD** y ejecuta:

```cmd
python --version
```

Deberías ver Python 3.8 o superior. Si no está instalado, descárgalo de:
https://www.python.org/downloads/

**IMPORTANTE:** Durante la instalación, marca la casilla "Add Python to PATH"

### Paso 2: Crear carpeta del proyecto

```cmd
mkdir VOXMETRIK_V2
cd VOXMETRIK_V2
```

Coloca aquí todos los archivos del proyecto:
- `elt_pipeline.py`
- `requirements.txt`
- `analyze_warehouse.py`
- `example_queries.py`
- `README.md`
- etc.

### Paso 3: Crear entorno virtual

```cmd
python -m venv venv
```

Esto crea una carpeta `venv` con un entorno aislado.

### Paso 4: Activar entorno virtual

**En PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

**En CMD:**
```cmd
venv\Scripts\activate.bat
```

Deberías ver `(venv)` al inicio de la línea de comandos.

### Paso 5: Instalar dependencias

```cmd
pip install --upgrade pip
pip install -r requirements.txt
```

Esto instala:
- pandas
- duckdb
- pyarrow
- python-dateutil
- requests
- tabulate

**Espera a que termine completamente** (2-5 minutos).

### Paso 6: Ejecutar el pipeline

```cmd
python elt_pipeline.py
```

**Esperado:**
- Deberías ver mensajes [INFO], [SUCCESS] en la consola
- Al final: "PIPELINE ELT COMPLETADO EXITOSAMENTE ✓"
- Se crearán carpetas: `data/`, `duckdb/`

### Paso 7: Analizar resultados (opcional)

```cmd
python analyze_warehouse.py
```

Muestra estadísticas del Data Warehouse.

### Paso 8: Ver consultas de ejemplo (opcional)

```cmd
python example_queries.py
```

Ejecuta 8 consultas SQL de análisis musical.

---

## ❌ Solución de Problemas

### Error: "python no es reconocido"

**Solución:**
1. Reinicia PowerShell/CMD
2. Si persiste, instala Python nuevamente
3. Durante la instalación, marca "Add Python to PATH"

### Error: "No such file or directory"

**Solución:**
- Verifica estar en la carpeta correcta: `cd VOXMETRIK_V2`
- Verifica que todos los `.py` estén en esa carpeta

### Error: "No module named 'duckdb'"

**Solución:**
```cmd
pip install duckdb --upgrade
```

### Error: "Permission denied" o "Cannot open database"

**Solución:**
1. Cierra otros programas que accedan a DuckDB
2. Elimina la carpeta `duckdb/`
3. Vuelve a ejecutar: `python elt_pipeline.py`

### Error: "TabError: inconsistent use of tabs and spaces"

**Solución:**
- El archivo tiene problema de indentación
- Descarga nuevamente `elt_pipeline.py` desde outputs

---

## 📁 Estructura esperada después de ejecutar

```
VOXMETRIK_V2/
├── venv/                          (Entorno virtual)
├── data/
│   ├── raw/
│   │   └── raw_spotify.csv
│   └── stage/
│       └── raw_spotify.parquet
├── duckdb/
│   └── voxmetrik.duckdb          ⭐ BASE DE DATOS
├── elt_pipeline.py
├── analyze_warehouse.py
├── example_queries.py
├── requirements.txt
└── README.md
```

---

## 🔍 Verificar que todo funciona

### 1. Verificar archivos creados

Abre el Explorador de Archivos (`Win + E`) y verifica:
- ✓ Existe `data/raw/raw_spotify.csv` (~50 KB)
- ✓ Existe `data/stage/raw_spotify.parquet` (~20 KB)
- ✓ Existe `duckdb/voxmetrik.duckdb` (~200 KB)

### 2. Consultar la BD en Python

Crea un archivo `test.py`:

```python
import duckdb

conn = duckdb.connect('duckdb/voxmetrik.duckdb')

# Ver tablas
tablas = conn.execute(
    "SELECT table_name FROM information_schema.tables"
).fetchall()

print("Tablas creadas:")
for tabla in tablas:
    print(f"  - {tabla[0]}")

# Ver datos
tracks = conn.execute("SELECT COUNT(*) FROM dim_track").fetchone()
print(f"\nTotal de tracks: {tracks[0]}")
```

Ejecuta:
```cmd
python test.py
```

Deberías ver:
```
Tablas creadas:
  - raw_spotify
  - dim_artista
  - dim_album
  - ...

Total de tracks: 15
```

---

## 🎯 Comandos útiles en Windows

```cmd
# Activar entorno virtual
venv\Scripts\activate.bat

# Desactivar entorno virtual
deactivate

# Ver versión de Python
python --version

# Ver paquetes instalados
pip list

# Actualizar pip
python -m pip install --upgrade pip

# Ejecutar script
python nombre_archivo.py

# Eliminar carpeta (equivalente a rm -rf en Linux)
rmdir /s duckdb

# Limpiar caché de Python
py -m pip cache purge
```

---

## 📊 Después de ejecutar exitosamente

Tienes un **Data Warehouse profesional** con:

✅ **12 Tablas:**
- RAW: raw_spotify
- Dimensiones: dim_artista, dim_album, dim_genero, dim_track
- Facts: fact_audio_features
- Aggregations: agg_genero_popularidad, agg_top_artistas, agg_distribucion_energia
- Control: ctl_carga_dataset, ctl_auditoria, ctl_reporte

✅ **Datos de ejemplo:**
- 15 canciones de Spotify
- 13 artistas únicos
- 8 géneros diferentes
- 13 álbumes

✅ **Listo para:**
- Cargar datos reales desde PocketBase
- Ejecutar análisis con DuckDB
- Generar reportes de auditoría
- Hacer cargas incrementales

---

## 🚀 Próximos Pasos

1. **Conectar a PocketBase:**
   - Edita `elt_pipeline.py`
   - Modifica `extract_from_pocketbase()` con tu URL de PocketBase

2. **Hacer consultas SQL:**
   - Instala DBeaver (gratis)
   - Conecta a `duckdb/voxmetrik.duckdb`
   - Ejecuta SQL directamente

3. **Integrar con tu aplicación:**
   - Importa duckdb en tu código Python
   - Consulta el warehouse desde tu app

---

## 💬 Errores comunes y soluciones rápidas

| Error | Solución |
|-------|----------|
| `ModuleNotFoundError: No module named 'X'` | `pip install X` |
| `FileNotFoundError` | Verificar ruta relativa, estar en carpeta VOXMETRIK_V2 |
| `PermissionError: database is locked` | Cerrar el archivo o esperar 5 segundos |
| `AttributeError: module 'logging'` | Descargar nuevamente elt_pipeline.py |
| DuckDB size grows fast | Normal, comprime con Parquet automáticamente |

---

## 📞 Soporte

Si tienes problemas:

1. **Lee el README.md** - tiene documentación completa
2. **Ejecuta analyze_warehouse.py** - muestra problemas de integridad
3. **Verifica requirements.txt** - asegúrate instalar todo
4. **Revisa logs en consola** - tienen mensajes [ERROR] descriptivos

---

**¡Pipeline ELT listo para ejecutar en Windows! 🎉**

Ahora ejecuta:
```cmd
python elt_pipeline.py
```

Y verás tu Data Warehouse en acción.
