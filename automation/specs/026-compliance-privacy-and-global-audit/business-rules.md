# Business rules — Spec 026

- BR-CMPL-01: Never claim certified compliance with external norms.
- BR-CMPL-02: Deletion DSR blocked when active legal hold or blocking retention policy.
- BR-CMPL-03: No silent deletes — status becomes `blocked` or `completed` with audit.
- BR-CMPL-04: Sensitive access requires non-empty reason.
- BR-CMPL-05: Export payloads are sanitized (no secrets).
- BR-CMPL-06: Audit log is append-only (search only).
- BR-CMPL-07: Consent withdrawal recorded; does not invent legal effect beyond org policy.
