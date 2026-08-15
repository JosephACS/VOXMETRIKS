# Research — 051 Professional Artist Journey

## Existing assets

- `artists/identity_access` already supports memberships, claim/create/access requests, invitations and Platform Admin approval.
- `artist-space` frontend already exposes summary, profile, tracks, releases and team.
- `artists` organization frontend manages business artist profiles and team/history.
- `catalog_publishing` already owns release drafts, tracks, private media, contributors, rights, review states and publication.
- Spec 050 already restores “Soy artista”, safe invitation return URLs and server-authoritative space bootstrap.

## Confirmed fractures

1. Three user-facing surfaces represent overlapping artist concepts.
2. Approved independent artists are stored with `organization_id=0`, while publishing requires a real organization context.
3. Artist Space tracks/releases are read-only lists with no connected publish action.
4. The organization release wizard can silently use the first artist profile.
5. Several wizard operations use `catchError(() => of(null))`, allowing false success.
6. Catalog/profile/team navigation is not consistently permission filtered.
7. Claim discovery shows both claim and access actions without authoritative management state.

## Decisions

### D1 — Two experiences, one domain

Artist Space serves one selected artist. Organization Catalog serves businesses managing many artists. Old paths remain compatibility routes; shared services/use cases remain domain-owned.

### D2 — Hidden backing tenant

An independent artist receives a real `app_organization` with type `artist_workspace`. It exists for tenant isolation and publishing but is filtered from regular organization discovery/navigation. Artist authorization never depends on exposing or activating that organization.

### D3 — Adapter, not duplicate publishing engine

Artist-scoped publishing endpoints validate artist membership, resolve the backing organization and call existing catalog-publishing use cases. They MUST NOT duplicate the state machine or persistence logic.

### D4 — Explicit permissions

Stable role codes remain. Add catalog/draft/submit capabilities to artist-role permissions and make frontend controls consume the same manifest.

### D5 — Platform review for independent artists

Independent submissions are reviewed through Platform Ops without requiring the reviewer to become a member of the hidden tenant. Existing review/publish use cases and self-approval checks are reused and all cross-tenant access is audited.

### D6 — No silent orchestration

Draft steps persist explicitly. Failure of media, track, contributor, rights or submit prevents a success result and remains retryable.

## Rejected alternatives

- **Keep `organization_id=0` and special-case every publishing query**: weak tenant semantics and grows exceptions.
- **Show the hidden tenant as a normal organization**: exposes irrelevant billing/CRM/CS modules and recreates user confusion.
- **Build a second artist publishing package**: violates single ownership and duplicates the release state machine.
- **Delete organization artist management**: labels/distributors require multi-artist administration.
- **Merge artist and warehouse artist tables**: operational ownership and analytical catalog identities have different lifecycles.
