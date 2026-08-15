# Contract — Platform Ops Overview

## Endpoint

`GET /api/v1/platform-ops/overview`

Authorization: the same platform authority used by the existing Platform Ops surface. Unauthorized identities receive 401/403 without queue counts.

## Response

Strict Pydantic model (`extra='forbid'`):

- `health`: `healthy | degraded | unavailable`
- `generated_at`: UTC timestamp
- `queues`: array of:
  - `code`: `artist_requests | catalog_reviews | audio_unresolved | incidents`
  - `count`: integer or `null`
  - `availability`: `available | unavailable`
  - `severity`: `normal | attention | critical`
- `next_queue`: one queue code or `null`
- `has_pending_work`: boolean

Priority for `next_queue`: artist requests, catalog reviews, unresolved audio, incidents. A queue whose source is unavailable is not treated as empty.

The endpoint does not expose route paths, internal SQL errors, table names, secrets or raw payloads.

