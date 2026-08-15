# Spec 055 — Platform Admin Professional Journey

## Problem

Platform administration exists as separate pages for artist requests, independent catalog reviews, unresolved audio and low-level runtime data. The default dashboard exposes provider codes, jobs, flags and backup paths instead of telling an administrator what requires attention. Actions use inconsistent feedback and confirmation patterns, which makes a functional product feel like a technical console.

## Goal

Provide one professional Platform Admin workspace that prioritizes real work queues, preserves the existing domain engines and moves diagnostic detail to an explicit advanced-system surface.

## Canonical journey

1. A platform administrator enters `/platform-ops`.
2. The server returns an authoritative overview with health and counts for artist requests, catalog reviews, unresolved audio and operational incidents.
3. The UI highlights the next non-empty queue and links to every available queue.
4. The administrator reviews human-readable evidence before acting.
5. Approve, request-changes, reject, publish, resolve and mark-unavailable actions require the appropriate capability, expose busy state, and return explicit success/error feedback.
6. Rejection and request-changes require a non-blank reason. Destructive or irreversible actions require an inline confirmation step.
7. Providers, jobs, feature flags and backups live under `/platform-ops/system`; they are not the primary dashboard.

## Product rules

- Reuse `platform_ops`, artist identity access, catalog publishing and audio source services. Do not create parallel approval or audio engines.
- Platform Admin is platform-scoped. Do not expose organization CRM, billing, subscriptions or campaign surfaces without an organization context.
- The overview is read-only and performs no DDL or seed operations.
- Queue counts use canonical persisted state; unavailable data is `null`/`unavailable`, never fabricated as zero.
- Backend remains the authorization authority. Frontend visibility mirrors capabilities but never replaces backend checks.
- The default surface uses human labels. Internal IDs appear only as secondary references.
- No raw secrets, provider payloads, JSON blobs, filesystem paths or development/academic copy on the default dashboard.
- Simulated provider behavior remains honestly labeled under advanced tools.
- No `window.confirm`; use accessible inline confirmation UI.

## Acceptance criteria

- `GET /api/v1/platform-ops/overview` returns a strict typed response with health, queue counts, availability and `next_queue`.
- `/platform-ops` renders queue-first overview and never loads provider/job/flag/backup lists.
- `/platform-ops/system` contains the existing diagnostic lists and is the only page that loads them.
- Artist request, catalog review and unresolved-audio pages have loading, empty, error, busy and success states.
- Mutations reject invalid transitions and blank reasons without partial writes.
- Navigation and contextual tabs include System only for eligible Platform Admin users.
- Desktop 1366×768 and mobile 390×844 traverse every visible Platform Admin link without unexpected 401/403.
- E2E actions use normal UI interactions and an isolated DuckDB copy.

## Out of scope

- New provider integrations, real email delivery, real backups or infrastructure provisioning.
- Organization commercial modules.
- Replacing catalog publishing, artist identity or audio-resolution state machines.
- Broad redesign of Data Ops, Workpanel or reports.

