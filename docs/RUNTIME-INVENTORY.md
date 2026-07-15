# Runtime inventory — VOXMETRIKS demo

What must exist on disk for a laptop demo. **No secrets in this file.**

## Required runtime artifacts

| Artifact | Path | Notes |
|----------|------|-------|
| Backend env | `apps/backend/.env` | From `.env.example`; includes `DEMO_ACCOUNT_PASSWORD` (never commit) |
| Optional root env | `.env` | Fallback / shared overrides |
| Warehouse | `data/warehouse/voxmetrik.duckdb` | ~hundreds of MB; not in Git |
| Media (optional) | `data/media/` | Local published audio/covers after Spec 031 flows |
| Backend venv | `apps/backend/.venv/` | Created by `scripts/setup_demo.ps1` |
| Frontend modules | `apps/frontend/node_modules/` | `npm ci` / `npm install` |

## Portable bundle

Export/restore sibling folder (gitignored):

- `../VOXMETRIKS-DEMO-RUNTIME/`
  - `env/backend.env`, `env/root.env` (if present)
  - `data/warehouse/voxmetrik.duckdb`
  - `data/media/` (optional)
  - `manifest.json`, `SHA256SUMS.txt`, `RESTORE-INSTRUCTIONS.txt`

Scripts:

- `scripts/export_demo_runtime.ps1`
- `scripts/restore_demo_runtime.ps1`

## Process / ports

| Service | URL | Port |
|---------|-----|------|
| Frontend | http://127.0.0.1:4200 | 4200 |
| Backend health | http://127.0.0.1:8000/health | 8000 |
| OpenAPI | http://127.0.0.1:8000/docs | 8000 |

PID/logs during managed demo: `scripts/.demo-pids/` (gitignored).

## Not required on laptop

- Cloud SMTP (use `EMAIL_PROVIDER=console`)
- Production CDN
- ELT gold rebuild (warehouse already seeded)
- Committing `*.duckdb` or `.env`
