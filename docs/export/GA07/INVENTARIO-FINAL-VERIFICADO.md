# Inventario final verificado — VOXMETRIKS

**Fecha de verificación:** 2026-07-15
**Estado del sistema:** `ENTERPRISE_ACADEMIC_SYSTEM_CLOSED_WITH_ACCEPTED_DEBT`
**Git en esta auditoría:** no ejecutado

## Aclaración: casos de uso

| Tipo | Definición | Conteo verificado |
|------|------------|-------------------|
| **Técnico** | Métodos/funciones públicos en `*use_cases*.py` (sin `_privados`) | **404** |
| **Negocio (agrupados)** | Objetivos únicos por actor (login, publicar, facturar, etc.) derivados de Specs 001–031 + menús | **≈ 95–110** (estimación documental por dominio; **no** 1:1 con métodos) |

No afirmar que 404 métodos = 404 casos de negocio únicos.

---

## Cifras técnicas

| Ítem | Valor | Fuente / método | Exclusiones / límites |
|------|------:|-----------------|------------------------|
| Specs `001`–`031` | **31** | `automation/specs/^\d{3}-` | Archive fuera del prefijo |
| Specs con closure `CLOSED*` explícito | **7** rastreadas en muestras 016–019/029–031; resto cerrado vía TRACEABILITY/028 | Lectura docs | Histórico uneven |
| Paquetes backend | **24** | `apps/backend/app/packages` | `__pycache__` |
| Paquetes frontend | **24** | `apps/frontend/src/app/packages` | |
| Endpoints `@*router.*` | **469** | Regex en `apps/backend/app/**/*.py` | Helpers no-router |
| Use-cases técnicos | **404** | AST `*use_cases*.py` | Services sin ese nombre |
| Literales `path:` FE | **128** únicos | `*routes*.ts` | Wildcards vacíos |
| Tests BE `test_*.py` | **88** | `apps/backend/tests` | |
| Tests FE `*.spec.ts` | **37** | frontend recursive | |
| DuckDB tamaño | **393.01 MB** (412 102 656 B) | `stat` `data/warehouse/voxmetrik.duckdb` | Lock puede impedir conteos |
| Tablas `main` | **183** | `information_schema` | |
| Prefijo `app_` | **138** tablas | DuckDB names | |
| `dim_track` | **89 740** | `COUNT(*)` | Importado |
| `dim_artista` | **31 429** | `COUNT(*)` | |
| `dim_album` | **46 154** | `COUNT(*)` | |
| Eventos ACTIVITY facts | **900 000** | `SUM(COUNT(*))` sobre `ACTIVITY_FACT_TABLES` (streaming+user_activity+playlist+favorites+searches+sessions); ctl `synthetic_activity_target_900000` | Heurística parcial sin favorites/searches da 801 000 |
| Cuentas demo seed | **11** | `DEMO_USERS` en `seed_integrated_demo.py` | Password solo env |
| Audio/portadas locales bajo `data/media` | **0** en disco al inventariar | Path aún no creado hasta primer upload | Seed crea al correr |

### Prefijos referidos en código (heurística estática previa)

Ver reportes Spec 030 / inventarios previos: `app_` dominante; warehouse `dim_/fact_/agg_/ctl_`.

---

## Precios canónicos (código)

**B2C** — `personal_subscriptions/application/catalog.py`
Free $0 · Individual $4.99 / $49.90 · Duo $7.99 / $79.90 · Familiar $9.99 / $99.90

**B2B** — `subscriptions/application/commercial_catalog.py`
Starter $49/$490 · Professional $99/$990 · Business $199/$1 990 · Enterprise $499/$4 990

Importes 75/100/200/500: solo `_LEGACY_DEMO_AMOUNTS` (retiro), no catálogo activo.

---

## Runtime a copiar a otra PC

- Repo código
- `data/warehouse/voxmetrik.duckdb`
- `data/media/` (si existe tras seeds/uploads)
- `apps/backend/.env` (nunca en git; no documentar secretos)
- Dependencias: venv + `npm install`

## Variables `.env` (nombres, sin valores)

`DB_PATH`, `DEMO_ACCOUNT_PASSWORD`, `VOXMETRIKS_SEED_DEMO_ACCOUNTS`, `EMAIL_PROVIDER`, `MEDIA_STORAGE_*`, `ALLOW_DEMO_SELF_APPROVE`, `CORS_ORIGINS`, `FRONTEND_BASE_URL`, `YOUTUBE_API_KEY` (opcional), SMTP si aplica.

## Limitaciones

- Playwright E2E y Docker Compose: ver `DEUDAS-PRODUCCION.md` (**NOT_VERIFIED** en esta auditoría).
- Conteos use-case de negocio son agregados documentales, no AST.
