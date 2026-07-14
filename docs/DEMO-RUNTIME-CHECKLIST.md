# Checklist runtime — demo en laptop

Guía para levantar VOXMETRIKS desde la rama **`demo-ready`**. No incluye secretos ni contraseñas reales.

---

## 1. Obtener el código

```bash
git clone https://github.com/JosephACS/VOXMETRIKS.git
cd VOXMETRIKS
git fetch origin demo-ready
git checkout demo-ready
```

Si ya tienes el repo:

```bash
git fetch origin
git checkout demo-ready
git pull origin demo-ready
```

---

## 2. Archivos locales que debes copiar (no están en Git)

| Qué | Origen (máquina de desarrollo) | Destino en la laptop |
|-----|--------------------------------|----------------------|
| **`.env` backend** | Copia manual segura | `apps/backend/.env` |
| **Warehouse DuckDB** | Copia del archivo binario | `data/warehouse/voxmetrik.duckdb` |
| **Bronce opcional** | Solo si no ejecutarás ELT | `data/bronze/raw_spotify.parquet` |

### Rutas exactas

- **`.env` que usa el backend (orden de carga):**
  1. `apps/backend/.env` (recomendado para demo local)
  2. `<repo>/.env` (raíz del monorepo)
  3. `infrastructure/environments/.env`

  El backend resuelve variables con `apps/backend/app/core/config.py`. **No subas `.env` a Git.**

- **DuckDB de desarrollo (warehouse musical):**
  - Variable: `DB_PATH` en `.env` (vacío = auto)
  - Ruta por defecto: `<repo>/data/warehouse/voxmetrik.duckdb`
  - Ejemplo absoluto Windows: `C:\Users\<tu-usuario>\...\voxmetriks\data\warehouse\voxmetrik.duckdb`

### Otros runtime opcionales

- Portadas/audio en caché: se regeneran; no es obligatorio copiarlas.
- `node_modules/`, `.venv/`, `dist/`: se instalan/generan en la laptop (no copiar).

---

## 3. Variables importantes en `.env`

Copia desde `apps/backend/.env.example` y completa:

| Variable | Uso demo |
|----------|----------|
| `DB_PATH` | Vacío → usa `data/warehouse/voxmetrik.duckdb` |
| `DEMO_ACCOUNT_PASSWORD` | Contraseña compartida de cuentas demo (solo local) |
| `VOXMETRIKS_SEED_DEMO_ACCOUNTS` | `1` para ejecutar seed integrado |
| `EMAIL_PROVIDER` | `console` (sin SMTP real) |
| `CORS_ORIGINS` | `http://localhost:4200,http://127.0.0.1:4200` |
| `RUN_ETL_ON_BOOT` | `never` si ya copiaste el DuckDB |
| `ENVIRONMENT` | `development` |

**No escribas la contraseña demo en este documento ni la commitees.**

Plan alternativo sin correo: `EMAIL_PROVIDER=console` (pytest y demo local ya lo usan).

---

## 4. Instalar backend

```bash
cd voxmetriks
python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r apps/backend/requirements.txt
```

Copia `.env`:

```bash
copy apps\backend\.env.example apps\backend\.env
# Edita apps\backend\.env con DEMO_ACCOUNT_PASSWORD y DB_PATH si aplica
```

Seed demo integrado (opcional, idempotente):

```bash
cd apps\backend
set VOXMETRIKS_SEED_DEMO_ACCOUNTS=1
set DEMO_ACCOUNT_PASSWORD=TU_SECRETO_LOCAL
python scripts\seed_integrated_demo.py --cleanup-first
```

---

## 5. Instalar frontend

```bash
cd apps\frontend
npm install
```

---

## 6. Iniciar servicios

**Backend** (desde `apps/backend`):

```bash
cd apps\backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend** (otra terminal):

```bash
cd apps\frontend
npm start
```

UI: http://localhost:4200
API docs: http://localhost:8000/docs

---

## 7. Validar salud

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/health
```

Respuesta esperada: JSON con estado OK (sin exponer rutas sensibles si `HEALTH_VERBOSE=false`).

---

## 8. Cuentas demo

Ver **`docs/DEMO-ACCOUNTS.md`** (sin contraseñas).

| Usuario | Rol | Rutas |
|---------|-----|-------|
| `listener.free` | B2C Free | `/home`, `/account/plans` |
| `listener.premium` | B2C Premium | `/account/subscription` |
| `household.owner` | B2C Familiar | `/account/household` |
| `organization.owner` | B2B org demo | `/subscriptions/overview` |
| `finance.manager` | Facturación | `/billing/invoices` |
| `sales.manager` | CRM | `/crm` |
| `platform.admin` | Ops | `/platform-ops` |

Email: `{username}@demo.voxmetriks.local`
Contraseña: valor de `DEMO_ACCOUNT_PASSWORD` en tu `.env` local.

---

## 9. Validación rápida post-arranque

```bash
cd apps\backend
python -m pytest tests/test_subscriptions_use_cases_k2.py -q
cd ..\frontend
npm run lint
npm test
npm run build
```

---

## 10. Qué NO subir a Git

- `.env`, `.env.local`, credenciales SMTP/Resend
- `*.duckdb`, `*.db`, bases pytest temporales
- `node_modules/`, `dist/`, `.venv/`, cachés
- Logs y artefactos de cobertura

Plantillas seguras: `apps/backend/.env.example`, `infrastructure/environments/.env.example`.
