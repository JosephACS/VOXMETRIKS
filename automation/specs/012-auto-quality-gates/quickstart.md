# Quickstart: Calidad Automática (Spec 012)

## Backend

```powershell
cd backend
pip install -r requirements.txt

# Lint
make lint
# o: python -m ruff check .

# Auto-fix mecánico
make lint-fix

# Tests (incluye hotspots)
make test
# o: python -m pytest -v tests/test_quality_hotspots.py

# Cobertura
make coverage

# Gate completo
make check
```

## Frontend

```powershell
cd frontend
npm install

npm run lint
npm run lint:fix
npm run test
npm run build
npm run check    # lint + test + build
```

## Hotspots — ejecutar tests aislados

```powershell
# Backend
cd backend
python -m pytest tests/test_quality_hotspots.py -v

# Frontend
cd frontend
npx ng test --no-watch --include **/music-player.service.spec.ts
```

## CI recomendado

```yaml
# Ejemplo conceptual
- run: cd backend && make check
- run: cd frontend && npm run check
```

Variables: `CI=true` hace que `ng test` use modo no-interactivo (redundante con `--no-watch`).
