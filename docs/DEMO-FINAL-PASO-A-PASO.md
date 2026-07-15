# Demo final paso a paso

Contraseña única local: variable `DEMO_ACCOUNT_PASSWORD` (no escribir aquí).

Scripts recomendados: `scripts/setup_demo.ps1` → `start_demo.ps1` → `verify_demo.ps1`.

## 1. Arranque

```powershell
.\scripts\setup_demo.ps1
.\scripts\start_demo.ps1
# http://127.0.0.1:4200
# http://127.0.0.1:8000/health
```

Manual equivalent:

```bash
# backend
cd apps/backend
set EMAIL_PROVIDER=console
set VOXMETRIKS_SEED_DEMO_ACCOUNTS=1
set DEMO_ACCOUNT_PASSWORD=TU_SECRETO
python scripts/seed_integrated_demo.py
uvicorn app.main:app --host 127.0.0.1 --port 8000

# frontend
cd apps/frontend
npm start -- --host 127.0.0.1 --port 4200
```

## 2. Flujo presentación 5 cuentas (7–10 min)

Orden sugerido (misma contraseña vía env):

| Min | Cuenta | Qué mostrar |
|-----|--------|-------------|
| 0–1 | `listener.free` | Discover/búsqueda, límites Free |
| 1–3 | `demo.artist` | Nuevo lanzamiento → audio/portada → derechos → enviar → revisión/publicar |
| 3–5 | `listener.free` → Premium | Planes → checkout **simulado** → factura |
| 5–7 | `organization.owner` o `demo.business` | Org VOXMETRIKS Demo, CRM o billing breve |
| 7–10 | `finance.manager` o `demo.business` | `/royalties` → settlement/statement/payout **simulado** |

Detalles por ruta: `docs/DEMO-ACCOUNTS.md`.

## 3. Artista → publicar (detalle)

Login `demo.artist` → `/artist/releases/new` → audio/portada → derechos 60/40 → enviar.
Revisor/admin → `/catalog-review` → aprobar → publicar.
Verificar búsqueda/perfil y audio **local_published** (no demo genérico).

## 4. B2C

`listener.free` → planes → Premium Individual → factura → pago **simulado**.
`listener.premium` → confirmar entitlements.
`household.owner` → household (no es org).

## 5. B2B

`sales.manager` → CRM.
`organization.owner` → plan org + miembros.
`finance.manager` → facturas/conciliación.

## 6. Regalías

`finance.manager` → `/royalties` → fondo → atribución → settlement → statement → payout **simulado**.
Banner: no mueve dinero real.

## 7. Presentación corta

`demo.business` — menú reducido ingresos.

## Fallos frecuentes

| Síntoma | Plan B |
|---------|--------|
| Failed to fetch | Backend apagado → `start_demo.ps1` |
| Menú completo en demo.business | Preferencia `presentation_nav` / re-seed |
| Sin media | Correr seed/publish una vez; `MEDIA_STORAGE_ROOT` |
| Org “none” | Seleccionar VOXMETRIKS Demo en selector |
| DB bloqueada al exportar | `stop_demo.ps1` luego `export_demo_runtime.ps1` |
