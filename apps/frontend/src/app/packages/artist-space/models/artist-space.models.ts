/** Spec 046 — Artist Space models. Extended by Spec 051 (professional journey). */
export type ArtistMembershipRole = 'owner' | 'administrator' | 'member' | 'reader';

export type ArtistSpacePermission =
  | 'artist_space.view'
  | 'artist_space.profile.update'
  | 'artist_space.team.manage'
  | 'artist_space.access.review'
  | 'artist_space.invite'
  | 'artist_space.catalog.view'
  | 'artist_space.release.create'
  | 'artist_space.release.edit'
  | 'artist_space.release.submit';

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

export type ArtistRequestType = 'claim_ownership' | 'request_access' | 'create_new';

/** Server-validated relationship between the applicant and the artist. */
export type ArtistRelationshipType =
  | 'artist_self'
  | 'manager'
  | 'label_representative'
  | 'collaborator';

export const ARTIST_RELATIONSHIP_TYPES: readonly ArtistRelationshipType[] = [
  'artist_self',
  'manager',
  'label_representative',
  'collaborator',
];

export interface ArtistAccessRequest {
  id: number;
  applicant_user_id: number;
  request_type: ArtistRequestType;
  target_artist_profile_id: number | null;
  warehouse_artist_id: number | null;
  proposed_display_name: string | null;
  proposed_role: string;
  status: string;
  created_at: string;
  reviewed_at: string | null;
  reviewer_user_id: number | null;
  rejection_reason: string | null;
  relationship_type?: ArtistRelationshipType | null;
  evidence_url?: string | null;
  evidence_note?: string | null;
}

export interface ArtistInvitation {
  id: number;
  email_normalized: string;
  role: string;
  status: string;
  expires_at: string;
  created_at: string;
  updated_at: string;
}

export interface ArtistTeamMember {
  id: number;
  artist_profile_id: number;
  user_id: number;
  role: ArtistMembershipRole | string;
  status: string;
  email?: string | null;
  display_name?: string | null;
  permissions?: string[];
}

/** Server-authoritative discovery state (051 contract). */
export type ArtistManagementState = 'unmanaged' | 'managed' | 'member' | 'pending';

/** Exactly one action the caller may take on a discovery candidate. */
export type ArtistDiscoveryAction =
  | 'claim_ownership'
  | 'request_access'
  | 'open_space'
  | 'view_request'
  | 'none';

export interface ArtistDiscoveryItem {
  warehouse_artist_id: number;
  display_name: string;
  image_url: string | null;
  management_state: ArtistManagementState;
  allowed_action: ArtistDiscoveryAction;
  artist_profile_id: number | null;
  request_id: number | null;
  request_status: string | null;
}

export interface ArtistDiscoveryResponse {
  items: ArtistDiscoveryItem[];
  total: number;
}

export interface ArtistExternalIdentifier {
  system_code: string;
  external_value: string;
}

export interface ArtistProfileDetail {
  id: number;
  organization_id: number;
  display_name: string;
  legal_name: string | null;
  bio?: string | null;
  country_code?: string | null;
  primary_genre?: string | null;
  website_url?: string | null;
  image_url?: string | null;
  warehouse_artist_id: number | null;
  membership_role: ArtistMembershipRole | string;
  permissions: string[];
  external_identifiers: ArtistExternalIdentifier[];
}

export interface ArtistProfilePatchBody {
  display_name?: string;
  legal_name?: string | null;
  bio?: string | null;
  country_code?: string | null;
  primary_genre?: string | null;
  website_url?: string | null;
  image_url?: string | null;
  external_identifiers?: ArtistExternalIdentifier[];
}

export interface ArtistAccessRequestCreateBody {
  request_type: ArtistRequestType;
  warehouse_artist_id?: number | null;
  target_artist_profile_id?: number | null;
  proposed_display_name?: string | null;
  proposed_role?: string | null;
  relationship_type?: ArtistRelationshipType | null;
  evidence_url?: string | null;
  evidence_note?: string | null;
  accuracy_attested?: boolean;
}

/** Roles an owner/administrator may hand out; ownership transfer is out of scope. */
export const ARTIST_ASSIGNABLE_ROLES: readonly ArtistMembershipRole[] = [
  'administrator',
  'member',
  'reader',
];

const ROLE_LABEL_KEYS: Record<ArtistMembershipRole, string> = {
  owner: 'artistSpace.role.owner',
  administrator: 'artistSpace.role.administrator',
  member: 'artistSpace.role.member',
  reader: 'artistSpace.role.reader',
};

/** Human role label key — never render the raw backend role code. */
export function artistRoleLabelKey(role: string | null | undefined): string {
  const normalized = (role ?? '').trim().toLowerCase();
  return ROLE_LABEL_KEYS[normalized as ArtistMembershipRole] ?? 'artistSpace.role.unknown';
}

export function artistManagementStateLabelKey(state: string | null | undefined): string {
  const normalized = (state ?? '').trim().toLowerCase();
  switch (normalized) {
    case 'unmanaged':
    case 'managed':
    case 'member':
    case 'pending':
      return `artistSpace.discovery.state.${normalized}`;
    default:
      return 'artistSpace.discovery.state.unknown';
  }
}

export function artistDiscoveryActionLabelKey(
  action: string | null | undefined,
): string {
  const normalized = (action ?? '').trim().toLowerCase();
  switch (normalized) {
    case 'claim_ownership':
      return 'artistSpace.discovery.action.claimOwnership';
    case 'request_access':
      return 'artistSpace.discovery.action.requestAccess';
    case 'open_space':
      return 'artistSpace.discovery.action.openSpace';
    case 'view_request':
      return 'artistSpace.discovery.action.viewRequest';
    default:
      return 'artistSpace.discovery.action.none';
  }
}

export function artistRequestTypeLabelKey(type: string | null | undefined): string {
  const normalized = (type ?? '').trim().toLowerCase();
  switch (normalized) {
    case 'claim_ownership':
      return 'artistSpace.request.type.claimOwnership';
    case 'request_access':
      return 'artistSpace.request.type.requestAccess';
    case 'create_new':
      return 'artistSpace.request.type.createNew';
    default:
      return 'artistSpace.request.type.unknown';
  }
}

export function artistRequestStatusLabelKey(status: string | null | undefined): string {
  const normalized = (status ?? '').trim().toLowerCase();
  switch (normalized) {
    case 'pending':
    case 'approved':
    case 'rejected':
    case 'cancelled':
      return `artistSpace.request.status.${normalized}`;
    default:
      return 'artistSpace.request.status.unknown';
  }
}

export function artistRelationshipLabelKey(
  relationship: string | null | undefined,
): string {
  const normalized = (relationship ?? '').trim().toLowerCase();
  switch (normalized) {
    case 'artist_self':
      return 'artistSpace.relationship.artistSelf';
    case 'manager':
      return 'artistSpace.relationship.manager';
    case 'label_representative':
      return 'artistSpace.relationship.labelRepresentative';
    case 'collaborator':
      return 'artistSpace.relationship.collaborator';
    default:
      return 'artistSpace.relationship.unknown';
  }
}

export function canAccessArtistPermission(
  permissions: readonly string[] | null | undefined,
  required: ArtistSpacePermission | string,
): boolean {
  if (!permissions?.length) return false;
  return permissions.includes(required);
}

/** `https://` (or `http://`) absolute URL check used by profile/evidence forms. */
export function isHttpUrl(value: string | null | undefined): boolean {
  const raw = (value ?? '').trim();
  if (!raw) return false;
  try {
    const parsed = new URL(raw);
    return parsed.protocol === 'https:' || parsed.protocol === 'http:';
  } catch {
    return false;
  }
}
