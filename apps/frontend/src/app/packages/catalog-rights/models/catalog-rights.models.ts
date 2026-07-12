/** Catalog Rights & Contracts domain models — Spec 021. */

export interface CatalogAsset {
  id: number;
  organization_id: number;
  title: string;
  status: 'draft' | 'active' | 'inactive' | 'archived';
  warehouse_track_id: number | null;
  artist_profile_id: number | null;
  created_by: number | null;
  created_at: string;
  updated_at: string;
}

export interface PaginatedAssets {
  items: CatalogAsset[];
  total: number;
  page: number;
  page_size: number;
}

export interface CatalogRelease {
  id: number;
  organization_id: number;
  title: string;
  warehouse_album_id: number | null;
  created_by: number | null;
  created_at: string;
  updated_at: string;
}

export interface PaginatedReleases {
  items: CatalogRelease[];
  total: number;
  page: number;
  page_size: number;
}

export interface CatalogAssetArtist {
  id: number;
  asset_id: number;
  artist_profile_id: number;
  role: string;
  created_at: string;
}

export interface CatalogOwnership {
  id: number;
  asset_id: number;
  organization_id: number | null;
  artist_profile_id: number | null;
  ownership_type: string;
  created_by: number | null;
  created_at: string;
  updated_at: string;
}

export type RightsType = 'master' | 'publishing' | 'neighboring' | 'other';
export type ContractStatus = 'draft' | 'active' | 'expired' | 'archived' | 'disputed';

export interface RightsContract {
  id: number;
  organization_id: number;
  asset_id: number;
  rights_type: RightsType;
  status: ContractStatus;
  exclusive: boolean;
  valid_from: string;
  valid_to: string | null;
  evidence_ref: string | null;
  created_by: number | null;
  created_at: string;
  updated_at: string;
}

export interface PaginatedContracts {
  items: RightsContract[];
  total: number;
  page: number;
  page_size: number;
}

export interface RightsContractParty {
  id: number;
  contract_id: number;
  party_name: string;
  party_type: string;
  ownership_percentage: number;
  organization_id: number | null;
  artist_profile_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface RightsConflict {
  id: number;
  organization_id: number;
  asset_id: number;
  rights_type: string;
  territory_code: string;
  status: 'open' | 'resolved' | 'dismissed';
  details: string | null;
  resolved_by: number | null;
  resolved_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface AddContractPartyResponse {
  party: RightsContractParty;
  conflicts_opened: RightsConflict[];
}

export interface RightsTerritory {
  id: number;
  contract_id: number;
  territory_code: string;
  territory_name: string;
  created_at: string;
}

export interface SetTerritoriesResponse {
  territories: RightsTerritory[];
  conflicts_opened: RightsConflict[];
}

export interface RightsAuthorizedUse {
  id: number;
  contract_id: number;
  use_code: string;
  description: string | null;
  created_at: string;
}

export interface RightsApproval {
  id: number;
  contract_id: number;
  organization_id: number;
  status: 'pending' | 'approved' | 'rejected';
  approver_user_id: number | null;
  requested_by: number | null;
  notes: string | null;
  decided_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface RightsCoverageRow {
  asset_id: number;
  rights_type: string;
  territory_code: string;
  total_percentage: number;
  contract_count: number;
  has_conflict: boolean;
}

export interface RightsStatusHistoryEntry {
  id: number;
  organization_id: number;
  entity_type: string;
  entity_id: number;
  from_status: string | null;
  to_status: string;
  actor: number | null;
  reason: string | null;
  at: string;
  created_at: string;
}
