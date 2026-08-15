# Feature 053 — Professional Organization Journey

**Branch:** `codex/053-organization-professional-journey`
**Status:** Approved
**Product scope:** Organization creation, joining, onboarding, team setup and entry into the business workspace

## Problem

VOXMETRIKS already has Organizations, memberships, RBAC, invitations, subscriptions, billing and the professional checkout from Spec 052. The product journey is still fragmented: creation exposes technical fields, onboarding repeats data, progress lives only in component memory, invitations expose internal details, members are rendered as numeric IDs, and plan/payment/team steps do not form one durable flow.

The feature must connect the existing domains into one professional journey. It must not create another organization, RBAC, subscription or billing engine.

## Product decisions

1. A business user either creates an organization or joins through a valid invitation. Arbitrary public joining is not allowed.
2. Organization creation asks only for human business data. Slug, timezone and currency defaults are generated server-side from validated catalogs; advanced settings remain editable by authorized users.
3. The server is authoritative for journey progress and `next_action`. Reload, logout and switching spaces cannot reset or skip required state.
4. Onboarding state never grants entitlements. Operational access continues to derive from the real subscription/module-access snapshot.
5. Paid plans reuse Spec 052 checkout. Trials reuse the existing no-charge trial flow.
6. Team setup uses existing invitations and roles with human labels. Platform roles and raw role codes are never offered.
7. Invited members are not forced through owner-only billing steps. Their destination depends on organization state and capabilities.
8. Normal UI does not expose internal IDs, raw status codes, invitation tokens or academic/demo copy.
9. Every server mutation is tenant-scoped, transactional where multiple writes occur, idempotent and auditable.
10. Existing organization settings remain the editable source of truth after onboarding.

## Personas

- **Creator/owner:** creates the organization, selects trial or paid plan, completes checkout, optionally invites a team and enters the hub.
- **Billing administrator:** can resume an authorized pending checkout but cannot alter members without team permissions.
- **Organization administrator:** manages profile and team according to capabilities; cannot bypass subscription access rules.
- **Invited member/viewer:** accepts an invitation and lands in the organization without seeing owner-only setup or mutation controls.
- **Unauthenticated invitee:** signs in or registers and returns to the same invitation through the durable return URL from Spec 050.

## Canonical journeys

### Create a business workspace

`Business entry → Create organization → Review profile → Choose trial/plan → Checkout when paid → Team (optional) → Organization hub`

- The creation form collects display name, organization type, country and optional legal name.
- The server derives a unique slug plus country-based timezone/currency defaults and returns the created organization and authoritative journey state.
- A slug collision is resolved server-side unless the user deliberately provided an advanced slug.
- An existing in-progress journey resumes at its current server `next_action`.
- Paid checkout failure remains resumable and does not unlock operational modules.
- Successful payment or trial refreshes the session/organization context and advances to Team/Hub.

### Join an organization

`Invitation link → Authentication if needed → Accept → Activate organization space → Allowed landing`

- The token is consumed once and removed from URL/history as early as possible.
- Email mismatch, expired, revoked and already-used invitations produce distinct safe messages.
- An operational organization sends the member to its hub or first permitted module.
- An organization still being configured shows a professional waiting/status view unless the member has permission to continue setup.

### Edit after onboarding

`Organization hub → Settings / Members / Invitations / Roles / Billing`

- Profile fields use the same validated catalogs as creation.
- Members show safe identity presentation (display name and masked/authorized email), human role labels and human statuses instead of `user #id`.
- Navigation and CTAs reflect exact server capabilities; direct unauthorized calls still return 403.

## Functional requirements

- **FR-001** Add an authoritative Organization Journey read model with `organization`, `membership`, `capabilities`, `access_tier`, `profile`, `subscription`, `checkout`, `team_summary`, `completed_steps` and `next_action`.
- **FR-002** Persist only explicit journey metadata such as completion or optional-team dismissal. Derive payment, plan, membership and profile truth from their existing domains.
- **FR-003** Make the journey response deterministic and idempotent for repeated reads and refreshes.
- **FR-004** Create organizations with strict catalogs and server-generated defaults; reject unsupported type/country/timezone/currency values.
- **FR-005** Preserve advanced slug editing but never require a normal user to understand slugs.
- **FR-006** Reuse `/subscriptions/select-plan`, trial and `/subscriptions/checkout`; do not duplicate payment orchestration.
- **FR-007** Resume pending/failed/processing Organization checkout from the journey response.
- **FR-008** Mark journey complete only after server prerequisites are satisfied. Completion must not modify access tier or entitlements.
- **FR-009** Return capability-driven actions for profile update, plan selection, checkout, invitation, member view, role view and hub entry.
- **FR-010** Expose invitation-safe role options from backend catalogs with human labels and descriptions; exclude platform/system-only roles.
- **FR-011** Enrich authorized member/invitation presentation so normal UI never depends on numeric user IDs or raw role/status codes.
- **FR-012** Preserve the Spec 050 return URL through authentication and consume invitation state once.
- **FR-013** Never expose an invitation token in production delivery mode. A local-development link may be returned once only when explicitly configured and must be labeled as a local environment facility.
- **FR-014** Filter organization administration links and onboarding actions by exact capabilities and access tier.
- **FR-015** Provide accessible loading, empty, validation, success, conflict, forbidden and retry feedback on desktop and mobile.
- **FR-016** Keep organization profile and team fields editable after onboarding through the same backend contracts.
- **FR-017** Emit audit events for journey completion and retain existing organization, invitation, role, subscription and checkout audit behavior.
- **FR-018** Use isolated DuckDB copies for automated journeys and leave the canonical warehouse fingerprint unchanged.

## Acceptance scenarios

1. A new owner creates an organization using human fields, reloads, and resumes the same journey without duplicated organizations.
2. A paid plan decline leaves access at onboarding; retry success activates operational access once and lands in Team/Hub.
3. A trial creates no payment artifacts and advances using the existing trial contract.
4. An invited viewer authenticates, accepts the invitation and reaches only permitted surfaces without owner billing prompts.
5. A billing administrator can resume checkout but cannot invite or change roles without those permissions.
6. A member lacking `member.invite` does not see the invite CTA and receives 403 on a direct mutation.
7. Creation, invitation acceptance and journey completion replay safely under concurrent requests.
8. Profile updates validate catalogs, preserve allowed values and show saved data after reload.
9. Desktop 1366×768 and mobile 390×844 complete owner success, owner decline/retry and invited-member journeys through real UI.
10. Automated acceptance contains no canonical DB writes, raw PAN/CVV, leaked invitation tokens or internal-ID copy.

## Out of scope

- Global redesign of every Organization domain tab.
- CRM, Customer Success, Compliance, Campaigns, Royalties, strategic dashboards or AI changes.
- Real email infrastructure or a real payment gateway.
- Taxes, FX, contracts, legal verification or public self-service joining without an invitation.
- Rewriting Organizations, RBAC, Billing, Subscriptions, Checkout or session bootstrap.
