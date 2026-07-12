# API Contracts — Spec 021

**Base:** `/api/v1/catalog-rights`  
**Headers:** `Authorization: Bearer <token>`, `X-Organization-Id: <org_id>`

## Catalog Assets
| Method | Path | Permission |
|--------|------|------------|
| GET | `/assets` | rights.view |
| POST | `/assets` | rights.create |
| GET | `/assets/{id}` | rights.view |
| POST | `/assets/{id}/link-warehouse-track` | rights.update |
| GET | `/assets/{id}/artists` | rights.view |
| POST | `/assets/{id}/artists` | rights.create |
| GET | `/assets/{id}/ownership` | rights.view |
| POST | `/assets/{id}/ownership` | rights.create |
| GET | `/assets/{id}/coverage` | rights.view |
| POST | `/assets/{id}/detect-overlap` | rights.conflict |

## Catalog Releases
| Method | Path | Permission |
|--------|------|------------|
| GET | `/releases` | rights.view |
| POST | `/releases` | rights.create |

## Rights Contracts
| Method | Path | Permission |
|--------|------|------------|
| GET | `/contracts` | rights.view |
| POST | `/contracts` | rights.create |
| GET | `/contracts/{id}` | rights.view |
| POST | `/contracts/{id}/archive` | rights.archive |
| GET | `/contracts/{id}/history` | rights.view |
| GET | `/contracts/{id}/parties` | rights.view |
| POST | `/contracts/{id}/parties` | rights.create |
| GET | `/contracts/{id}/territories` | rights.view |
| POST | `/contracts/{id}/territories` | rights.create |
| GET | `/contracts/{id}/authorized-uses` | rights.view |
| POST | `/contracts/{id}/authorized-uses` | rights.create |
| POST | `/contracts/{id}/submit-for-approval` | rights.update |
| POST | `/contracts/{id}/approve` | rights.approve |
| GET | `/contracts/{id}/approvals` | rights.view |

## Conflicts
| Method | Path | Permission |
|--------|------|------------|
| GET | `/conflicts` | rights.view |
| POST | `/conflicts` | rights.conflict |
| POST | `/conflicts/{id}/resolve` | rights.conflict |

## Response notes
- `POST .../parties` and `POST .../territories` return `conflicts_opened[]` when overlap >100%.
- Cross-tenant IDs return 404 (NotFoundError), not 403.
