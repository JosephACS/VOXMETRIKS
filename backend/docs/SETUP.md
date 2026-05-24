# VOXMETRIK_V2 Backend - Setup Guide

## Estructura de la carpeta

```
backend_voxmetrik_v2/
├── main.py                      # FastAPI app principal
├── database.py                  # Conexión DuckDB
├── requirements.txt             # Dependencias
├── voxmetrik.duckdb            # Base de datos
├── .env.example                # Config ejemplo
├── routes/                      # Endpoints API
│   ├── __init__.py
│   ├── artists.py              # /artists endpoints
│   ├── tracks.py               # /tracks endpoints
│   └── stats.py                # /stats y /genres endpoints
├── services/                    # Lógica de negocio
│   └── __init__.py             # Todos los servicios
├── schemas/                     # Modelos Pydantic
│   ├── __init__.py
│   └── models.py               # Todos los modelos
├── tests/                       # Tests (agregar test_api.py)
│   └── __init__.py
└── docs/                        # Documentación
    └── SETUP.md                # Este archivo
```

## Instalación

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Ejecutar el servidor
```bash
python main.py
```

### 3. Acceder a la API
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **API**: http://localhost:8000

## Endpoints disponibles

### Artistas
- `GET /artists/top` - Top artistas
- `GET /artists/{id}` - Detalles artista

### Tracks
- `GET /tracks/top` - Top tracks
- `GET /tracks/{id}` - Detalles track

### Géneros
- `GET /genres` - Todos los géneros
- `GET /genres/popularity` - Géneros con stats

### Estadísticas
- `GET /stats/general` - Estadísticas generales
- `GET /stats/energy-distribution` - Distribución energía

## Solución de problemas

**"Port 8000 already in use"**
```bash
uvicorn main:app --port 8001
```

**"Cannot open voxmetrik.duckdb"**
- Asegúrate que el archivo está en la carpeta raíz

**"ModuleNotFoundError"**
```bash
pip install -r requirements.txt
```
