# 046 — Data model

## Extensión `ensure_artist_tables`

Añadir a `ARTISTS_TABLES` y crear:

### `app_artist_membership`

| Columna | Tipo | Notas |
|---------|------|-------|
| id | INTEGER PK | |
| artist_profile_id | INTEGER NOT NULL | → app_artist_profile |
| user_id | INTEGER NOT NULL | → app_user |
| role | VARCHAR | CHECK IN (`owner`,`administrator`,`member`,`reader`) |
| status | VARCHAR | CHECK IN (`active`,`revoked`) |
| created_at, updated_at | TIMESTAMP | |
| revoked_at | TIMESTAMP NULL | |

Índices: `user_id`, `artist_profile_id`, `(user_id, status)`.

### `app_artist_access_request`

| Columna | Tipo | Notas |
|---------|------|-------|
| id | INTEGER PK | |
| applicant_user_id | INTEGER NOT NULL | |
| request_type | VARCHAR | `claim_ownership` / `request_access` / `create_new` |
| target_artist_profile_id | INTEGER NULL | |
| warehouse_artist_id | INTEGER NULL | |
| proposed_display_name | VARCHAR NULL | create_new |
| proposed_role | VARCHAR | default `member` (request_access) |
| status | VARCHAR | `pending`/`approved`/`rejected`/`cancelled` |
| created_at, reviewed_at | TIMESTAMP | |
| reviewer_user_id | INTEGER NULL | |
| rejection_reason | VARCHAR NULL | |

Índices: `applicant_user_id`, `status`.

### `app_artist_invitation`

Espejo de org invitation:

| Columna | Tipo |
|---------|------|
| id | INTEGER PK |
| artist_profile_id | INTEGER NOT NULL |
| email_normalized | VARCHAR NOT NULL |
| token_hash | VARCHAR NOT NULL |
| role | VARCHAR (`administrator`/`member`/`reader`) |
| status | `pending`/`accepted`/`expired`/`revoked` |
| expires_at | TIMESTAMP |
| invited_by | INTEGER |
| accepted_by, accepted_at | NULLABLE |
| revoked_by, revoked_at | NULLABLE |
| created_at, updated_at | TIMESTAMP |

Lifecycle: `pending` → `accepted` | `revoked` | `expired`.  
`revoke` / `resend` solo sobre `pending`. Resend reemplaza `token_hash` y extiende `expires_at` (mismo `id`). Listados públicos omiten `token_hash`.

## Sentinel

`app_artist_profile.organization_id = 0` → artista independiente (sin org context).

### `create_new` debt

Approved `create_new` creates management profile only; `warehouse_artist_id` may remain NULL; does **not** insert `dim_artista`. Music may be empty until future warehouse link.
