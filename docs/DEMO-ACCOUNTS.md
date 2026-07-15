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
| `demo.business` | Presentación negocio | Menú reducido B2C+B2B ingresos/cobros + regalías lectura | `/discover`, `/account/*`, `/crm/*`, `/subscriptions/*`, `/billing/*`, `/business-analytics`, `/royalties/*` |
| `demo.artist` | Portal artista Spec 031 | Subir/enviar lanzamientos; ver contratos/statements; sin CRM/ops | `/artist/*`, `/royalties/statements`, `/payouts` |

### Cuenta de portal artista `demo.artist`

- Preferencia / rol de presentación: portal artista (`presentation_role=artist` o acceso `app_artist_portal_access`).
- Organización: **VOXMETRIKS Demo** con alcance a su `artist_profile`.
- **Puede:** crear/editar borradores, subir audio/portada privados, enviar a revisión, ver estados, contratos relacionados, statements/payouts propios en lectura.
- **No puede:** autoaprobarse (salvo flag demo auditado), ver otros artistas, CRM global, billing manage, pools de regalías globales, ops/compliance.
- Contraseña: `DEMO_ACCOUNT_PASSWORD` (nunca documentar el valor).

### Cuenta de presentación `demo.business`

- Roles: plataforma `sales_manager` (CRM) + org `billing_manager` (suscripción/facturación).
- Preferencia UI: `presentation_nav=true` (menú reducido solo en frontend; rutas del sistema siguen existiendo).
- Plan personal: Premium Individual (mock pay).
- Organización: miembro de **VOXMETRIKS Demo** (Professional).
- **Puede:** ver planes personales y empresariales, CRM básico (panel/prospectos/oportunidades), facturas y pagos, conciliación, panel empresarial, **regalías en lectura** (`/royalties/*`, `/payouts` — sin aprobar ni simular si la UI oculta acciones peligrosas).
- **No se le muestra en menú:** ELT, exploradores, auditoría, artistas, derechos, campañas, CS, soporte, compliance, ops, administración global (salvo regalías de demostración controlada).
- **No tiene** rol `owner` ni `platform_admin` (sin privilegios peligrosos de cierre de org / ops).

Emails canónicos: `{username}@demo.voxmetriks.local` (marcadas `preferences.demo=true`, `email_verified=true`).

## Separación de planes

- **Personales:** Free · Premium Individual · Premium Duo · Premium Familiar → `/account/*`
- **Empresariales:** Starter · Professional · Business · Enterprise → `/subscriptions/*` (contexto organización)

## Notas

- Tests (`pytest`) usan DB temporal aislada; nunca el warehouse de desarrollo.
- `EMAIL_PROVIDER=console` en pytest — no se envían correos reales.
- Idioma UI por defecto: **español**.
