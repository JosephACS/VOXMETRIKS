# Plan — 055 Platform Admin Professional Journey

## Backend

- Add a read-only overview use case in `platform_ops` and a strict Pydantic response in its presentation layer.
- Compose counts from existing artist request, catalog publishing, audio source and incident state. Do not seed or create tables on GET.
- Harden platform actions only where tests expose missing validation, atomicity or audit behavior; do not rewrite domain engines.

## Frontend

- Replace the current Platform Ops dashboard with queue cards, health summary and next-action guidance.
- Move the current provider/job/flag/backup presentation to a lazy `/platform-ops/system` page.
- Improve the existing artist-request, catalog-review and unresolved-audio pages in place.
- Reuse Enterprise UI components, `NotificationService`, the 054 product-surface registry and existing API services.
- Add one small presentation utility only if status/queue mapping would otherwise be duplicated.

## Verification

- Directed backend tests for overview, RBAC, state transitions and rollback.
- Directed frontend tests for dashboard, queues, confirmations and routing.
- Frontend build, `create_app()`, OpenAPI presence and `git diff --check`.
- Isolated Playwright 055 for Platform Admin desktop/mobile; no canonical DB writes.
- Do not run the 10–15 minute full backend suite or the entire frontend suite during implementation.

