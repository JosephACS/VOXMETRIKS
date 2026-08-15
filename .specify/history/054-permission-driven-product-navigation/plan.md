# Plan — 054 Permission-Driven Product Navigation

## Architecture

Create a typed, pure frontend product-surface registry and access evaluator. Reuse session bootstrap, `SpaceContextService`, organization permissions/access tier, artist capabilities and existing route guards. The registry is presentation metadata; backend guards remain authoritative.

## Implementation sequence

1. Inventory every current sidebar item, contextual tab and guarded route.
2. Define stable surface ids and capability/tier contracts.
3. Route `space-nav.config`, predicted shell navigation and `module-context` through the registry.
4. Remove username/presentation and out-of-product exception paths from production decisions.
5. Correct Platform Admin, organization Reports and permission-specific tabs.
6. Preserve edit-entry paths for organizations, artists, members and billing.
7. Add pure matrix tests, route/navigation parity tests and isolated E2E personas.

## Constraints

- Prefer deletion of duplicate policy code over compatibility shims.
- Do not weaken route or backend guards to make a navigation test pass.
- Do not hardcode access by display role when a permission exists.
- No canonical dataset writes.
- No new backend tables, seeds or domain engines.

## Validation strategy

- During implementation: directed navigation, guard and module-context tests only.
- Final local gate once: frontend lint, full frontend tests, production build, `create_app()`, Playwright 054 and `git diff --check`.
- Backend full suite is unnecessary unless backend product code changes.
- GitHub CI runs once after the audited commit.
