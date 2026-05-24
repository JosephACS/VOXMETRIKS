# VOXMETRIK_V2 - Quick Start Guide 🚀

## 5 minutos para empezar

### Paso 1: Instalar Dependencias
```bash
pip install -r requirements.txt
```

### Paso 2: Verificar Base de Datos
```bash
python scripts/init.py
```

Deberías ver:
```
✅ Archivo de base de datos encontrado
✅ Conexión a DuckDB establecida correctamente
✅ dim_artista
✅ dim_genero
✅ dim_track
✅ dim_album
✅ fact_audio_features
```

### Paso 3: Iniciar el Servidor
```bash
uvicorn main:app --reload
```

O simplemente:
```bash
python main.py
```

### Paso 4: Acceder a la API
Abre tu navegador:
- **Documentación interactiva**: http://localhost:8000/docs
- **Documentación ReDoc**: http://localhost:8000/redoc
- **API base URL**: http://localhost:8000

## Primeros Comandos

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. Obtener Top Artistas
```bash
curl http://localhost:8000/artists/top?limit=10
```

### 3. Obtener Estadísticas Generales
```bash
curl http://localhost:8000/stats/general
```

### 4. Buscar Tracks
```bash
curl "http://localhost:8000/tracks/search/?q=love&limit=10"
```

## Usando con Python

```python
import requests

# Obtener top artistas
response = requests.get("http://localhost:8000/artists/top")
artists = response.json()["data"]
print(f"Top artist: {artists[0]['nombre_artista']}")

# Obtener estadísticas
response = requests.get("http://localhost:8000/stats/general")
stats = response.json()["data"]
print(f"Total tracks: {stats['total_tracks']}")
```

## Estructura de Carpetas
```
backend/
├── main.py                # ⭐ Archivo principal
├── database.py            # Conexión a BD
├── requirements.txt       # Dependencias
├── routes/                # Endpoints
│   ├── artists.py
│   ├── genres.py
│   ├── tracks.py
│   └── stats.py
└── services/              # Lógica de negocio
    ├── artist_service.py
    ├── genre_service.py
    ├── track_service.py
    └── stats_service.py
```

## Solución de Problemas

### Error: "Database file not found"
```bash
# Verificar que existe el archivo
ls duckdb/voxmetrik.duckdb

# Verificar la ruta en .env
cat .env | grep DB_PATH
```

### Error: "Port 8000 already in use"
```bash
# Usar otro puerto
uvicorn main:app --reload --port 8001
```

### Error: "Module not found"
```bash
# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
```

## Endpoints Principales

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/artists/top` | GET | Top 10 artistas |
| `/genres/top` | GET | Top 10 géneros |
| `/tracks/top` | GET | Top 10 tracks |
| `/stats/general` | GET | Estadísticas generales |
| `/stats/energy-distribution` | GET | Distribución de energía |

## Parámetros Comunes

```bash
# Limitar resultados
?limit=20

# Buscar
?q=término_búsqueda

# Combinar
?q=drake&limit=30
```

## Testing

```bash
# Ejecutar tests
pytest tests/test_api.py -v

# Con cobertura
pytest tests/test_api.py --cov
```

## Despliegue Rápido con Docker

```bash
# Construir imagen
docker build -t voxmetrik-api .

# Ejecutar contenedor
docker run -p 8000:8000 voxmetrik-api

# Con docker-compose
docker-compose up -d
```

## Documentación Completa

Ver `README.md` para documentación detallada de:
- Todos los endpoints
- Ejemplos de respuestas
- Configuración avanzada
- Deployment en producción

## Soporte

¿Problemas? Verifica:
1. `python scripts/init.py --full`
2. Los logs en la terminal
3. La documentación en `/docs`

¡Listo! 🎉 Tu API está corriendo.
