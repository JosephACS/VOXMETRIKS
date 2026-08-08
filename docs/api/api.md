# API Reference — VOXMETRIK_V2

**Base URL:** `http://localhost:8000`  
**OpenAPI interactivo:** `/docs` (solo en `ENVIRONMENT=development`)  
**Total endpoints montados:** 93  
**Formato éxito (Enterprise):** `{ "status": "success", "data": ..., "meta": {...} }`  
**Formato error:** `{ "status": "error", "message": "...", "details": {...} }`

---

## Health & Root

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/` | Metadatos del servicio | No |
| GET | `/health` | Salud del warehouse (legacy shape) | No |
| GET | `/api/v1/health` | Igual que `/health` | No |
| GET | `/api/v1/health/enterprise` | Health con envelope enterprise | No |

### GET `/health`

**Respuesta 200:**
```json
{
  "status": "healthy",
  "db_connected": true,
  "tables_ok": true,
  "etl_status": "ready",
  "gold_ready": true
}
```

**Errores:** 503 si DuckDB no disponible (degraded/unhealthy en body).

---

## Enterprise API — `/api/v1`

### Dashboard

#### GET `/api/v1/dashboard/overview`

| | |
|---|---|
| **Descripción** | KPIs principales: streams, usuarios, géneros, dispositivos, growth |
| **Parámetros** | Ninguno |
| **Cache** | TTL `CACHE_TTL_DASHBOARD` (default 120s) |

**Response 200:**
```json
{
  "status": "success",
  "data": {
    "total_streams": 1250000,
    "active_users": 8420,
    "top_genres": [{ "id_genero": 1, "nombre_genero": "Pop", "streams_7d": 50000, "trend_pct": 12.5 }],
    "top_artists": [{ "nombre_artista": "Artist", "streams_7d": 10000, "growth_pct": 8.2 }],
    "device_usage": [{ "platform": "mobile", "device_type": "phone", "share_pct": 45.0 }],
    "growth_trends": [{ "fecha": "2026-06-01", "total_streams": 40000, "unique_users": 1200 }]
  },
  "meta": { "count": 30, "source": "duckdb" }
}
```

### Analytics

#### GET `/api/v1/analytics/streams`

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `start_date` | date | Inicio (default: hoy − 30d) |
| `end_date` | date | Fin (default: hoy) |
| `date_from`, `date_to` | date | Alias filtros reutilizables |
| `genre`, `artist`, `platform`, `device` | string | Filtros opcionales |

**Response:** series diarias, peak_hours, trending_artists, top_genres, device_breakdown.

### Tracks

#### GET `/api/v1/tracks/top`

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `limit` | int | 20 | Máx items (modo legacy) |
| `page` | int | 1 | Paginación |
| `page_size` | int | — | Si se envía, activa paginación |
| `sort_by` | string | — | Campo orden |
| `sort_order` | asc/desc | desc | Dirección |
| `genre`, `artist`, `min_popularity` | — | — | Filtros |

**Response 200:**
```json
{
  "status": "success",
  "data": [{
    "id_track": 1,
    "nombre_track": "Track",
    "nombre_artista": "Artist",
    "popularity": 88,
    "total_streams": 15000
  }],
  "meta": { "count": 20, "limit": 20 }
}
```

#### GET `/api/v1/tracks/recommendations/{user_id}`

| Parámetro | Tipo | Descripción |
|-----------|------|-------------|
| `user_id` | path int ≥1 | Usuario objetivo |
| `limit` | query int | 1–50, default 20 |
| `page`, `page_size` | query | Paginación opcional |

**Response 200:**
```json
{
  "status": "success",
  "data": [{
    "track_id": 42,
    "score": 0.87,
    "reason": "Matches your top genre Pop",
    "track_name": "Hit Song",
    "popularity": 75,
    "engagement_score": 0.62
  }]
}
```

**Errores:** 422 si `user_id` inválido; 503 si DuckDB falla.

### Users

#### GET `/api/v1/users/{user_id}/insights`

**Response 200:** perfil de engagement del usuario.  
**404:** `{ "status": "error", "message": "User N not found" }`

---

## Modular API — `/api/v2`

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v2/dashboard/overview` | Overview V2 |
| GET | `/api/v2/dashboard/realtime` | Métricas tiempo real |
| GET | `/api/v2/dashboard/growth` | Tendencias crecimiento |
| GET | `/api/v2/dashboard/engagement` | Engagement agregado |
| GET | `/api/v2/users/status` | Estado servicio users |
| GET | `/api/v2/users/{user_id}` | Perfil usuario |
| GET | `/api/v2/users/{user_id}/activity` | Actividad reciente |
| GET | `/api/v2/stream/status` | Estado streaming |
| POST | `/api/v2/stream/start` | Iniciar sesión |
| POST | `/api/v2/stream/end` | Finalizar sesión |
| POST | `/api/v2/stream/skip` | Registrar skip |
| POST | `/api/v2/stream/pause` | Pausa |
| POST | `/api/v2/stream/resume` | Reanudar |
| GET | `/api/v2/stream/session/{user_id}/live` | Sesión activa |
| GET | `/api/v2/analytics/status` | Estado analytics |
| GET | `/api/v2/analytics/daily-streams` | Series diarias |
| GET | `/api/v2/analytics/top-artists` | Top artistas |
| GET | `/api/v2/analytics/top-tracks` | Top tracks |
| GET | `/api/v2/analytics/genres` | Distribución géneros |
| GET | `/api/v2/analytics/platform-usage` | Uso plataforma |
| GET | `/api/v2/search/status` | Estado búsqueda |
| GET | `/api/v2/search` | Búsqueda full-text |
| GET | `/api/v2/recommendations/status` | Estado motor |
| GET | `/api/v2/recommendations/{user_id}` | Recomendaciones V2 |

---

## Legacy API — `/api/v1` (packages)

### Autenticación — `/api/v1/users`

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/auth-config` | Config OAuth/SMTP | No |
| POST | `/login` | Login → Bearer token | No |
| POST | `/register` | Registro + código email | No |
| POST | `/verify-email` | Activar cuenta | No |
| POST | `/resend-code` | Reenviar código | No |
| POST | `/google` | Google Sign-In | No |
| POST | `/logout` | Invalidar sesión | Bearer |
| GET | `/me` | Perfil actual | Bearer |
| PATCH | `/me/preferences` | Preferencias UI | Bearer |

**POST `/login` — Request:**
```json
{ "login": "demo", "password": "demo123", "remember": true }
```

**Response 200:**
```json
{ "token": "abc...", "user": { "id": 1, "username": "demo", "role": "listener" } }
```

**401:** credenciales inválidas (envelope `{ status, message }`).

### Streaming — catálogo

| Grupo | Endpoints clave |
|-------|-----------------|
| **Artists** | CRUD `/artists`, `/artists/top`, `/artists/{id}/stats` |
| **Genres** | CRUD `/genres`, `/genres/stats` |
| **Tracks** | `/tracks`, `/tracks/search`, CRUD, `/detail`, `/features`, `/audio-source`, `/cover` |
| **Playlists** | CRUD + add/remove tracks |
| **Favorites** | GET/POST/DELETE `/favorites/{track_id}` |
| **Dashboard BFF** | GET `/dashboard/home` |

### Analytics legacy

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/analytics/warehouse` | Metadatos warehouse |
| GET | `/analytics/trending` | Trending tracks |
| GET | `/analytics/platform` | Uso plataforma |
| GET | `/analytics/engagement` | Engagement |
| GET | `/analytics/explorer/tables` | Listado tablas (engineer) |
| GET | `/analytics/explorer/preview/{table}` | Preview tabla |
| GET | `/analytics/history` | Historial usuario |
| GET | `/analytics/recommendations` | Recomendaciones legacy |

### Stats

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/stats/summary` | Resumen KPIs |
| GET | `/stats/top-tracks` | Top tracks stats |
| GET | `/stats/energia` | Distribución energy |
| GET | `/stats/loads` | Cargas ELT |
| POST | `/stats/import` | Import dataset (engineer) |
| POST | `/stats/synthetic` | Datos sintéticos |

---

## Códigos de error comunes

| Código | Significado |
|--------|-------------|
| 400 | ValueError / bad request |
| 401 | No autenticado |
| 403 | Sin permisos (engineer) |
| 404 | Recurso no encontrado |
| 422 | Validación Pydantic |
| 429 | Rate limit excedido |
| 503 | Error DuckDB |
| 504 | Timeout |

---

## Autenticación

```http
Authorization: Bearer <token>
```

Obtener token: `POST /api/v1/users/login`

---

## Rate limiting

- Auth: `AUTH_RATE_LIMIT` / `AUTH_RATE_WINDOW_SEC`
- Global: `GLOBAL_RATE_LIMIT` / `GLOBAL_RATE_WINDOW_SEC`

Ver [security.md](../security/security.md).
