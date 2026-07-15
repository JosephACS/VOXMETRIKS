# Demo laptop setup

Fresh Windows laptop → runnable local demo. **No secrets in this doc.**

## 1. Prerequisites

- Windows 10/11, PowerShell 5.1+
- Python **≥ 3.11** on PATH
- Node.js LTS + npm on PATH
- Git

## 2. Get the code

```powershell
git clone <repo-url> voxmetriks
cd voxmetriks
git checkout demo-ready   # or the branch you were given
```

## 3. Restore runtime (recommended)

Copy `VOXMETRIKS-DEMO-RUNTIME` next to the repo (sibling folder), then:

```powershell
.\scripts\restore_demo_runtime.ps1
```

This restores `.env` files, DuckDB, and optional `data/media` after SHA256 verification.

Alternatively copy manually:

- `apps/backend/.env` from a secure channel
- `data/warehouse/voxmetrik.duckdb`

## 4. Install dependencies

```powershell
.\scripts\setup_demo.ps1
```

Creates `apps/backend/.venv`, installs pip requirements, runs `npm ci` in frontend.

## 5. Start / stop / verify

```powershell
.\scripts\start_demo.ps1
# prints only:
#   http://127.0.0.1:4200
#   http://127.0.0.1:8000/health

.\scripts\verify_demo.ps1
.\scripts\stop_demo.ps1
```

Backend child gets `EMAIL_PROVIDER=console` (no real email).

## 6. Optional re-seed

Only if `DEMO_ACCOUNT_PASSWORD` is available in process env or `apps/backend/.env`:

```powershell
cd apps\backend
$env:VOXMETRIKS_SEED_DEMO_ACCOUNTS = '1'
$env:EMAIL_PROVIDER = 'console'
# load DEMO_ACCOUNT_PASSWORD privately — do not Write-Host
.\.venv\Scripts\python.exe scripts\seed_integrated_demo.py
.\.venv\Scripts\python.exe scripts\seed_integrated_demo.py
.\.venv\Scripts\python.exe scripts\verify_final_demo_state.py
```

## 7. Accounts

See `docs/DEMO-ACCOUNTS.md` (usernames only; one shared local password via env).
