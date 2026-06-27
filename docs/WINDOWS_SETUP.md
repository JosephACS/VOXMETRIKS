# Setup en Windows

Guía específica de Windows. Para el flujo general ver [`QUICKSTART.md`](QUICKSTART.md).

## Requisitos

- **Python 3.12** ("Add Python to PATH" al instalar)
- **Node.js 20+** (para el frontend Angular)
- **PocketBase** corriendo con el dataset (~100k) — fuente del catálogo

Verifica:

```powershell
python --version
node --version
```

## 1. Entorno virtual + dependencias (backend / ELT)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
pip install -r backend\requirements.txt
```

## 2. Configurar entorno

```powershell
Copy-Item .env.example .env
```

Edita `.env` con tus credenciales de PocketBase (`POCKETBASE_URL`, `POCKETBASE_EMAIL`, `POCKETBASE_PASSWORD`).

## 3. Construir el warehouse (ELT)

Con PocketBase arriba y el dataset cargado:

```powershell
python elt\pipelines\elt_pipeline.py
```

Genera `data\warehouse\voxmetrik.duckdb`. Validación opcional:

```powershell
python scripts\validate_warehouse.py
python scripts\analyze_warehouse.py
```

## 4. Backend (API)

```powershell
cd backend
uvicorn app.main:app --reload --port 8000
```

- Swagger: http://localhost:8000/docs
- Health: http://localhost:8000/health

## 5. Frontend

```powershell
cd frontend
npm install
npm start
```

SPA en http://localhost:4200.

## Arranque rápido todo-en-uno

```powershell
scripts\dev_start.bat
```

## Alternativa: Docker

Levanta PocketBase → ELT → API → frontend con una sola orden:

```powershell
docker compose up --build
```

- Frontend: http://localhost:8080
- API: http://localhost:8000

## Problemas comunes

| Síntoma | Solución |
|---------|----------|
| `python no se reconoce` | Reinstala Python marcando "Add to PATH" y reinicia la terminal |
| `No module named duckdb` | Activa el venv y reinstala: `pip install -r requirements.txt` |
| `BRONZE EXTRACT FAILED` | PocketBase no está arriba o `.env` mal configurado |
| API no conecta desde el front | Revisa `CORS_ORIGINS` en `.env` (incluir `http://localhost:4200`) |
