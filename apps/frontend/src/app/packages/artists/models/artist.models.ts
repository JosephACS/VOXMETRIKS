/** Artists & Team Management domain models — Spec 020. */

export interface ArtistProfile {
  id: number;
  organization_id: number;
  display_name: string;
  legal_name: string | null;
  normalized_name: string;
  status: 'draft' | 'active' | 'inactive' | 'archived';
  warehouse_artist_id: number | null;
  created_by: number | null;
  created_at: string;
  updated_at: string;
}

export interface ArtistOrganizationLink {
  id: number;
  artist_id: number;
  organization_id: number;
  relationship_role: 'primary' | 'secondary' | 'licensed' | 'partner';
  is_primary: boolean;
  status: 'active' | 'ended';
  created_at: string;
  updated_at: string;
}

export interface ArtistAssignment {
  id: number;
  artist_id: number;
  organization_id: number;
  user_id: number;
  role: string;
  status: 'active' | 'ended';
  assigned_at: string;
  ended_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ArtistTeamMember {
  id: number;
  artist_id: number;
  organization_id: number;
  user_id: number;
  team_role: string;
  status: 'active' | 'removed';
  added_at: string;
  removed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ArtistExternalIdentifier {
  id: number;
  artist_id: number;
  system_code: string;
  external_value: string;
  created_at: string;
  updated_at: string;
}

export interface ArtistStatusHistoryEntry {
  id: number;
  artist_id: number;
  organization_id: number;
  from_status: string | null;
  to_status: string;
  reason: string | null;
  actor_user_id: number | null;
  at: string;
  created_at: string;
}

export interface PaginatedArtists {
  items: ArtistProfile[];
  total: number;
  page: number;
  page_size: number;
}
