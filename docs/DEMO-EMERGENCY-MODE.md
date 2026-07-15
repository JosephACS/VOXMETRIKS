# Demo emergency mode

When the prepared laptop or primary DB fails during a presentation. **No passwords here.**

## Decision tree (≤2 minutes)

1. **Backend health down** → `.\scripts\stop_demo.ps1` then `.\scripts\start_demo.ps1`. Check `scripts/.demo-pids/backend.log`.
2. **DuckDB missing/corrupt** → restore bundle: `.\scripts\restore_demo_runtime.ps1` then start again.
3. **Ports busy** → stop demo; if needed Task Manager kill orphaned `python`/`node` on 8000/4200.
4. **Login fails** → confirm `apps/backend/.env` exists and was restored; re-seed only if password is available in env (never invent one live).
5. **No network beyond localhost** → expected; demo is local-only.

## Fallback narrative (no live app)

Use:

- Pre-recorded video (see `docs/VIDEO-BACKUP-SCRIPT.md`)
- Screenshots / architecture slides from entregas
- Guion oral: B2C free→premium, artist publish, org billing, royalties mock

## What never to do live

- Type real passwords into slides or chat
- Force-push / reset Git mid-demo
- Point production SMTP at a real mailbox
- Run destructive `DROP` / wipe scripts without a backup sibling folder

## Contacts / prep

Keep a USB or cloud copy of `VOXMETRIKS-DEMO-RUNTIME` (encrypted) separate from the laptop clone.
