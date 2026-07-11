# VOXMETRIKS OMEGA REVIEW

**Clasificación:** CONFIDENCIAL — Comité de destrucción técnica  
**Fecha:** 2026-07-10  
**Premisa de evaluación:** el sistema será usado por **millones de usuarios concurrentes**  
**Veredicto unánime:** **NO APTO PARA PRODUCCIÓN A ESCALA.** Es un prototipo académico con branding de producto.

---

## Panel

| Rol | Perspectiva dominante |
|-----|------------------------|
| CTO Spotify | Catálogo, playback, derechos, recomendaciones a escala |
| Principal Engineer Netflix | Disponibilidad, isolation, failure domains |
| Senior UX Designer Apple | Claridad, honestidad de producto, craft |
| Staff Engineer Google | Latencia, fan-out, data correctness |
| Product Manager Notion | Propuesta de valor, roadmap mentiroso |
| Security Engineer Cloudflare | Superficie de ataque, authz, abuse |
| DevOps Lead GitHub | Deploy, observability, operabilidad |
| AI Engineer OpenAI | Claims vs realidad de “IA” |

**Regla del comité:** no se concede el beneficio de la duda. Si no escala, no existe.

---

## 0. Sentencia ejecutiva

VOXMETRIKS confunde **demo local** con **plataforma**.

- Un solo archivo DuckDB no es un warehouse de producto.
- Un solo worker Uvicorn no es un backend.
- Rate limit / cache / notificaciones / SSE en memoria de proceso no son “enterprise”.
- yt-dlp + iframe YouTube no es un audio stack legal.
- Heurísticas con nombre “AI” no son inteligencia artificial de producto.
- Documentar “RC1 listo para beta” mientras analytics enterprise están **sin autenticación** es negligencia de release.

Si mañana abrís esto a un millón de usuarios, el sistema colapsa en minutos: un write cierra el read pool, el boot puede bloquear la API hasta una hora, y cualquiera puede leer insights de usuarios por ID en rutas públicas.

---

# 1. ARQUITECTURA

### P1 — Single-file DuckDB como sistema de registro
| | |
|--|--|
| **Gravedad** | Crítica |
| **Impacto** | Imposible multi-región, multi-AZ, multi-tenant, HA |
| **Por qué está mal** | Un archivo + un writer. Los writes liberan/reabren el read connection (`database.py`). Lecturas serializadas con un mutex global. Compose fuerza `--workers 1`. |
| **Cómo lo haría Spotify** | OLTP (Postgres/Spanner) + serving stores (Cassandra/Bigtable) + warehouse analítico separado (BigQuery/Snowflake). Nunca el mismo archivo para auth, favoritos y agregados Gold. |
| **Prioridad** | P0 — sin esto no hay producto |

### P2 — Tres APIs en un proceso (enterprise v1 + packages v1 + v2)
| | |
|--|--|
| **Gravedad** | Alta |
| **Impacto** | Contratos divergentes, auth inconsistente, doble mantenimiento |
| **Por qué está mal** | `main.py` monta enterprise, legacy packages y `/api/v2` con dos stacks DuckDB (`database.py` vs `duckdb_client.py`). OpenAPI se contradice a sí mismo. |
| **Cómo lo haría Netflix** | Un edge API gateway, un contrato versionado, deprecación con fecha. Un solo data access layer. |
| **Prioridad** | P0 |

### P3 — Dominios acoplados al mismo proceso y al mismo DB file
| | |
|--|--|
| **Gravedad** | Alta |
| **Impacto** | Blast radius total: un job ELT tumba el player |
| **Por qué está mal** | Auth, streaming, analytics, AI, platform jobs y ETL comparten proceso y warehouse. |
| **Cómo lo haría Google** | Bounded contexts + stores dedicados + async boundaries. Playback nunca espera a analytics. |
| **Prioridad** | P0 |

### P4 — Estado “enterprise” en memoria de proceso
| | |
|--|--|
| **Gravedad** | Crítica |
| **Impacto** | Horizontal scale = mentira |
| **Por qué está mal** | Cache, rate limit, notifications, SSE hub son dicts/deques locales. Segundo pod = otro universo. SSE: segundo subscribe del mismo user **sobrescribe** el primero (`realtime/hub.py`). |
| **Cómo lo haría Cloudflare** | Edge + Redis/KV + pub/sub. Rate limit global. Eventos fan-out con Durable Objects / Kafka. |
| **Prioridad** | P0 |

---

# 2. BACKEND

### P5 — Auth: sesiones opacas en DuckDB, SECRET_KEY decorativo
| | |
|--|--|
| **Gravedad** | Crítica |
| **Impacto** | Cada request autenticado pelea por el warehouse; no hay firma criptográfica de token |
| **Por qué está mal** | UUID en `app_session`. `SECRET_KEY` existe en config y **no se usa**. Revocación y lookup son SQL contra el cuello de botella. |
| **Cómo lo haría Spotify** | JWT/OAuth2 + session store Redis + short-lived access tokens + refresh rotation. Warehouse fuera del hot path de auth. |
| **Prioridad** | P0 |

### P6 — Rutas enterprise / v2 sin autenticación
| | |
|--|--|
| **Gravedad** | Crítica (seguridad) |
| **Impacto** | Filtración de KPIs, streams, insights por `user_id` |
| **Por qué está mal** | `dashboards.py`, `enterprise_analytics.py`, `enterprise_users.py`, tracks top/recommendations enterprise, y rutas v2 **sin** `require_*`. |
| **Cómo lo haría Cloudflare** | Deny-by-default. Authn + Authz en gateway. Tests que fallen el PR si un route queda público por accidente. |
| **Prioridad** | P0 — hotfix inmediato |

### P7 — Boot bloqueante con ETL hasta 3600s
| | |
|--|--|
| **Gravedad** | Alta |
| **Impacto** | Cold start = API muerta; healthcheck mentiroso; deploys peligrosos |
| **Por qué está mal** | `run_system_boot()` en lifespan; legacy ETL timeout 1h. Docker `RUN_ETL_ON_BOOT=auto`. |
| **Cómo lo haría GitHub/Netflix** | Jobs asíncronos, readiness vs liveness separados, pipeline en workers, nunca en el request path ni en el boot del API. |
| **Prioridad** | P0 |

### P8 — Helpers SQL con `WHERE {where}` concatenado
| | |
|--|--|
| **Gravedad** | Alta |
| **Impacto** | Una llamada incorrecta = inyección |
| **Por qué está mal** | `query_helpers.py` / `safe_query` construyen SQL por string. Explorer usa `f'SELECT * FROM "{table}"'`. AI search parametriza valores pero no es el patrón global. |
| **Cómo lo haría Google** | Query builders tipados, prepared statements only, allowlists formales, fuzzing de inputs. |
| **Prioridad** | P1 |

### P9 — “Background jobs” que no son un sistema de jobs
| | |
|--|--|
| **Gravedad** | Media-Alta |
| **Impacto** | Sin retry, sin DLQ, sin idempotencia, sin observabilidad de cola |
| **Por qué está mal** | Loop asyncio en el mismo proceso API. Pierde todo al reiniciar. |
| **Cómo lo haría Netflix** | Temporal/Cadence/SQS + workers. Exactly-once o at-least-once documentado. |
| **Prioridad** | P1 |

---

# 3. FRONTEND

### P10 — Bundle inicial ~629 kB sobre budget
| | |
|--|--|
| **Gravedad** | Alta (UX móvil / mercados emergentes) |
| **Impacto** | TTI pobre; Material + ECharts en el camino crítico |
| **Por qué está mal** | Lazy routes no compensan dependencias pesadas en shell. |
| **Cómo lo haría Apple/Google** | Code-split agresivo, design system ligero, charts on-demand, performance budgets que **rompen CI**. |
| **Prioridad** | P1 |

### P11 — N+1 de covers en Home y rails
| | |
|--|--|
| **Gravedad** | Alta |
| **Impacto** | Decenas/cientos de HTTP por viewport; thundering herd al API |
| **Por qué está mal** | `home.component.ts` hace `forEach` → `resolveCover`. MediaCard/TrackRow piden cover por id. Sin batch endpoint. |
| **Cómo lo haría Spotify** | Batch `/covers?ids=` o URLs firmadas en el payload de lista. CDN. |
| **Prioridad** | P0 para escala |

### P12 — Dualidad features/ vs packages/
| | |
|--|--|
| **Gravedad** | Media |
| **Impacto** | UX inconsistente, deuda, rutas confusas |
| **Por qué está mal** | Dos mundos de UI (insights vs streaming packages) sin un design system único. |
| **Cómo lo haría Notion** | Un solo surface model. Un design system. Matar duplicados. |
| **Prioridad** | P1 |

### P13 — `console.error` como “observabilidad” de cliente
| | |
|--|--|
| **Gravedad** | Media |
| **Impacto** | Cero telemetría de producto; ruido en prod |
| **Por qué está mal** | Errores van a consola, no a un pipeline de crash/analytics. |
| **Cómo lo haría GitHub** | Sentry/RUM + structured client events + privacy scrubbing. |
| **Prioridad** | P2 |

---

# 4. UX

### P14 — Producto que miente sobre lo que es
| | |
|--|--|
| **Gravedad** | Crítica (confianza) |
| **Impacto** | Expectativa Spotify/Apple Music; entrega demo + heurística |
| **Por qué está mal** | “IA”, “Enterprise”, “Release Candidate”, “plataforma inteligente” sobre reglas locales y un DuckDB. |
| **Cómo lo haría Apple** | Naming honesto. “Academic streaming analytics demo” hasta que el stack lo merezca. |
| **Prioridad** | P0 de producto |

### P15 — Home sobrecargada: analytics + smart + DNA + rails
| | |
|--|--|
| **Gravedad** | Alta |
| **Impacto** | Primera viewport no es una composición musical; es un dashboard |
| **Por qué está mal** | Compite con el job del usuario: escuchar. KPIs y charts en el feed de consumo. |
| **Cómo lo haría Spotify/Apple** | Home = play. Analytics = superficie separada. |
| **Prioridad** | P1 |

### P16 — Estados vacíos / errores / loaders inconsistentes
| | |
|--|--|
| **Gravedad** | Media |
| **Impacto** | Sensación de app incompleta bajo fallo de red |
| **Por qué está mal** | Patrones por componente; toasts nuevos no unifican error UX. |
| **Cómo lo haría Notion** | Sistema de estados: empty / loading / error / offline con copy y recovery. |
| **Prioridad** | P2 |

### P17 — Credenciales demo todavía en copy i18n
| | |
|--|--|
| **Gravedad** | Media (seguridad + profesionalismo) |
| **Impacto** | Builds “prod” siguen enseñando passwords de seed |
| **Por qué está mal** | Hardening vació el form; el hint sigue publicando `demo123` / `admin123`. |
| **Cómo lo haría Cloudflare** | Zero credentials in client bundles. Docs internas only. |
| **Prioridad** | P1 |

---

# 5. PLAYER / AUDIO

### P18 — Catálogo sin derechos + yt-dlp como “resolver”
| | |
|--|--|
| **Gravedad** | Existencial (legal) |
| **Impacto** | No se puede operar comercialmente; riesgo de takedown |
| **Por qué está mal** | `youtube_provider.py` busca con yt-dlp. No hay licencias. Audius/demo no cubren un catálogo Spotify-scale. |
| **Cómo lo haría Spotify** | Acuerdos de label, ISRC, delivery pipelines, DRM donde aplique. Nunca scrapear YouTube para servir millones. |
| **Prioridad** | P0 legal — bloquea “producto internacional” |

### P19 — Iframe YouTube 1×1 como motor de playback
| | |
|--|--|
| **Gravedad** | Alta |
| **Impacto** | Controles frágiles, UX no nativa, dependencia de terceros, ToS gris |
| **Por qué está mal** | Player “profesional” montado sobre un embed oculto. Buffering/seek/errores son de segunda clase. |
| **Cómo lo haría Spotify** | Media stack propio o partners licenciados; CDN de audio; client robusto. |
| **Prioridad** | P0 para producto real |

### P20 — Cola/favoritos/sesión en cliente sin sync multi-device
| | |
|--|--|
| **Gravedad** | Alta a escala |
| **Impacto** | Experiencia “Spotify” rota entre dispositivos |
| **Por qué está mal** | Persistencia localStorage/session; favoritos sí van a API, cola no es un servicio de sync. |
| **Cómo lo haría Spotify** | Playback state service + presence + conflict resolution. |
| **Prioridad** | P1 |

---

# 6. ELT / WAREHOUSE / ANALYTICS

### P21 — Medallion en el mismo archivo que OLTP de app
| | |
|--|--|
| **Gravedad** | Crítica |
| **Impacto** | Contención I/O; analytics mata streaming |
| **Por qué está mal** | `dim_*`, `fact_*`, `agg_*`, `app_*` conviven. |
| **Cómo lo haría Netflix/Google** | Serving DB ≠ analytical warehouse. ETL a store analítico; serving lee materializaciones/API. |
| **Prioridad** | P0 |

### P22 — Gold “enterprise” sin SLO ni lineage operativo
| | |
|--|--|
| **Gravedad** | Alta |
| **Impacto** | Números incorrectos sin alarma; defensa académica ≠ ops |
| **Por qué está mal** | Validación básica; no hay data contracts, freshness SLAs, o ownership. |
| **Cómo lo haría Google** | Data contracts, monitors, freshness, column lineage, on-call. |
| **Prioridad** | P1 |

### P23 — Explorer como SQL UI cerca de datos sensibles
| | |
|--|--|
| **Gravedad** | Alta |
| **Impacto** | Fuga por allowlist incompleta / redaction estrecha |
| **Por qué está mal** | Blocklist parcial; preview genérico; dependencia de disciplina humana. |
| **Cómo lo haría Cloudflare** | Least privilege, row-level security, audit log, no DESCRIBE libre. |
| **Prioridad** | P0 |

### P24 — Dashboards que pueden full-scan mentalidad “agg_*”
| | |
|--|--|
| **Gravedad** | Media-Alta |
| **Impacto** | Bajo carga, queries pesadas en el mismo DB del player |
| **Por qué está mal** | Caché in-process no salva multi-user cold cache. |
| **Cómo lo haría Spotify** | Pre-aggregates en serving cache (Redis), CDN, o BI separado. |
| **Prioridad** | P1 |

---

# 7. IA

### P25 — Naming fraudulento: “AI” = if/else + cosine
| | |
|--|--|
| **Gravedad** | Crítica (integridad de producto) |
| **Impacto** | Expectativa de modelo; realidad `nl_search.py` keyword table |
| **Por qué está mal** | `LocalRuleBasedAIProvider`, recommendation engine documentado “No ML”, AI DJ = narraciones fijas. External LLM opcional y no default. |
| **Cómo lo haría OpenAI** | Separar: (1) rules, (2) classical ML, (3) LLM. Etiquetar en UI el provider. Evaluaciones. No vender reglas como “IA”. |
| **Prioridad** | P0 de honestidad |

### P26 — Sin evaluación, sin offline metrics, sin A/B
| | |
|--|--|
| **Gravedad** | Alta |
| **Impacto** | No sabés si las recomendaciones ayudan |
| **Por qué está mal** | Tests unitarios de cosine ≠ NDCG, diversity, skip-rate. |
| **Cómo lo haría Spotify/OpenAI** | Offline eval + online experiments + guardrails. |
| **Prioridad** | P1 |

### P27 — `POST /ai/search/natural` sin auth
| | |
|--|--|
| **Gravedad** | Alta |
| **Impacto** | Abuse / scraping del catálogo vía “IA” |
| **Por qué está mal** | Endpoint público sobre warehouse. |
| **Cómo lo haría Cloudflare** | Auth + rate limit por usuario + WAF. |
| **Prioridad** | P0 |

### P28 — Sin embeddings reales / sin retrieval layer
| | |
|--|--|
| **Gravedad** | Media (si se aspira a “internacional”) |
| **Impacto** | “Similar” es toy-scale O(n) sobre 400 tracks |
| **Por qué está mal** | Similarity engine limita candidatos por popularity; no ANN index. |
| **Cómo lo haría Spotify** | Embedding service + ANN (ScaNN/Faiss) + two-tower / session models. |
| **Prioridad** | P2 (después de datos y derechos) |

---

# 8. DOCUMENTACIÓN

### P29 — Docs de victoria vs realidad operativa
| | |
|--|--|
| **Gravedad** | Alta |
| **Impacto** | Stakeholders creen que hay “enterprise platform” |
| **Por qué está mal** | `FINAL_PRODUCT_AUDIT.md` dice beta seria; este review demuestra single-worker + rutas abiertas. |
| **Cómo lo haría Notion/GitHub** | Docs con “known non-goals”, threat model, scale limits en la primera página. |
| **Prioridad** | P0 |

### P30 — Documentación contradictoria / legacy paths
| | |
|--|--|
| **Gravedad** | Media |
| **Impacto** | Onboarding roto; deploys mal hechos |
| **Por qué está mal** | Histórico de `backend/` vs `apps/backend/`, docker profiles, FAQ links rotos. |
| **Cómo lo haría GitHub** | Una sola source of truth; links chequeados en CI. |
| **Prioridad** | P2 |

---

# 9. SEGURIDAD

### P31 — Superficie pública de analytics
| | |
|--|--|
| **Gravedad** | Crítica |
| **Impacto** | Data leak |
| **Prioridad** | P0 — ver P6 |

### P32 — Rate limit per-process / per-IP trivial
| | |
|--|--|
| **Gravedad** | Alta |
| **Impacto** | Bypass con N IPs o N workers (si algún día los hay) |
| **Por qué está mal** | Sliding window en dict local. |
| **Cómo lo haría Cloudflare** | Edge rate limiting + bot management + token bucket distribuido. |
| **Prioridad** | P0 a escala |

### P33 — Passwords demo en seeds + hints
| | |
|--|--|
| **Gravedad** | Media-Alta |
| **Impacto** | Compromiso trivial si `ENVIRONMENT` mal seteado |
| **Cómo lo haría Cloudflare** | No seeds en prod images; secrets manager; break-glass accounts. |
| **Prioridad** | P1 |

### P34 — Sin threat model, sin audit log, sin WAF assumptions
| | |
|--|--|
| **Gravedad** | Alta |
| **Impacto** | Incident response imposible |
| **Prioridad** | P1 |

---

# 10. ESCALABILIDAD

### P35 — Hard ceiling: 1 proceso, 1 archivo, 1 writer
| | |
|--|--|
| **Gravedad** | Existencial |
| **Impacto** | Millones de usuarios = fantasía |
| **Prioridad** | P0 |

### P36 — Fan-out de covers + smart home sin CDN
| | |
|--|--|
| **Gravedad** | Alta |
| **Impacto** | API como CDN accidental |
| **Prioridad** | P0 |

### P37 — Sin multi-tenant isolation
| | |
|--|--|
| **Gravedad** | Crítica para SaaS |
| **Impacto** | Un “producto internacional” B2B es imposible |
| **Prioridad** | P1 (después de split de stores) |

---

# 11. MANTENIBILIDAD

### P38 — Complejidad accidental de dual-stack
| | |
|--|--|
| **Gravedad** | Alta |
| **Impacto** | Cada feature se implementa 2–3 veces o se olvida un path |
| **Prioridad** | P0 |

### P39 — Tests que no miden producción
| | |
|--|--|
| **Gravedad** | Alta |
| **Impacto** | 53 vitest + subset pytest ≠ load, chaos, contract, security tests |
| **Por qué está mal** | Playwright no corre en el entorno RC; no hay k6/locust; no hay authz regression suite completa. |
| **Cómo lo haría Google** | Test pyramid + load gates + canaries. |
| **Prioridad** | P1 |

### P40 — “Fases” como arquitectura
| | |
|--|--|
| **Gravedad** | Media |
| **Impacto** | El código crece por narrativa de fase, no por boundaries de dominio limpios |
| **Prioridad** | P2 |

---

# 12. PRODUCTO

### P41 — No hay moat ni modelo de negocio realista
| | |
|--|--|
| **Gravedad** | Existencial |
| **Impacto** | Sin derechos de música no hay streaming comercial |
| **Cómo lo haría Spotify PM** | O sos analytics sobre datos licenciados, o sos cliente de un DSP API, o sos research demo. Elegí uno. |
| **Prioridad** | P0 estratégico |

### P42 — Mezcla tres productos en uno
| | |
|--|--|
| **Gravedad** | Alta |
| **Impacto** | Ninguno es excelente |
| **Por qué está mal** | Consumer music app + data engineering IDE + “AI lab” en la misma SPA. |
| **Cómo lo haría Notion** | Un job-to-be-done. El resto es módulo o producto separado. |
| **Prioridad** | P0 de foco |

### P43 — Roadmap que salta a multi-tenant/cloud sin cimientos
| | |
|--|--|
| **Gravedad** | Media |
| **Impacto** | Desperdicio de ingeniería |
| **Prioridad** | P1 — reescribir roadmap desde P0 técnicos |

---

# 13. CÓDIGO

### P44 — Abstracciones “enterprise” sobre estructuras toy
| | |
|--|--|
| **Gravedad** | Alta |
| **Impacto** | Falsa sensación de madurez |
| **Ejemplos** | `PlatformStatusService`, `NotificationStore`, `EventHub`, `AIProvider` — correctos como interfaces, insuficientes como implementación. |
| **Prioridad** | P1 |

### P45 — Inconsistencia de authz entre capas
| | |
|--|--|
| **Gravedad** | Crítica |
| **Impacto** | FE cree que hay roles; BE enterprise no los aplica |
| **Prioridad** | P0 |

---

# 14. PERFORMANCE

### P46 — Mutex global de lectura = anti-throughput
| | |
|--|--|
| **Gravedad** | Crítica |
| **Impacto** | Concurrencia ≈ 1 query a la vez por proceso |
| **Prioridad** | P0 |

### P47 — Smart home compone demasiado en request
| | |
|--|--|
| **Gravedad** | Alta |
| **Impacto** | Latencia p99 explosiva cuando se “personaliza” |
| **Por qué está mal** | Profile + rank + discover + mixes + because + trending (+ AI widgets) en un GET. Cache in-process no es CDN. |
| **Cómo lo haría Spotify** | Home composition async precomputed por usuario; edge cache; stale-while-revalidate. |
| **Prioridad** | P0 |

### P48 — Sin profiling / sin budgets de latencia en CI
| | |
|--|--|
| **Gravedad** | Media |
| **Impacto** | Regresiones invisibles |
| **Prioridad** | P2 |

---

# MATRIZ DE PRIORIDADES (TOP 15 PARA NO MORIR)

| # | Problema | Prioridad |
|---|----------|-----------|
| 1 | Authz en enterprise/v2/AI search | P0 hotfix |
| 2 | Separar OLTP de warehouse | P0 |
| 3 | Matar single-worker/single-file como “prod” | P0 |
| 4 | Estado distribuido (Redis/NATS) | P0 |
| 5 | Derechos / audio legal | P0 legal |
| 6 | Unificar API (una superficie) | P0 |
| 7 | Boot sin ETL bloqueante | P0 |
| 8 | Batch covers + CDN | P0 |
| 9 | Honestidad de naming IA/Enterprise | P0 producto |
| 10 | Auth tokens fuera de DuckDB | P0 |
| 11 | Home composition precompute | P1 |
| 12 | Job system real | P1 |
| 13 | Bundle / performance budgets en CI | P1 |
| 14 | Eval de recomendaciones | P1 |
| 15 | Threat model + audit logs | P1 |

---

# ROADMAP: DE PROTOTIPO A PRODUCTO INTERNACIONAL

Este roadmap **no** es el de “añadir PWA y multi-tenant”. Es el único camino creíble. Cada fase es un gate: si no se cumple, no se avanza.

## Gate 0 — Stop the bleeding (2–4 semanas)

**Objetivo:** dejar de mentir y dejar de sangrar datos.

1. Autenticar **todas** las rutas `/api/v1/dashboard`, `/analytics`, enterprise users, v2, AI search. Tests de regresión authz.
2. Quitar passwords del bundle i18n en builds production.
3. Separar readiness: API up sin ETL; ETL en job aparte.
4. Documento público: “Academic demo — not production scale” hasta Gate 3.
5. Inventario de datos sensibles + cerrar explorer a allowlist mínima.

**Exit criteria:** scan automatizado 0 endpoints sensibles públicos; boot API < 30s sin warehouse rebuild.

---

## Gate 1 — Foundations (2–3 meses)

**Objetivo:** arquitectura que sobreviva a 10k usuarios concurrentes (aún no millones).

1. **Postgres** (o equivalente) para users, sessions, favorites, playlists, playback state.
2. DuckDB **solo** analytics offline / batch; o migrar analytics a warehouse cloud.
3. Redis: sessions, rate limit, cache, pub/sub notificaciones.
4. API única versionada; deprecar v2 o enterprise duplicado.
5. Workers ≥2 detrás de load balancer; sticky sessions prohibidas como requisito.
6. Object storage + CDN para covers; endpoint batch.
7. Observabilidad: OpenTelemetry + logs estructurados + error tracking.

**Exit criteria:** load test 1k RPS lectura catálogo p95 < 200ms; write favorites no tumba reads.

---

## Gate 2 — Real media product (3–6 meses)

**Objetivo:** dejar de ser un scraper con UI bonita.

1. Decisión de negocio irreversible:
   - **A)** Analytics-only sobre dataset licenciado / sintético (sin pretender DSP), o
   - **B)** Integración oficial con DSP APIs (Spotify Web API, etc.) como cliente, o
   - **C)** Catálogo propio con contratos legales.
2. Eliminar yt-dlp del path de producción.
3. Player sobre fuentes licenciadas; telemetría de playback (starts, skips, completion).
4. Sync multi-device de cola/estado.
5. Home consumer limpia; analytics en app “Studio”.

**Exit criteria:** counsel legal aprueba el audio path; 0 dependencia de scrape en prod.

---

## Gate 3 — Intelligence that is real (3–6 meses en paralelo a Gate 2)

**Objetivo:** IA/ML con evaluación, no marketing.

1. Renombrar UI: “Smart rules” vs “Model-powered” según provider.
2. Feature store + embeddings + ANN retrieval.
3. Offline metrics (NDCG, recall@k, diversity) + online A/B.
4. LLM solo para copy/explain con sanitizer, budget, y fallback obligatorio (ya existe la idea; falta ops).
5. Precompute home rails por usuario (batch + nearline).

**Exit criteria:** experimento A/B con lift medible en engagement; docs de eval públicas internas.

---

## Gate 4 — International scale (6–12 meses)

**Objetivo:** millones de usuarios.

1. Multi-región active-active o active-passive con RPO/RTO definidos.
2. Multi-tenant con isolation (schemas / cell architecture).
3. Edge caching de catálogo y home fragments.
4. Chaos testing, capacity planning, error budgets.
5. Compliance (GDPR, CCPA), DRM/licensing ops, abuse desk.
6. Mobile clients (o PWA serio) solo después de Gates 1–3.

**Exit criteria:** 99.9%+ availability SLO; runbooks; on-call; pen-test pasado.

---

## Anti-roadmap (PROHIBIDO hasta Gate 2)

- “App desktop”
- “Monetización”
- “Multi-tenant SaaS”
- “IA avanzada / radio IA”
- “Rebrand enterprise”
- Más fases de features sobre DuckDB single-file

Construir castillos sobre arena no es ambición. Es desperdicio.

---

# VEREDICTOS POR MIEMBRO DEL PANEL

| Miembro | Veredicto en una frase |
|---------|------------------------|
| **CTO Spotify** | Sin derechos y sin media stack propio, no es un competidor: es un PowerPoint ejecutable. |
| **Principal Netflix** | Un solo failure domain. Un write apaga las lecturas. Inaceptable. |
| **UX Apple** | La interfaz promete magia; el sistema entrega heurística. Eso es deshonestidad de diseño. |
| **Staff Google** | N+1 covers + mutex global = anti-patrón de latencia. |
| **PM Notion** | Tres productos, cero foco, roadmap de fantasía. |
| **Security Cloudflare** | Analytics sin auth en 2026 es imperdonable. Ship hotfix o apagad el servicio. |
| **DevOps GitHub** | ETL en boot + workers=1 + estado en memoria = no deployable. |
| **AI OpenAI** | Llamarlo AI sin eval ni modelo es marketing. Las reglas locales están bien; el nombre no. |

---

# CONCLUSIÓN

VOXMETRIKS, medido como **demo académica / portafolio**, puede existir.

VOXMETRIKS, medido como **producto internacional para millones de usuarios**, **fracasa en arquitectura, seguridad, legalidad de audio, escala, honestidad de IA y operabilidad**.

El camino no es “Fase 8 de features”.  
El camino es **Gate 0 → Gate 4**: sangrado, cimientos, media legal, inteligencia real, escala.

Hasta entonces, cada badge de “Enterprise”, “RC1” o “AI” es una deuda de credibilidad.

---

*Documento generado por el comité OMEGA. Sin elogios. Sin concesiones. Sin permiso para fingir que esto ya es Spotify.*
