# API Contract — 051 Artist Journey

All endpoints require an authenticated session. Errors use `{detail: {code, message}}` with stable, non-sensitive codes.

## Discovery and requests

### `GET /api/v1/artist-access/discover?search=...&limit=20`

Returns catalog candidates enriched server-side:

```json
{
  "items": [{
    "warehouse_artist_id": 123,
    "display_name": "Artist",
    "image_url": null,
    "management_state": "unmanaged",
    "allowed_action": "claim_ownership",
    "artist_profile_id": null,
    "request_id": null,
    "request_status": null
  }],
  "total": 1
}
```

`management_state`: `unmanaged | managed | member | pending`
`allowed_action`: `claim_ownership | request_access | open_space | view_request | none`

### `POST /api/v1/artist-access/requests`

Existing route, strict body:

```json
{
  "request_type": "claim_ownership",
  "warehouse_artist_id": 123,
  "target_artist_profile_id": null,
  "proposed_display_name": null,
  "proposed_role": "member",
  "relationship_type": "artist_self",
  "evidence_url": "https://example.test/evidence",
  "evidence_note": null,
  "accuracy_attested": true
}
```

`claim_ownership` requires relationship plus evidence. `create_new` requires display name, relationship and attestation. `request_access` requires managed target and non-owner role.

## Artist profile and team

Existing artist-space routes remain. Profile PATCH becomes strict and supports:

```json
{
  "display_name": "Artist",
  "legal_name": "Private legal name",
  "bio": "Public biography",
  "country_code": "EC",
  "primary_genre": "latin",
  "website_url": "https://artist.example",
  "image_url": "https://cdn.example/artist.jpg",
  "external_identifiers": [
    {"system_code": "youtube", "external_value": "channel-id"}
  ]
}
```

Responses expose legal name only to permitted roles. Team/invitation/access endpoints retain routes but return human-mappable reason codes and never expose token hashes.

## Artist-scoped publishing

Routes are under `/api/v1/artist-space/{artist_profile_id}/publishing`:

- `GET /releases`
- `POST /releases` — create draft
- `GET /releases/{submission_id}`
- `PATCH /releases/{submission_id}`
- `POST /releases/{submission_id}/tracks`
- existing media/contributor/rights mutations through artist-scoped adapters
- `POST /releases/{submission_id}/submit`

The server resolves organization from the profile and verifies both active artist membership and the requested artist permission. Client-supplied organization ID is ignored/prohibited. All mutations reuse existing catalog-publishing application use cases.

## Platform independent-review adapter

Routes are under `/api/v1/platform/catalog-reviews`:

- `GET /?status=under_review`
- `GET /{submission_id}`
- `POST /{submission_id}/request-changes`
- `POST /{submission_id}/approve`
- `POST /{submission_id}/reject`
- `POST /{submission_id}/publish`

Only submissions backed by `organization_type='artist_workspace'` are eligible. Platform authorization, self-review prevention and audit are mandatory.

## Stable error codes

- `artist_not_found`
- `artist_membership_required`
- `artist_permission_denied`
- `artist_request_conflict`
- `artist_request_invalid_state`
- `artist_evidence_required`
- `artist_workspace_provision_failed`
- `release_artist_mismatch`
- `release_invalid_state`
- `release_incomplete`
- `self_review_forbidden`
- `permission_denied`

400 is validation, 403 authorization, 404 scoped absence, 409 state/idempotency conflict. Responses MUST NOT reveal whether a foreign artist/release exists when the caller lacks scope.
