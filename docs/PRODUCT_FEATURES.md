# VOXMETRIKS — Product Features

**Versión:** V2 Release Candidate 1  
**Audiencia:** demo académica, beta privada, defensa de proyecto

---

## Experiencia de escucha

| Feature | Descripción |
|---------|-------------|
| Catálogo | Tracks, artistas, géneros con búsqueda y paginación |
| Reproductor | Play/pause, seek, shuffle, repeat, cola, historial previous |
| Favoritos | Globales, reactivos en toda la UI |
| Playlists | CRUD de usuario + agregar tracks |
| Cola | Reordenar, next/previous, persistencia de sesión |
| Audio | Resolver YouTube → Audius → demo local (fallback) |
| Covers | Gradientes + resolución de portadas cuando hay fuente |

---

## Personalización (Fase 4)

| Feature | Descripción |
|---------|-------------|
| Home inteligente | Secciones dinámicas por usuario |
| Discover Weekly | Playlist semanal personalizada |
| Daily Mix | Mixes por cluster (Rock/Pop/Chill/Instrumental) |
| Because you… | Rails contextuales |
| Similar tracks/artists | Cosine similarity sobre audio features |
| Audio DNA | Perfil sonoro (energía, dance, acústico…) |
| Trending | Today / week / genre / growth / saved |

---

## IA musical (Fase 6)

| Feature | Local (sin API) | Externo (opcional) |
|---------|-----------------|--------------------|
| Búsqueda natural | ✅ reglas ES/EN → filtros | — |
| Playlist por prompt | ✅ preview + confirmación | nombres más naturales |
| Explicaciones | ✅ reason codes | texto LLM |
| Mood profile | ✅ | — |
| AI DJ | ✅ bloques de texto | — |

**No es un chatbot.** La IA mejora búsqueda, descubrimiento y playlists.

---

## Analytics & datos

| Feature | Rol |
|---------|-----|
| Dashboard / KPIs | Resumen warehouse Gold |
| Explorer | Solo lectura, rol engineer |
| ELT pipeline UI | Monitoreo / disparo (engineer) |
| Stats / trending | Endpoints públicos o autenticados según ruta |

---

## Plataforma (Fase 5)

| Feature | Descripción |
|---------|-------------|
| Health / status | Warehouse, cache, jobs, recommendations |
| Notificaciones in-app | Toasts (favoritos, errores recuperables…) |
| Caché TTL | Home smart, recomendaciones, dashboards |
| Jobs background | Refresh cache, métricas (no bloquean HTTP) |
| SSE + polling | Eventos / notificaciones |

---

## Roles

| Rol | Puede |
|-----|-------|
| `user` | Escuchar, favoritos, playlists, smart, AI |
| `engineer` | Explorer, ELT, platform status/metrics |
| `admin` | Mutaciones de catálogo + todo engineer |

---

## Fuera de alcance (RC1)

- Licenciamiento musical real / DRM
- Chatbot conversacional
- App móvil nativa
- Multi-tenant SaaS
- Redis obligatorio / GPU / modelos pesados
