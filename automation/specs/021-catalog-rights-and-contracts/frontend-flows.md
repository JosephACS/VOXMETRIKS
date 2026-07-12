# Frontend Flows — Spec 021

## Routes (`/catalog-rights/*`)
| Route | Page | Purpose |
|-------|------|---------|
| `/catalog-rights/assets` | CatalogAssetsListPage | List/register assets |
| `/catalog-rights/assets/:id` | CatalogAssetDetailPage | Asset detail, coverage, overlap detect, link warehouse |
| `/catalog-rights/releases` | CatalogReleasesListPage | List/create releases |
| `/catalog-rights/contracts` | RightsContractsListPage | List/create contracts |
| `/catalog-rights/contracts/:id` | RightsContractDetailPage | Parties, territories, uses, **approvals** |
| `/catalog-rights/contracts/:id/history` | RightsContractHistoryPage | Status history |
| `/catalog-rights/conflicts` | RightsConflictsListPage | List/resolve conflicts |

Coverage and approvals are embedded sections on asset-detail and contract-detail pages respectively (no separate top-level routes).

## Nav (dashboard)
Section "Catalog Rights" with links to Assets, Releases, Contracts, Conflicts.

## i18n keys
`nav.section.catalogRights`, `nav.catalogRights.assets`, `.releases`, `.contracts`, `.conflicts` (en + es).

## UI constraints
- Use `@if` / `@for` control flow (Angular 17+).
- Display read-only notice: records are tracked, not legal certification.
