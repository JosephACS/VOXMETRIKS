# Business rules — Spec 027

- BR-OPS-01: Never claim real email, HA, production backup/restore, or international scale.
- BR-OPS-02: Store secret_ref only — never plaintext secrets in DB/API responses.
- BR-OPS-03: Webhook ingest is idempotent by provider_event_id / idempotency_key.
- BR-OPS-04: Failed jobs may retry then enter conceptual dead-letter status.
- BR-OPS-05: Mock email/notification adapters must be labeled MOCK.
- BR-OPS-06: Platform ops APIs require platform RBAC (`ops.*`).
