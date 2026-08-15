# Quickstart — 052

## Development checks

```powershell
cd apps/backend
python -m pytest -q tests/test_spec052_*.py --basetemp=.pytest-052

cd ../frontend
npm run lint
npm test
npm run build
```

E2E must launch the API against a temporary DuckDB copy and use dedicated 052 identities. Do not run purchase journeys against the canonical warehouse.

## Simulated-payment disclosure

The product must show one clear notice: no real charge occurs. Internal provider flags remain `is_mock/is_simulated` for truthfulness, but customer copy must not describe the application as an academic demo.
