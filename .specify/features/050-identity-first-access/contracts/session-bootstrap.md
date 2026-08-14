# Session bootstrap contract

## GET `/api/v1/session/bootstrap`

Authenticated response:

```json
{
  "user": { "id": 1, "display_name": "Alex", "identity_role": "user" },
  "security": { "email_verified": true, "profile_pin_enabled": false },
  "spaces": [
    {
      "key": "personal",
      "kind": "personal",
      "display_name": "Personal",
      "capabilities": [{ "code": "music.listen", "allowed": true, "reason": null }],
      "home_path": "/discover"
    }
  ],
  "active_space_key": "personal",
  "pending_actions": [],
  "recommended_path": "/discover"
}
```

Rules:

- Never include tokens, password state, emails of household members, invitation hashes or cross-tenant identifiers.
- Blocked capabilities may expose only stable human-safe reason codes.
- A partial discovery failure must be represented explicitly; it must not invent eligibility.

## POST `/api/v1/session/context`

Request:

```json
{ "space_key": "organization:12" }
```

Response: the same bootstrap document with the newly active space. Persist selection only after membership, permission and tier validation succeed.

Errors:

- `400` malformed/unsupported space key.
- `403` caller is not eligible; no tenant details.
- `409` context cannot be activated in its current lifecycle/tier.
