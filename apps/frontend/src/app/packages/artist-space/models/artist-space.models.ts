/** Spec 046 — Artist Space models */
export type ArtistMembershipRole = 'owner' | 'administrator' | 'member' | 'reader';

export type ArtistSpacePermission =
  | 'artist_space.view'
  | 'artist_space.profile.update'
  | 'artist_space.team.manage'
  | 'artist_space.access.review'
  | 'artist_space.invite';

export interface ArtistSpaceMineItem {
  artist_profile_id: number;
  warehouse_artist_id: number | null;
  display_name: string;
  image_url: string | null;
  membership_role: ArtistMembershipRole;
  membership_status: string;
  permissions: string[];
  organization_id: number;
}

export interface ArtistSpaceSummary {
  artist_profile_id: number;
  display_name: string;
  membership_role: string;
  team_size: number;
  pending_access_requests: number;
  track_count: number;
  organization_id: number;
  warehouse_artist_id: number | null;
}

export interface ArtistAccessRequest {
  id: number;
  applicant_user_id: number;
  request_type: 'claim_ownership' | 'request_access' | 'create_new';
  target_artist_profile_id: number | null;
  warehouse_artist_id: number | null;
  proposed_display_name: string | null;
  proposed_role: string;
  status: string;
  created_at: string;
  reviewed_at: string | null;
  reviewer_user_id: number | null;
  rejection_reason: string | null;
}

export function canAccessArtistPermission(
  permissions: readonly string[] | null | undefined,
  required: ArtistSpacePermission | string,
): boolean {
  if (!permissions?.length) return false;
  return permissions.includes(required);
}
