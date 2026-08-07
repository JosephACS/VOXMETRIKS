export interface HealthStatus {
  status: string;
  labeled_academic: boolean;
  message: string;
  components: Record<string, string>;
}

export interface FeatureFlag {
  id: number;
  flag_key: string;
  description: string;
  enabled: boolean;
  environment: string;
}

export interface ProviderConfig {
  id: number;
  provider_code: string;
  display_name: string;
  is_mock: boolean;
  secret_ref_redacted?: string;
  status: string;
}

export interface BackgroundJob {
  id: number;
  job_code: string;
  display_name: string;
  status: string;
}

export interface BackupRecord {
  id: number;
  backup_type: string;
  status: string;
  file_path: string;
  labeled_academic: boolean;
}

export interface UnresolvedAudioItem {
  track_id: number;
  provider: string;
  status: string;
  query?: string | null;
  resolved_at?: string | null;
  failure_count: number;
  track_name?: string | null;
  artist_name?: string | null;
  duration_ms?: number | null;
}

export interface UnresolvedAudioList {
  items: UnresolvedAudioItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface AudioCandidate {
  video_id: string;
  title: string;
  duration_sec?: number;
  channel_title?: string;
  query?: string;
  score?: number;
  accepted?: boolean;
}

export interface AudioCandidatesResponse {
  track_id: number;
  track_name: string;
  artist_name: string;
  duration_ms?: number | null;
  candidates: AudioCandidate[];
}
