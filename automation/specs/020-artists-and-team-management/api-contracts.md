# API Contracts — Spec 020

Base path: `/api/v1/artist-profiles` (see accepted-debt.md for why not
`/api/v1/artists`). All endpoints require `Authorization: Bearer <token>`
and `X-Organization-Id: <org id>` headers, and are RBAC-gated via
`require_org_artist_permission(<permission_code>)`.

## ArtistProfile
| Method | Path | Permission | Body | Response |
|---|---|---|---|---|
| GET | `/artist-profiles` | artist.view | query: status, page, page_size | `PaginatedArtists` |
| POST | `/artist-profiles` | artist.create | `ArtistProfileCreateRequest` | `ArtistProfileOut` (201) |
| GET | `/artist-profiles/{id}` | artist.view | — | `ArtistProfileOut` |
| POST | `/artist-profiles/{id}/activate` | artist.update | `ArtistTransitionRequest` | `ArtistProfileOut` |
| POST | `/artist-profiles/{id}/deactivate` | artist.update | `ArtistTransitionRequest` | `ArtistProfileOut` |
| POST | `/artist-profiles/{id}/archive` | artist.archive | `ArtistTransitionRequest` | `ArtistProfileOut` |
| POST | `/artist-profiles/{id}/link-warehouse` | artist.update | `LinkWarehouseArtistRequest` | `ArtistProfileOut` |
| POST | `/artist-profiles/{id}/transfer` | artist.transfer | `TransferOrganizationRequest` | `ArtistProfileOut` |
| GET | `/artist-profiles/{id}/history` | artist.view | — | `list[ArtistStatusHistoryOut]` |

## ArtistOrganization
| Method | Path | Permission | Body | Response |
|---|---|---|---|---|
| GET | `/artist-profiles/{id}/organizations` | artist.view | — | `list[ArtistOrganizationOut]` |
| POST | `/artist-profiles/{id}/organizations` | artist.update | `LinkOrganizationRequest` | `ArtistOrganizationOut` (201) |

## ArtistAssignment
| Method | Path | Permission | Body | Response |
|---|---|---|---|---|
| GET | `/artist-profiles/{id}/assignments` | artist.view | — | `list[ArtistAssignmentOut]` |
| POST | `/artist-profiles/{id}/assignments` | artist.assign | `AssignManagerRequest` | `ArtistAssignmentOut` (201) |
| POST | `/artist-profiles/{id}/assignments/{assignment_id}/end` | artist.assign | — | `ArtistAssignmentOut` |

## ArtistTeamMember
| Method | Path | Permission | Body | Response |
|---|---|---|---|---|
| GET | `/artist-profiles/{id}/team` | artist.view | — | `list[ArtistTeamMemberOut]` |
| POST | `/artist-profiles/{id}/team` | artist.assign | `AddTeamMemberRequest` | `ArtistTeamMemberOut` (201) |
| POST | `/artist-profiles/{id}/team/{member_id}/remove` | artist.assign | — | `ArtistTeamMemberOut` |

## ArtistExternalIdentifier
| Method | Path | Permission | Body | Response |
|---|---|---|---|---|
| GET | `/artist-profiles/{id}/external-identifiers` | artist.view | — | `list[ArtistExternalIdentifierOut]` |
| POST | `/artist-profiles/{id}/external-identifiers` | artist.update | `SetExternalIdentifierRequest` | `ArtistExternalIdentifierOut` (201) |

## Error mapping
`ArtistsError` subclasses map to HTTP codes via
`presentation/error_mapping.py`:
`NotFoundError → 404`, `ValidationError → 400`,
`DuplicateArtistError/ConflictError/ExternalIdentifierConflictError → 409`,
`InvalidTransitionError → 409`, `WarehouseArtistNotFoundError → 404`,
`PersistenceError → 503`. Missing `X-Organization-Id` → 400. Missing
permission → 403.
