# VOXMETRIKS V2 — Release Notes

## Release Candidate 1 (RC1)

**Fecha:** 2026-07-10  
**Nombre:** VOXMETRIKS V2 — Release Candidate 1  
**Tipo:** Beta privada / demo pública controlada

---

## Resumen del producto

Plataforma de streaming musical con analytics enterprise: reproducción profesional, recomendaciones inteligentes, IA musical con fallback local, observabilidad básica y warehouse DuckDB Medallion.

---

## Stack

| Capa | Tecnología |
|------|------------|
| Frontend | Angular 21, RxJS, Material/CDK, ECharts, Vitest |
| Backend | FastAPI 0.111, Pydantic v2, Python 3.12 |
| Datos | DuckDB 1.1, Medallion ELT |
| Audio | YouTube Data API (opcional), Audius, demo local |
| IA | Rule-based local + LLM OpenAI-compatible opcional |
| Ops | Docker Compose, Makefile, GitHub Actions CI opcional |

---

## Módulos principales

1. **Streaming UX** — catálogo, player, cola, favoritos, playlists  
2. **Audio Resolver** — multiproveedor con caché  
3. **Smart Engine** — home, mixes, similitud, Audio DNA  
4. **VOXMETRIKS AI** — NL search, playlist prompt, explain, DJ  
5. **Enterprise Platform** — health, notificaciones, jobs, caché  
6. **Analytics / ELT** — Gold tables, explorer, pipeline  

---

## Cómo levantarlo

```bash
# Docker (API)
make up

# Local
make install && make pipeline && make dev
cd apps/frontend && npm install && npm start
```

Guía: [QUICKSTART.md](QUICKSTART.md)

---

## Credenciales demo (solo development)

| Usuario | Password | Rol |
|---------|----------|-----|
| `demo` / `demo@voxmetrik.io` | `demo123` | user |
| `admin` / `admin@voxmetrik.io` | `admin123` | admin |
| `engineer` (si seeded) | `engineer123` | engineer |

En `ENVIRONMENT=production` no se siembran usuarios demo.

---

## Funcionalidades incluidas en RC1

- Login / logout / registro / Google Sign-In opcional  
- Reproducción completa + persistencia de sesión  
- Favoritos, playlists, cola  
- Audio resolver con fallback  
- Home personalizada + Discover Weekly + Daily Mix  
- Búsqueda natural y playlist por IA (confirmación manual)  
- Notificaciones toast  
- Health + platform status (engineer)  
- Dashboards y explorer (según rol)  

---

## Limitaciones conocidas

| Limitación | Notas |
|------------|-------|
| Bundle inicial ~629 kB | Sobre budget 550 kB — warning, no bloquea build |
| CSS Home sobre budget | Warning cosmético |
| Lint FE | 0 errores, 13 warnings (exit 0) |
| `/api/v2` | Montado; el FE consume `/api/v1` |
| Audio real | Depende de `YOUTUBE_API_KEY`; sin key → demo/Audius |
| IA externa | Opcional; sin key todo funciona en local rules |
| Caché / rate limit | In-process (no Redis) — un worker local |
| Docker / Playwright | Validar en entorno con Docker y browsers instalados |

---

## Pendientes post-RC (no bloquean demo)

- Redis opcional  
- WebSocket autenticado  
- Unificar o documentar deprecación `/api/v2`  
- Reducir bundle / CSS budgets  
- Limpiar `console.error` residuales en FE  
- Auth en algunas rutas enterprise legacy  

---

## Validación RC1 (ejecutada)

| Check | Resultado |
|-------|-----------|
| `pytest` (platform, AI, smart, auth, production_infra) | **PASS** (30 tests) |
| `npm run test` (frontend) | **PASS** (53 tests) |
| `npm run build` | **PASS** (con warnings de budget) |
| `npm run lint` | **PASS** — 0 errores, 13 warnings |
| Playwright E2E | **No ejecutado** en este entorno (requiere browsers + API/FE up) |
| `docker compose` | **No disponible** en el host de validación |

---

## Documentación RC

- [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md)  
- [PRODUCT_FEATURES.md](PRODUCT_FEATURES.md)  
- [ROADMAP.md](ROADMAP.md)  
- [FINAL_PRODUCT_AUDIT.md](FINAL_PRODUCT_AUDIT.md)  
