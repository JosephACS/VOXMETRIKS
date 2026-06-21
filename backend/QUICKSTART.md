# Backend — Quickstart

Documentación de arranque unificada: **[../docs/QUICKSTART.md](../docs/QUICKSTART.md)** (pasos 4–7: ELT, API, tests).

Resumen backend:

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
pytest tests/test_api.py -v
```

Ver también [README.md](../README.md).
