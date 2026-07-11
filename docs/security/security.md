# Security — Seguridad

## Modelo de amenazas (resumen)

| Amenaza | Mitigación |
|---------|------------|
| SQL Injection | Queries parametrizadas; validación SQL en DuckDBClient |
| XSS | Angular sanitization; headers CSP-friendly |
| CSRF | Bearer token (no cookies de sesión cross-site) |
| Brute force login | Rate limit auth (`AUTH_RATE_LIMIT`) |
| API abuse | Rate limit global (`GLOBAL_RATE_LIMIT`) |
| Info disclosure | Sin stack traces en producción |
| CORS misconfig | Wildcard bloqueado en prod |

## Autenticación

- **Mecanismo:** Bearer token en header `Authorization`
- **Almacenamiento:** `app_session` en DuckDB
- **Passwords:** bcrypt (cost factor 12)
- **Demo users:** Deshabilitados en `ENVIRONMENT=production`
- **Google OAuth:** Verificación ID token con `GOOGLE_CLIENT_ID`
- **Email verification:** Código 6 dígitos, TTL configurable

## Autorización (RBAC)

| Rol | Acceso |
|-----|--------|
| `listener` | Catálogo, favoritos, playlists propias |
| `engineer` | Explorer, ELT pipeline, stats import |

Guard frontend: `engineerGuard` en rutas `/elt-pipeline`, `/explorer`.

## Headers de seguridad

Middleware `SecurityHeadersMiddleware`:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Strict-Transport-Security` (solo producción)

## CORS

```env
CORS_ORIGINS=http://localhost:4200,https://app.example.com
```

En producción, `*` se trata como lista vacía (deny all cross-origin).

## Rate limiting

| Scope | Default | Config |
|-------|---------|--------|
| Auth endpoints | 20/min | `AUTH_RATE_LIMIT` |
| Global API | 120/min | `GLOBAL_RATE_LIMIT` |

Respuesta 429:
```json
{ "status": "error", "message": "Too many requests. Try again later." }
```

## Validación de inputs

- Pydantic en todos los body/query models
- Path params con `ge=1` donde aplica
- SQL: regex anti-DDL en `DuckDBClient._validate_sql`
- Longitud máxima en filtros (`max_length=120`)

## Secretos

| Variable | Uso |
|----------|-----|
| `SECRET_KEY` | Firma interna |
| `SMTP_PASSWORD` | Email |
| `POCKETBASE_PASSWORD` | ETL |
| `YOUTUBE_API_KEY` | Playback |
| `GOOGLE_CLIENT_ID` | OAuth |

**Nunca commitear `.env`** — está en `.gitignore`.

## Producción hardening

| Feature | Dev | Prod |
|---------|-----|------|
| `/docs`, `/redoc` | ✅ | ❌ |
| Demo users seed | ✅ | ❌ |
| Dev verification codes in API | ✅ | ❌ |
| Stack traces in errors | ✅ | ❌ |
| HSTS header | ❌ | ✅ |

## Recomendaciones futuras

- JWT con refresh tokens
- OAuth2 PKCE completo
- WAF / reverse proxy (Cloudflare)
- Secrets manager (Vault, AWS SM)
- Audit log export a SIEM

Ver [faq.md](../01-introduction/faq.md) para preguntas de defensa.
