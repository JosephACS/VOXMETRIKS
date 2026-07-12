# Business Rules — Spec 021

1. **Organization scoping.** All catalog assets and rights contracts are scoped by `X-Organization-Id`; cross-org access raises `NotFoundError`.
2. **Percentage validation is never global.** Ownership percentages are validated only for the tuple `(asset_id, rights_type, territory_code)` using a sweep-line algorithm across overlapping `[valid_from, valid_to]` periods of non-archived contracts.
3. **WORLD territory.** A contract with no explicit `app_rights_territory` rows is treated as `WORLD` scope and overlaps every explicit territory for the same asset/rights_type.
4. **Conflict on >100%.** When concurrent sum exceeds 100%, a `rights_conflict` row is opened/refreshed and contributing contracts transition to `status='disputed'`.
5. **Rights ≠ CRM commercial.** `app_rights_contract` and `app_commercial_contract` are separate domains; no joins, no shared lifecycle.
6. **Warehouse link optional.** `warehouse_track_id` must reference existing `dim_track.id_track`; `dim_track` is never mutated. `warehouse_album_id` is optional and unvalidated (no `dim_album` table).
7. **Approval workflow.** Submit from `draft` or `disputed`; one pending approval per contract; approve transitions contract to `active`.
8. **Archive is terminal** for active dispute resolution path (archived contracts excluded from overlap calculation).
9. **Audit on mutation.** All state changes write to `app_audit_log` via `AuditRepository`.
10. **No legal validity claims.** UI and docs use "recorded"/"tracked" — never "certified" or "proof of ownership".
11. **No auto-expiry.** `valid_to` passing does not auto-transition status to `expired` (accepted debt).
