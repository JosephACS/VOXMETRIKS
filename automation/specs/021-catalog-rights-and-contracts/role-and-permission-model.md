# Role and Permission Model — Spec 021

## Permissions
| Code | Description |
|------|-------------|
| `rights.view` | View assets, contracts, coverage, history, conflicts |
| `rights.create` | Register assets/releases; create contracts, parties, territories, uses |
| `rights.update` | Link warehouse tracks; submit for approval |
| `rights.approve` | Approve or reject rights contracts |
| `rights.conflict` | Detect, open, resolve conflicts |
| `rights.archive` | Archive rights contracts |

## Role matrix
| Role | Permissions |
|------|-------------|
| owner | all `rights.*` |
| administrator | view, create, update, approve, conflict, archive |
| artist_manager | view, create, update |
| finance | view |
| viewer | view |

Seeded in `apps/backend/app/packages/organizations/infrastructure/catalogs.py`.
