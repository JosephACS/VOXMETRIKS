# VOXMETRIK_V2 — Quick Start

## Prerequisites

- Python **3.12** (not 3.13+)
- pip ≥ 24

---

## 1. Clone / unzip and enter the project

```bash
cd VOXMETRIK_V2
```

---

## 2. Create virtual environment (recommended)

```bash
python3.12 -m venv .venv

# Linux / Mac
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

No wheels are compiled from source. All packages have pre-built binaries for Python 3.12.

---

## 4. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```
POCKETBASE_URL=http://127.0.0.1:8090
POCKETBASE_EMAIL=your_admin@email.com
POCKETBASE_PASSWORD=your_password
DB_PATH=           # leave blank for default: ./duckdb/voxmetrik.duckdb
```

If you don't have PocketBase, place your Parquet file at:

```
data/processed/stage/raw_spotify.parquet
```

---

## 5. Run the ELT pipeline

```bash
python elt_pipeline.py
```

**What this does:**
- Tries PocketBase → falls back to local Parquet
- Creates `duckdb/voxmetrik.duckdb` (or recreates it if corrupt/stale)
- Populates: `raw_spotify`, `dim_*`, `fact_audio_features`, `agg_*`, `ctl_*`

---

## 6. Start the API

```bash
cd backend
uvicorn main:app --reload
```

Or from project root:

```bash
uvicorn backend.main:app --reload
```

API is live at: http://127.0.0.1:8000

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc:       http://127.0.0.1:8000/redoc
- Health:      http://127.0.0.1:8000/health

---

## 7. API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/artists` | List artists (paginated, searchable) |
| GET | `/api/v1/artists/top` | Top artists by avg popularity |
| GET | `/api/v1/artists/{id}` | Artist by ID |
| GET | `/api/v1/artists/{id}/stats` | Artist stats |
| GET | `/api/v1/genres` | List genres |
| GET | `/api/v1/genres/stats` | Genre popularity stats |
| GET | `/api/v1/genres/{id}` | Genre by ID |
| GET | `/api/v1/tracks` | List tracks (filter by name/genre/artist) |
| GET | `/api/v1/tracks/{id}` | Track by ID |
| GET | `/api/v1/tracks/{id}/features` | Audio features for a track |
| GET | `/api/v1/stats/summary` | Row counts for all tables |
| GET | `/api/v1/stats/energia` | Energy distribution |
| GET | `/api/v1/stats/top-tracks` | Top tracks by popularity |
| GET | `/api/v1/stats/loads` | Recent pipeline load history |

---

## 8. Docker (optional)

```bash
# Build image
docker build -t voxmetrik_v2 .

# Run pipeline first
docker compose run --rm pipeline

# Start API
docker compose up api
```

---

## Troubleshooting

### `SerializationError: Failed to deserialize…`
The DuckDB file was written by a different DuckDB version.
**Fix:** The pipeline will automatically back up the old file and recreate it.
You can also manually delete `duckdb/voxmetrik.duckdb` and re-run the pipeline.

### `NOT NULL constraint failed: dim_track.nombre_track`
Rows with null/empty `track_name` are filtered out in `_normalize_df()` before
they reach the database. If this still appears, check your source data.

### `BinderException: Referenced column … not found`
The backend never invents column names. All SQL uses `DESCRIBE <table>` to get
real columns. If you see this, the pipeline may not have run or the schema is
outdated — run `python elt_pipeline.py` again.

### PocketBase 404 on `/api/admins/auth-with-password`
The modern endpoint is `/api/collections/_superusers/auth-with-password`.
This is already handled in the updated pipeline.
