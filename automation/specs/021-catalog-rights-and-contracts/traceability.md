# Traceability — Spec 021

| Use Case | Backend Class/Method | API Endpoint | Test |
|----------|---------------------|--------------|------|
| RegisterCatalogAsset | CatalogAssetUseCases.register | POST /assets | n2, n3 |
| LinkWarehouseTrack | CatalogAssetUseCases.link_warehouse_track | POST /assets/{id}/link-warehouse-track | n2, n3 |
| CreateRelease | CatalogReleaseUseCases.create | POST /releases | n2, n3 |
| LinkAssetArtist | CatalogAssetArtistUseCases.link | POST /assets/{id}/artists | n2, n3 |
| RegisterOwnership | CatalogOwnershipUseCases.record | POST /assets/{id}/ownership | n2 |
| CreateRightsContract | RightsContractUseCases.create | POST /contracts | n2, n3 |
| AddContractParty | RightsContractPartyUseCases.add | POST /contracts/{id}/parties | n2, n3 |
| SetTerritories | RightsTerritoryUseCases.set_territories | POST /contracts/{id}/territories | n2, n3 |
| SetAuthorizedUses | RightsAuthorizedUseUseCases.set_uses | POST /contracts/{id}/authorized-uses | n2, n3 |
| SubmitForApproval | RightsApprovalUseCases.submit | POST /contracts/{id}/submit-for-approval | n2, n3 |
| ApproveContract | RightsApprovalUseCases.decide | POST /contracts/{id}/approve | n2, n3 |
| DetectOverlap | RightsConflictUseCases.detect_overlap | POST /assets/{id}/detect-overlap | n2, n3 |
| OpenConflict | RightsConflictUseCases.open_conflict | POST /conflicts | n2, n3 |
| ResolveConflict | RightsConflictUseCases.resolve | POST /conflicts/{id}/resolve | n2, n3 |
| ArchiveContract | RightsContractUseCases.archive | POST /contracts/{id}/archive | n2, n3 |
| QueryRightsCoverage | RightsCoverageUseCases.query | GET /assets/{id}/coverage | n2, n3 |
| GetContractHistory | RightsHistoryUseCases.get_contract_history | GET /contracts/{id}/history | n2, n3 |

## Frontend mapping
| Page | Primary use cases |
|------|-------------------|
| catalog-assets-list | RegisterCatalogAsset, list |
| catalog-asset-detail | LinkWarehouseTrack, QueryRightsCoverage, DetectOverlap |
| catalog-releases-list | CreateRelease |
| rights-contracts-list | CreateRightsContract |
| rights-contract-detail | AddContractParty, SetTerritories, SetAuthorizedUses, Submit/Approve |
| rights-conflicts-list | ResolveConflict |
| rights-contract-history | GetContractHistory |
