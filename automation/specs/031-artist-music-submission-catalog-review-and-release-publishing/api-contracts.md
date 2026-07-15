# API contracts — Spec 031

Prefix `/api/v1`

## Releases `/releases`
- `POST /releases` create draft
- `GET /releases` list (scoped)
- `GET /releases/{id}` detail
- `PATCH /releases/{id}` metadata (draft/changes_requested)
- `POST /releases/{id}/tracks` add track
- `PATCH /releases/{id}/tracks/{tid}` update
- `POST /releases/{id}/contributors`
- `POST /releases/{id}/validate`
- `POST /releases/{id}/submit`
- `POST /releases/{id}/withdraw`

## Media `/media`
- `POST /media/audio` multipart
- `POST /media/cover` multipart
- `GET /media/{id}` metadata
- `GET /media/{id}/content` ACL-controlled stream (no raw FS path leak)

## Catalog review `/catalog-review`
- `GET /catalog-review` inbox
- `GET /catalog-review/{id}`
- `POST /catalog-review/{id}/claim` → under_review
- `POST /catalog-review/{id}/request-changes`
- `POST /catalog-review/{id}/approve`
- `POST /catalog-review/{id}/reject`
- `POST /catalog-review/{id}/schedule`
- `POST /catalog-review/{id}/publish`
- `POST /catalog-review/{id}/suspend`
- `POST /catalog-review/{id}/withdraw`

## Artist portal `/artist-portal`
- `GET /artist-portal/me`
- `GET /artist-portal/releases`
- `GET /artist-portal/tracks`
- `GET /artist-portal/summary`

All mutating routes: RBAC `publishing.*`, org header, audit, sanitized errors.
