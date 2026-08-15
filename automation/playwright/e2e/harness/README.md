# Spec 051 isolated E2E harness

Fail-closed Playwright for Spec 051. Never mutates `data/warehouse/voxmetrik.duckdb`.

## Run

```powershell
# Frontend must be reachable (or the harness starts it).
npm --prefix automation/playwright run e2e:051
```

What it does:

1. Copies the canonical DuckDB to `%TEMP%\voxmetrik-051-e2e\voxmetrik.duckdb`
2. Starts API on `127.0.0.1:8010` with `DB_PATH` = that temp file (`E2E=1`)
3. Seeds personas (listener, owner, administrator, collaborator/member, reader, label manager, platform admin)
4. Runs `playwright.051.config.ts` (no ambient globalSetup)
5. Tears down the isolated API

## Guards

- Refuses to start if `DB_PATH` resolves to the canonical warehouse
- Refuses temp paths under `data/warehouse`
- Requires OpenAPI routes `/artist-access/discover` and `/platform/catalog-reviews`
- Spec asserts `DB_PATH` contains `voxmetrik-051-e2e` before any test
