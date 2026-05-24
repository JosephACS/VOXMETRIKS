# 🚀 VOXMETRIK_V2 Backend

Production-ready FastAPI backend for Spotify musical analysis data.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run server
python main.py

# 3. Visit documentation
# http://localhost:8000/docs
```

## Folder Structure

```
backend_voxmetrik_v2/
├── main.py              # FastAPI app entry point
├── database.py          # DuckDB connection
├── requirements.txt     # Dependencies
├── voxmetrik.duckdb    # Database (ready to use)
├── routes/             # API endpoints
│   ├── artists.py      # /artists endpoints
│   ├── tracks.py       # /tracks endpoints
│   └── stats.py        # /stats and /genres
├── services/           # Business logic
├── schemas/            # Pydantic models
├── tests/              # Test files
└── docs/               # Documentation
```

## Available Endpoints

- `GET /` - API info
- `GET /health` - Health check
- `GET /status` - System status

### Artists
- `GET /artists/top` - Top artists
- `GET /artists/{id}` - Artist details

### Tracks
- `GET /tracks/top` - Top tracks
- `GET /tracks/{id}` - Track details

### Genres
- `GET /genres` - All genres
- `GET /genres/popularity` - Genres with stats

### Stats
- `GET /stats/general` - Warehouse statistics
- `GET /stats/energy-distribution` - Energy distribution

## Features

✅ 18 endpoints
✅ DuckDB integration
✅ Pydantic v2 validation
✅ OpenAPI/Swagger docs
✅ Professional logging
✅ Error handling

## Requirements

- Python 3.8+
- pip

## License

VOXMETRIK Project - All Rights Reserved
