# VOXMETRIK_V2 - GUÍA DE INICIO RÁPIDO

## ⚡ Inicio en 5 minutos

### Paso 1: Instalar dependencias
```bash
pip install -r requirements.txt
```

### Paso 2: Ejecutar el pipeline
```bash
python elt_pipeline.py
```

### Paso 3: Analizar resultados
```bash
python analyze_warehouse.py
```

---

## 📦 Requisitos Mínimos

- Python 3.8+
- 500 MB de espacio en disco
- Conexión a internet (para descargar dependencias)

---

## 🐳 Opción Docker

Si tienes Docker instalado:

```bash
# Compilar imagen
docker build -t voxmetrik-elt .

# Ejecutar pipeline
docker run -v $(pwd)/data:/app/data -v $(pwd)/duckdb:/app/duckdb voxmetrik-elt

# O usar docker-compose
docker-compose up
```

---

## 📊 Después de ejecutar

Los siguientes archivos se crearán automáticamente:

```
data/raw/raw_spotify.csv           # Datos crudos (CSV)
data/stage/raw_spotify.parquet     # Datos optimizados (Parquet)
duckdb/voxmetrik.duckdb           # Data Warehouse (DuckDB)
```

---

## 🔍 Consultar datos

Ejemplo básico en Python:

```python
import duckdb

conn = duckdb.connect('duckdb/voxmetrik.duckdb')

# Ver tabla de tracks
tracks = conn.execute("SELECT * FROM dim_track LIMIT 5").fetchall()
print(tracks)

# Top 5 artistas
top_artistas = conn.execute("""
    SELECT nombre_artista, promedio_popularidad 
    FROM agg_top_artistas a
    JOIN dim_artista d ON a.id_artista = d.id_artista
    LIMIT 5
""").fetchall()

for artista, popularidad in top_artistas:
    print(f"{artista}: {popularidad}")
```

---

## ✅ Verificar éxito

Después de ejecutar, deberías ver:

✓ Mensaje: `[SUCCESS] PIPELINE ELT COMPLETADO EXITOSAMENTE`
✓ Archivo: `duckdb/voxmetrik.duckdb` creado
✓ Tablas: 12 tablas en total (RAW + DIM + FACT + AGG + CTL)

---

## 🔧 Configuración para PocketBase

En `elt_pipeline.py`, busca `extract_from_pocketbase()` y reemplaza con:

```python
def extract_from_pocketbase(self) -> pd.DataFrame:
    url = "http://tu-servidor:8090/api/collections/spotify/records"
    response = urlopen(url)
    data = json.loads(response.read())
    return pd.DataFrame(data)
```

---

## 📈 Escalabilidad

El pipeline soporta:

- ✓ Datasets de 100k+ registros
- ✓ Cargas incrementales semanales
- ✓ Agregaciones pre-calculadas
- ✓ Auditoría completa de cambios

---

## ❓ Problemas Comunes

**Error: "No module named 'duckdb'"**
```bash
pip install --upgrade duckdb
```

**Error: "Permission denied"**
```bash
chmod +x elt_pipeline.py
python elt_pipeline.py
```

**Error: "Database locked"**
- Espera unos segundos
- Cierra otras aplicaciones accediendo a la BD

---

## 📚 Documentación Completa

Ver `README.md` para documentación detallada.

---

## 🚀 Próximos Pasos

1. **Revisar datos**: `python analyze_warehouse.py`
2. **Personalizar**: Modificar `elt_pipeline.py` según necesidades
3. **Producción**: Usar con Docker y PocketBase real
4. **Monitoreo**: Revisar tablas `ctl_*` para auditoría

---

## 💡 Tips

- Ejecuta regularmente: `python analyze_warehouse.py` para ver métricas
- Guarda `duckdb/voxmetrik.duckdb` regularmente
- Modifica datos en `SPOTIFY_SAMPLE_DATA` para tests
- Usa DuckDB IDE (DBeaver) para queries visuales

---

**¡Listo para analizar música! 🎵**
