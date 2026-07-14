# Cuentas demo locales — VOXMETRIKS

Guía de demostración B2C + B2B. **No contiene contraseñas.**

## Contraseña

Todas las cuentas usan el mismo secreto local definido en:

```text
DEMO_ACCOUNT_PASSWORD
```

(aliases leídos si falta: `DEMO_PASSWORD`, `VOXMETRIKS_DEMO_PASSWORD`)

- Solo se almacena el **hash** en DuckDB.
- No commits del valor real.
- Placeholder en `apps/backend/.env.example`.

## Seed

```bash
cd apps/backend
# Opcional: limpiar orgs/planes de pytest / Golden Path (no toca catálogo musical)
python scripts/cleanup_test_organizations.py --apply --retire-test-plans

set VOXMETRIKS_SEED_DEMO_ACCOUNTS=1
set DEMO_ACCOUNT_PASSWORD=TU_SECRETO_LOCAL
python scripts/seed_integrated_demo.py --cleanup-first
# segunda ejecución = idempotente
python scripts/seed_integrated_demo.py
```

Organización canónica: **VOXMETRIKS Demo** (`slug=voxmetriks-demo`, `is_demo=true`).

## Cuentas

| Identificador | Rol | Qué demuestra | Rutas principales |
|---------------|-----|---------------|-------------------|
| `listener.free` | Listener Free (B2C) | Música, límites Free, planes personales | `/home`, `/search`, `/playlists`, `/account/plans` |
| `listener.premium` | Premium Individual | Checkout mock, factura personal, entitlements | `/account/subscription`, `/account/billing`, `/account/plans` |
| `household.owner` | Titular Familiar | Household, invitaciones, miembros | `/account/household`, `/account/subscription` |
| `platform.admin` | Platform Admin | Catálogos B2C/B2B, métricas, ops | `/platform-ops`, `/account/plans`, CRM si aplica |
| `sales.manager` | Sales Manager | Prospectos → oportunidades → cotización → contrato | `/crm/*` |
| `organization.owner` | Owner org demo | Org, plan Professional, miembros, módulos empresa | `/organizations/*`, `/subscriptions/*` |
| `finance.manager` | Billing/Finance org | Facturas, pagos, conciliación, refunds, credit notes | `/billing/*` |

Emails canónicos: `{username}@demo.voxmetriks.local` (marcadas `preferences.demo=true`, `email_verified=true`).

## Separación de planes

- **Personales:** Free · Premium Individual · Premium Duo · Premium Familiar → `/account/*`
- **Empresariales:** Starter · Professional · Business · Enterprise → `/subscriptions/*` (contexto organización)

## Notas

- Tests (`pytest`) usan DB temporal aislada; nunca el warehouse de desarrollo.
- `EMAIL_PROVIDER=console` en pytest — no se envían correos reales.
- Idioma UI por defecto: **español**.
