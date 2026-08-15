# Contract — Organization Professional Journey

## Read journey

`GET /api/v1/organizations/{organization_id}/journey`

Requires active membership and `organization.view`.

Response shape:

```json
{
  "organization": { "id": 1, "display_name": "Acme Music", "organization_type": "label" },
  "access_tier": "onboarding",
  "completed_steps": ["organization"],
  "next_action": "choose_plan",
  "capabilities": {
    "update_profile": true,
    "choose_plan": true,
    "resume_checkout": false,
    "invite_team": true,
    "view_members": true,
    "enter_workspace": false,
    "complete_journey": false
  },
  "subscription": { "status": null, "plan_name": null, "trial": false },
  "checkout": null,
  "team": { "active_members": 1, "pending_invitations": 0 },
  "allowed_destinations": ["profile", "plan"]
}
```

Allowed `next_action` values:

- `review_profile`
- `choose_plan`
- `resume_checkout`
- `await_payment`
- `invite_team`
- `complete`
- `enter_workspace`
- `wait_for_owner`
- `organization_unavailable`

The backend decides this value. Frontend must not infer operational access from payment UI state.

## Complete journey

`POST /api/v1/organizations/{organization_id}/journey/complete`

Request:

```json
{ "idempotency_key": "opaque-user-intent-key", "team_step_skipped": true }
```

The server revalidates membership, profile and subscription/access prerequisites. It may record completion metadata, but it must not activate a plan, mark an invoice paid or grant entitlements.

## Organization creation

The existing `POST /api/v1/organizations` remains canonical. Normal requests provide:

```json
{
  "display_name": "Acme Music",
  "legal_name": "Acme Music S.A.",
  "organization_type": "label",
  "country_code": "EC",
  "client_intent_id": "opaque-user-intent-key"
}
```

`slug`, `timezone` and `default_currency` are optional advanced overrides. If absent, the backend generates validated defaults. The response adds `journey` or a `journey_url/next_action` sufficient to resume without client guesses.

## Role catalog

`GET /api/v1/organizations/{organization_id}/invitation-roles`

Returns only roles the actor may assign and that are valid for organization invitations:

```json
{
  "items": [
    { "code": "viewer", "label": "Solo lectura", "description": "Puede consultar información autorizada" }
  ]
}
```

Platform-scoped or inactive roles are never returned or accepted.

## Member presentation

Authorized member-list responses add a safe `user` object and human role presentation:

```json
{
  "id": 7,
  "status": "active",
  "user": { "display_name": "Ana Pérez", "email": "ana@example.com" },
  "roles": [{ "code": "viewer", "label": "Solo lectura" }]
}
```

The UI may use IDs as internal keys but cannot display them as identity.

## Errors

- `400 invalid_catalog_value | invalid_transition`
- `403 permission_denied`
- `404 organization_not_found`
- `409 create_conflict | journey_prerequisite_missing | concurrent_update`
- `410 invitation_expired`

Errors must not reveal foreign organization, membership, checkout or invitation identifiers.
