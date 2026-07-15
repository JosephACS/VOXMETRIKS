/** Spec 031 catalog publishing API models. */

export type ReleaseSubmissionStatus =
  | 'draft'
  | 'submitted'
  | 'under_review'
  | 'changes_requested'
  | 'approved'
  | 'scheduled'
  | 'published'
  | 'suspended'
  | 'rejected'
  | 'withdrawn'
  | 'archived'
  | string;

export interface ReleaseSubmission {
  id: number;
  organization_id: number;
  artist_profile_id: number;
  release_type: string;
  title: string;
  status: ReleaseSubmissionStatus;
  created_by: number;
  is_demo?: boolean;
  cover_media_id?: number | null;
  rights_contract_id?: number | null;
  catalog_asset_id?: number | null;
  planned_release_date?: string | null;
  published_at?: string | null;
  scheduled_at?: string | null;
  version?: string | null;
  label_name?: string | null;
  genre?: string | null;
  language?: string | null;
  explicit?: boolean;
  upc?: string | null;
  actual_release_date?: string | null;
  reject_reason?: string | null;
  withdraw_reason?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface SubmissionTrack {
  id: number;
  submission_id: number;
  title: string;
  version?: string | null;
  track_number: number;
  disc_number?: number;
  primary_artist_id?: number | null;
  duration_ms?: number | null;
  isrc?: string | null;
  explicit?: boolean;
  audio_media_id?: number | null;
  catalog_asset_id?: number | null;
  rights_contract_id?: number | null;
  warehouse_track_id?: number | null;
  validation_status?: string | null;
  sort_order?: number;
  created_at?: string;
  updated_at?: string;
}

export interface SubmissionContributor {
  id: number;
  submission_id: number;
  track_id?: number | null;
  party_role: string;
  artist_profile_id?: number | null;
  display_name: string;
  created_at?: string;
}

export interface ReviewIssue {
  id: number;
  severity: string;
  code: string;
  message: string;
  field_ref?: string | null;
  resolved?: boolean;
  created_at?: string;
}

export interface ReleaseDetail {
  submission: ReleaseSubmission;
  tracks: SubmissionTrack[];
  contributors: SubmissionContributor[];
  issues: ReviewIssue[];
}

export interface StatusHistoryEntry {
  id: number;
  submission_id: number;
  from_status: string;
  to_status: string;
  actor_user_id: number;
  reason?: string | null;
  created_at: string;
}

export interface PortalSummary {
  organization_id: number;
  artist_profile_ids: number[];
  status_counts: Record<string, number>;
}

export interface ValidateReadyResult {
  submission_id: number;
  ready: boolean;
  blockers: string[];
  track_count: number;
  duplicates: { title?: string; isrc?: string }[];
}

export interface DraftCreateBody {
  artist_profile_id: number;
  title: string;
  release_type?: string;
  version?: string | null;
  label_name?: string | null;
  genre?: string | null;
  language?: string | null;
  explicit?: boolean;
  planned_release_date?: string | null;
  upc?: string | null;
  rights_contract_id?: number | null;
  idempotency_key?: string | null;
  is_demo?: boolean;
}

export interface MetadataUpdateBody {
  title?: string;
  version?: string | null;
  label_name?: string | null;
  genre?: string | null;
  language?: string | null;
  explicit?: boolean;
  planned_release_date?: string | null;
  actual_release_date?: string | null;
  upc?: string | null;
  release_type?: string;
  rights_contract_id?: number | null;
}

export interface TrackCreateBody {
  title: string;
  track_number?: number;
  disc_number?: number;
  version?: string | null;
  isrc?: string | null;
  explicit?: boolean;
  duration_ms?: number | null;
  rights_contract_id?: number | null;
  warehouse_track_id?: number | null;
}

export interface ContributorCreateBody {
  party_role: string;
  display_name: string;
  track_id?: number | null;
  artist_profile_id?: number | null;
}

/** Map backend status → primary UI label bucket. */
export function publishingUiBucket(
  status: string,
): 'draft' | 'in_review' | 'published' | 'other' {
  const s = (status || '').toLowerCase();
  if (s === 'draft') return 'draft';
  if (s === 'published') return 'published';
  if (
    s === 'submitted' ||
    s === 'under_review' ||
    s === 'changes_requested' ||
    s === 'approved' ||
    s === 'scheduled'
  ) {
    return 'in_review';
  }
  return 'other';
}

export function publishingPrimaryLabelKey(status: string): string {
  const bucket = publishingUiBucket(status);
  if (bucket === 'draft') return 'publishing.status.draft';
  if (bucket === 'published') return 'publishing.status.published';
  if (bucket === 'in_review') return 'publishing.status.inReview';
  return `status.${status}`;
}

export function hasPrivateMedia(
  submission: ReleaseSubmission,
  tracks: SubmissionTrack[] = [],
): boolean {
  if ((submission.status || '').toLowerCase() === 'published') return false;
  return tracks.some((t) => !!t.audio_media_id) || !!submission.cover_media_id;
}
