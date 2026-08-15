# Feature Specification: Identity and First Access Orchestration

**Feature Branch**: `050-identity-first-access`

**Created**: 2026-08-13

**Status**: Draft — product decisions approved; implementation pending

**Input**: Consolidate the existing account, session and product-space capabilities into one coherent first-access journey without rewriting VOXMETRIKS.

## Product boundary

This feature connects existing identity, organization, Artist Space and household capabilities. It does not implement checkout, artist publishing, dashboards, real MFA or a payment provider.

## User Scenarios & Testing

### User Story 1 - Create and verify an account (Priority: P1)

A visitor creates an account with only the information required for identity, verifies the email and reaches a valid first-access destination without seeing development internals.

**Independent Test**: Register a new account, verify it, reload and confirm that the authenticated session and Personal space remain valid.

**Acceptance Scenarios**:

1. **Given** a new visitor, **When** they submit display name/username, email, password and confirmation, **Then** a pending account and verification challenge are created.
2. **Given** a valid challenge, **When** the user verifies it, **Then** the Free personal capability is provisioned explicitly and the session bootstrap succeeds.
3. **Given** an invalid, expired or over-attempt challenge, **When** it is submitted, **Then** the user receives a recoverable localized error and no session is created.
4. **Given** a production-like UI, **When** verification is shown, **Then** no development code, provider detail or credential is exposed.

### User Story 2 - Resume the intended destination after authentication (Priority: P1)

A user who followed an invitation or protected deep link returns to that destination after authentication instead of being sent to a role-based generic home.

**Independent Test**: Open an organization or artist invitation while signed out, authenticate and complete the invitation without copying the URL again.

**Acceptance Scenarios**:

1. **Given** an authorized `returnUrl`, **When** login succeeds, **Then** the destination is restored after validating membership/capability.
2. **Given** an unsafe or unauthorized destination, **When** login succeeds, **Then** the system ignores it and selects a safe eligible space without leaking data.
3. **Given** a failed or expired session restored from storage, **When** bootstrap runs, **Then** private context is cleared before returning to login.

### User Story 3 - Enter through an eligible product space (Priority: P1)

After authentication the application derives Personal, Organization, Artist, Data Ops and Platform Admin spaces from real memberships and roles, restores the last valid one or asks the user when a choice is meaningful.

**Independent Test**: Authenticate accounts with one and multiple spaces, switch between them, reload, revoke a membership and verify safe fallback.

**Acceptance Scenarios**:

1. **Given** a new ordinary account, **When** bootstrap completes, **Then** Personal is active and the user may choose “Listen”, “I am an artist” or “Manage an organization” as guided actions.
2. **Given** multiple eligible spaces, **When** no valid destination or persisted selection exists, **Then** a space chooser is shown.
3. **Given** a persisted eligible space, **When** the app reloads, **Then** it is restored with the same backend-authorized capabilities.
4. **Given** a revoked membership, **When** bootstrap or navigation detects it, **Then** the stale space is removed and the user returns safely to Personal.
5. **Given** a space activation failure, **When** the user switches, **Then** the previous URL and context remain active.

### User Story 4 - Use account recovery and household profiles safely (Priority: P2)

Password recovery revokes old access, and the household profile chooser appears only inside the Personal listening journey when the plan and roster require it.

**Independent Test**: Reset a password, verify old sessions/devices are revoked, then test a multi-profile Personal account and an Organization route.

**Acceptance Scenarios**:

1. **Given** a valid reset challenge, **When** a password is changed, **Then** all existing sessions and trusted devices are revoked atomically.
2. **Given** a Personal household with multiple profiles, **When** post-login resolution applies, **Then** “Who is listening?” precedes the Personal destination.
3. **Given** an Organization, Artist, Data Ops or Platform destination, **When** login succeeds, **Then** the household chooser does not intercept it.

### Edge Cases

- Two tabs activate different spaces concurrently; the latest successful explicit activation wins.
- An invitation is accepted while a different organization is persisted.
- Organization bootstrap succeeds while Artist or platform discovery is temporarily unavailable.
- A user logs out and another logs in on the same browser; no previous private state survives.
- Schema initialization runs against multiple independent DuckDB connections/databases in one process.
- A verification or reset challenge is requested repeatedly or for an unknown account.

## Requirements

### Functional Requirements

- **FR-001**: Registration MUST request only identity/legal data; favorite genre moves to optional Personal onboarding.
- **FR-002**: Registration, reset and password change MUST use one shared password policy with confirmation in the UI.
- **FR-003**: Authentication MUST preserve only a validated local `returnUrl` and restore it after session bootstrap.
- **FR-004**: The backend MUST expose one bootstrap contract containing user, security posture, eligible spaces, active context, capabilities, pending actions and recommended route.
- **FR-005**: Space eligibility MUST derive from real personal access, organization membership, artist membership, identity role and platform role; user input cannot grant a role.
- **FR-006**: Space activation MUST be explicit and return the backend-authoritative capability manifest used by navigation and guards.
- **FR-007**: Authorization MUST evaluate session, active account, membership, permission and subscription tier in backend; frontend only renders that decision.
- **FR-008**: Login, registration, verification, Google login and session restore MUST resolve destinations through the same post-auth orchestrator.
- **FR-009**: Household profile selection MUST apply only to Personal listening destinations and must use public presentation fields only.
- **FR-010**: Logout and 401 handling MUST clear session, organization, artist, household profile, space selection and private caches before another account can render.
- **FR-011**: Verification/recovery responses MUST be anti-enumeration safe and MUST NOT expose development/provider details outside an explicit development-only channel.
- **FR-012**: Schema initialization MUST be correct per database connection; a process-global “ready” flag MUST NOT skip required tables in an independent database.
- **FR-013**: Existing legacy routes MAY remain as adapters, but role-only redirects, username-based presentation exceptions and duplicate navigation MUST not remain authoritative.
- **FR-014**: All mutable forms MUST use typed reactive forms, localized human messages, catalog-backed selectors where applicable, a single status/error region and preserved values after recoverable failure.
- **FR-015**: The feature MUST add E2E coverage for registration, verification, recovery, deep links, multi-space switching, membership revocation and cross-account logout isolation.

### Key Entities

- **Session bootstrap**: Authoritative snapshot of user, security state, spaces, active context, capabilities, pending actions and initial route.
- **Product space**: Personal, Organization, Artist, Data Ops or Platform Admin context backed by real eligibility.
- **Capability decision**: Allowed/blocked module action with permission, tier and human-safe reason.
- **Post-auth intent**: Validated deep link or guided first-run choice; it never grants authorization.

## Success Criteria

- **SC-001**: Every successful authentication path reaches the same bootstrap/orchestration service.
- **SC-002**: Valid invitation deep links survive authentication; unsafe destinations never do.
- **SC-003**: Menu, route guard and backend capability decisions agree for every tested space/role.
- **SC-004**: Registration, verification, recovery and ten required space/isolation E2E scenarios pass at 1366x768 and 390x844.
- **SC-005**: Directed backend tests pass independently and in any order, including fresh temporary databases.
- **SC-006**: Frontend lint has zero errors; build and full test suites pass.

## Assumptions

- Existing identity, organizations, Artist Space, platform roles and household services are reused.
- Personal is the safe fallback for an authenticated ordinary user.
- PIN remains a household profile PIN, not MFA.
- Real MFA, checkout and public marketing expansion are separate product decisions.
