# Data Model — 051 Professional Artist Journey

## Reused tables

- `app_artist_profile`
- `app_artist_membership`
- `app_artist_access_request`
- `app_artist_invitation`
- `app_artist_external_identifier`
- `app_artist_status_history`
- `app_organization`, `app_organization_member`, organization RBAC/audit tables
- `app_release_submission` and existing release child/history/publication tables

## Additive profile fields

`app_artist_profile` gains nullable, idempotently added fields:

- `bio VARCHAR`
- `country_code VARCHAR`
- `primary_genre VARCHAR`
- `website_url VARCHAR`
- `image_url VARCHAR`

`legal_name` remains non-public and editable only by owner/administrator. External service identifiers continue in `app_artist_external_identifier`; do not add one column per provider.

## Additive request evidence

`app_artist_access_request` gains:

- `relationship_type VARCHAR` — `artist_self | manager | label_representative | collaborator`
- `evidence_url VARCHAR`
- `evidence_note VARCHAR`

Claim ownership requires relationship plus at least one evidence field. New-artist creation requires relationship and an explicit accuracy attestation at the API boundary.

## Hidden backing tenant

- `app_organization.organization_type = 'artist_workspace'`
- deterministic slug based on stable profile/request identity, not display name alone
- owner has an active organization membership for internal publishing authorization
- organization discovery/session bootstrap filters this type from ordinary Organization spaces
- Artist Space resolves `artist_profile.organization_id` internally

### Legacy migration

For each active/draft profile with `organization_id=0`:

1. Lock/serialize the migration region.
2. Reuse a deterministic existing `artist_workspace` organization when present.
3. Otherwise provision organization + owner membership from the active artist owner.
4. Update profile organization using the established DuckDB-safe profile mutation helper.
5. Ensure idempotency and exactly one active artist owner.
6. Never mutate `dim_artista` or other warehouse tables.

## Artist permissions

| Stable role | Human label | Capabilities |
|---|---|---|
| `owner` | Propietario | all Artist Space actions; owner-only safeguards |
| `administrator` | Administrador | profile, catalog, submit, team, invitations, access review |
| `member` | Colaborador | view; create/edit drafts; no submit/team management |
| `reader` | Solo lectura | view only |

New permission codes:

- `artist_space.catalog.view`
- `artist_space.release.create`
- `artist_space.release.edit`
- `artist_space.release.submit`

Existing profile/team/invite/access permissions remain.

## State machines

### Artist access request

`pending → approved | rejected | cancelled`

Only pending requests mutate. Platform reviews claim/create. Artist owner/admin reviews request_access.

### Release submission

Reuse current state machine:

`draft → submitted → under_review → changes_requested | approved | rejected → scheduled → published`

Corrections from `changes_requested` return through resubmission. Status history remains append-only. Published content is immutable through draft-edit endpoints.

## Invariants

1. One profile has one non-sentinel backing organization.
2. One user has at most one active membership per artist.
3. At least one active owner exists for an active artist.
4. An Artist Space query always scopes by both authenticated user membership and artist profile.
5. A release artist profile belongs to the resolved organization.
6. A creator cannot approve their own release.
7. Publication is idempotent.
