# Feature Specification: Professional Artist Journey

**Feature Branch**: `codex/051-artist-professional-journey`
**Created**: 2026-08-13
**Status**: Approved
**Input**: Consolidate the existing artist identity, team, catalog and publishing capabilities into one professional end-to-end journey without rewriting the product.

## Product decision

Artist Space is the canonical experience for an individual artist or artist team. The Organization Catalog remains the canonical experience for labels, distributors and businesses managing multiple artists. Both surfaces reuse the same artist profile and publishing domains; they are not separate products.

An approved independent artist receives an internal tenant workspace used for isolation, rights and publishing. That backing workspace MUST NOT appear as a second business organization in the product-space selector. Existing independent profiles stored with `organization_id=0` are migrated idempotently.

## User Scenarios & Testing

### User Story 1 — Become or join an artist (Priority: P1)

An authenticated person enters through “Soy artista” and chooses exactly one understandable path: claim an existing catalog artist, create a new artist, request access to a managed artist, or accept an invitation.

**Why this priority**: Artist ownership is the security boundary for every later profile, team and publishing action.

**Independent Test**: Exercise all four entry paths with separate accounts and verify that no Artist Space is granted before the correct approval or invitation acceptance.

**Acceptance Scenarios**:

1. **Given** an unclaimed catalog artist, **when** a user submits relationship and ownership evidence, **then** one platform-review request is created and its friendly status is visible.
2. **Given** a managed artist, **when** a non-member requests access, **then** the request goes to that artist’s owner/administrator rather than Platform Ops.
3. **Given** no catalog match, **when** a user proposes a new artist, **then** Platform Ops can approve or reject it with an auditable reason.
4. **Given** a valid invitation link, **when** the matching authenticated user accepts it, **then** the Artist Space is immediately available and the return URL is consumed once.
5. **Given** an existing membership or pending request, **when** the user searches the same artist, **then** the UI shows the current state and does not offer an invalid duplicate action.

---

### User Story 2 — Manage an editable artist workspace (Priority: P1)

An approved artist enters a focused workspace with Summary, Profile, Music and Team. Profile fields are editable according to role, use human controls and produce clear loading, success, validation and error feedback.

**Why this priority**: Approval without a usable workspace is not a completed product journey.

**Independent Test**: As owner, administrator, collaborator and reader, open the same artist and verify the exact allowed controls and 403 behavior.

**Acceptance Scenarios**:

1. **Given** an owner or administrator, **when** they edit public name, bio, country, genre, website, image or external links, **then** valid changes persist and are shown after reload.
2. **Given** a reader, **when** the profile loads, **then** data is visible but edit and destructive controls are absent.
3. **Given** multiple artist memberships, **when** the user changes Artist Space, **then** every page uses the selected `artist_profile_id`; no page silently uses the first profile.
4. **Given** a mobile viewport, **when** forms or lists render, **then** actions remain reachable and labels never overlap inputs.

---

### User Story 3 — Manage the artist team (Priority: P1)

An owner or administrator invites collaborators with a human role selector, reviews access requests, changes roles, resends/revokes pending invitations and removes members without exposing tokens or internal codes.

**Independent Test**: Invite one user per role, accept one invitation, change one role, revoke one invitation and member, and verify last-owner protection.

**Acceptance Scenarios**:

1. **Given** team-management permission, **when** an email and role are submitted, **then** one pending invitation is created with delivery status and visible feedback.
2. **Given** a pending access request, **when** an owner approves it, **then** the requested non-owner membership is created atomically.
3. **Given** the last owner, **when** any action would remove or demote that owner, **then** the operation is rejected without partial state.
4. **Given** insufficient permission, **when** team mutations are attempted by API, **then** 403 is returned without leaking another artist’s data.

---

### User Story 4 — Create and submit music (Priority: P1)

An artist with publishing permission creates a release draft from Artist Space, adds one or more tracks, uploads private audio and cover art, adds contributors and rights, reviews the complete submission and sends it for review.

**Independent Test**: Create a multi-track draft, reload it, correct validation errors, submit it and verify that it appears in the artist’s Music page with the correct state.

**Acceptance Scenarios**:

1. **Given** an active Artist Space, **when** “Nuevo lanzamiento” is selected, **then** the active artist is explicit and cannot be replaced by `artist_profile_ids[0]`.
2. **Given** incomplete required metadata, missing tracks or invalid rights shares, **when** submission is attempted, **then** the relevant step is identified and no false success is shown.
3. **Given** an upload or contributor operation fails, **when** the wizard processes the draft, **then** the failure is visible and later stages are not silently reported as successful.
4. **Given** a collaborator, **when** a draft is created or edited, **then** it can be saved but only an owner/administrator can submit it for review.
5. **Given** a label/distributor organization, **when** its catalog manager creates a release, **then** an artist must be selected explicitly from permitted profiles.

---

### User Story 5 — Review and resolve submissions (Priority: P2)

Platform catalog reviewers handle independent-artist submissions; organization reviewers handle label/distributor submissions. The creator cannot approve their own submission. Artists can see requested changes, correct the draft and resubmit.

**Independent Test**: Submit as an independent artist, request changes as Platform Ops, resubmit, approve and publish; repeat a label submission with a distinct organization reviewer.

**Acceptance Scenarios**:

1. **Given** an independent-artist submission, **when** Platform Ops opens its review queue, **then** the reviewer sees metadata, private-media indicators, contributors, rights issues and history without activating the hidden workspace.
2. **Given** the same actor created the submission, **when** they try to approve it, **then** separation of duties blocks the action.
3. **Given** requested changes, **when** the artist updates and resubmits, **then** history remains append-only and the new review is possible.
4. **Given** approval, **when** publication is executed idempotently, **then** the release and tracks appear once in Artist Space and the listening catalog.

## Edge Cases

- Two users claim the same unowned artist concurrently: at most one owner is approved.
- A catalog artist becomes managed between discovery and submission: the server returns a stable conflict and the UI offers “Solicitar acceso”.
- An invitation is expired, revoked, already accepted or belongs to another email.
- An artist request is cancelled while a reviewer has it open.
- Backing-workspace provisioning fails after approval begins: request, profile, organization and memberships roll back together.
- A legacy profile with `organization_id=0` is encountered repeatedly: migration reuses the same backing workspace.
- A user belongs to the artist team but not the backing organization: Artist Space authorization remains artist-membership based.
- A user belongs to the backing organization but not the artist: they receive no Artist Space access.
- Multiple artist profiles share similar names: actions use stable IDs and display contextual metadata, never name matching alone.
- Upload, save or submit fails mid-wizard: persisted completed steps remain valid, error is shown and no later step is claimed successful.
- Rights total exceeds or falls below the accepted allocation rule: submission is blocked with field-level guidance.
- Published content cannot be overwritten by a draft mutation.

## Requirements

### Functional Requirements

- **FR-001**: The product MUST expose one canonical “Soy artista” entry with claim, create, access-request and invitation paths.
- **FR-002**: Artist discovery MUST return server-authoritative management state and the single allowed next action per user/artist.
- **FR-003**: Claim requests MUST capture relationship type and at least one evidence note or evidence URL; raw identity documents are outside scope.
- **FR-004**: Platform Ops MUST review `claim_ownership` and `create_new`; active artist owners/administrators MUST review `request_access`.
- **FR-005**: Approval MUST atomically create/reuse the artist profile, backing tenant, artist owner membership and tenant owner membership.
- **FR-006**: New independent artists MUST NOT use `organization_id=0`; existing zero-backed profiles MUST be migrated idempotently without appearing as ordinary business organizations.
- **FR-007**: Artist Space authorization MUST remain based on `app_artist_membership`, not on hidden organization membership.
- **FR-008**: Roles MUST be presented as Propietario, Administrador, Colaborador and Solo lectura while preserving stable backend codes.
- **FR-009**: Permissions MUST distinguish view, profile update, draft create/edit, submission, team management, invitation and access review.
- **FR-010**: Artist profile MUST support editable display name, legal name with restricted visibility, bio, country, primary genre, website, image and external identifiers.
- **FR-011**: Country, genre, role, release type and language MUST use selects/comboboxes; raw IDs and internal status codes MUST NOT be required from users.
- **FR-012**: Artist Music MUST consolidate releases and tracks in one surface with tabs/filters and one role-aware “Nuevo lanzamiento” action.
- **FR-013**: The release workflow MUST support multiple tracks, private audio, cover, contributors, rights contract selection, draft persistence, review and explicit submit.
- **FR-014**: Every release creation path MUST select or receive an explicit artist profile; choosing the first profile implicitly is prohibited.
- **FR-015**: Release orchestration MUST NOT swallow failed track, media, contributor, rights or submit operations.
- **FR-016**: Independent submissions MUST have a Platform Ops review route; organization submissions MUST retain organization-scoped review.
- **FR-017**: Creator/reviewer separation, tenant isolation and artist isolation MUST be enforced server-side and audited.
- **FR-018**: Request, invitation, membership, profile and publication mutations MUST use transactions and stable 400/403/404/409 error codes.
- **FR-019**: The UI MUST provide loading, empty, success, validation, conflict and retry states; destructive actions MUST require confirmation.
- **FR-020**: Legacy `/artist-profiles` and `/artist/releases` routes MUST remain compatible, but navigation MUST not present them as duplicate products.
- **FR-021**: Artist and catalog changes MUST refresh session/space context without requiring logout.
- **FR-022**: All new tests MUST use isolated temporary databases and MUST NOT mutate the canonical dataset.
- **FR-023**: No payment, royalty payout, AI, analytics redesign or real email-provider integration is part of this feature.

### Key Entities

- **Artist Profile**: Canonical business identity for an artist; belongs to one backing tenant and may link to one warehouse artist.
- **Artist Membership**: Sole authority for Artist Space access and role-specific capabilities.
- **Artist Access Request**: Claim, create or access application with evidence, state and review trail.
- **Artist Invitation**: Time-bounded team invitation tied to email, role and artist.
- **Artist Workspace Organization**: Internal organization tenant used by an independent artist for isolation and publishing; hidden from ordinary business-space discovery.
- **Release Submission**: Stateful draft/review/publication aggregate linked explicitly to artist profile and backing organization.
- **Release Track / Contributor / Rights Link / Review**: Existing publishing children and append-only decision evidence.

## Success Criteria

- **SC-001**: All four artist-entry paths pass backend, frontend and E2E tests with zero unauthorized space grants.
- **SC-002**: An approved independent artist can reach Artist Space and create/submit a release without manually creating or selecting a business organization.
- **SC-003**: A label user managing multiple artists must explicitly choose the artist on every new release; automated tests prove no first-item fallback.
- **SC-004**: Owner, administrator, collaborator and reader controls match backend permissions on all Artist Space pages.
- **SC-005**: One independent submission completes request-changes → resubmit → approve → publish with one release and no duplicate tracks.
- **SC-006**: Cross-artist, cross-organization and self-approval security tests pass with no payload leakage.
- **SC-007**: Desktop 1366×768 and mobile 390×844 E2E cover entry, profile, team and release workflows with no inaccessible primary action.
- **SC-008**: Full backend/frontend gates pass at closure; the canonical DuckDB hash/mtime is unchanged by tests.

## Assumptions

- Existing FastAPI, Angular, artist identity, organization and catalog-publishing domains are reused.
- `organization_type='artist_workspace'` identifies hidden backing tenants unless a dedicated visibility field is proven necessary during implementation.
- Platform Admin is the initial catalog reviewer for independent artists; a dedicated catalog-reviewer platform role may be added only by reusing current RBAC catalogs.
- Email delivery may remain the existing development/outbox channel, but the UI never exposes raw tokens outside explicitly allowed development tooling.
- Audio remains private until publication and current provider/licensing limitations remain unchanged.

## Out of Scope

- Rebuilding authentication, organizations or publishing from scratch.
- Payment checkout, subscriptions, royalty settlement or real payouts.
- Commercial streaming licensing or distribution to external DSPs.
- Government-ID/KYC document handling.
- New AI or recommendation features.
