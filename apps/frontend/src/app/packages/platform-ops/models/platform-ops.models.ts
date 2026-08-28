export interface HealthStatus {
  status: string;
  labeled_academic: boolean;
  message: string;
  components: Record<string, string>;
}

export type PlatformOpsQueueCode =
  | 'artist_requests'
  | 'catalog_reviews'
  | 'audio_unresolved'
  | 'incidents';

export interface PlatformOpsQueue {
  code: PlatformOpsQueueCode;
  count: number | null;
  availability: 'available' | 'unavailable';
  severity: 'normal' | 'attention' | 'critical';
}

export interface PlatformOpsOverview {
  health: 'healthy' | 'degraded' | 'unavailable';
  generated_at: string;
  queues: PlatformOpsQueue[];
  next_queue: PlatformOpsQueueCode | null;
  has_pending_work: boolean;
}

export const PLATFORM_OPS_QUEUE_PATHS: Record<PlatformOpsQueueCode, string> = {
  artist_requests: '/platform-ops/artist-requests',
  catalog_reviews: '/platform-ops/catalog-reviews',
  audio_unresolved: '/platform-ops/audio-unresolved',
  incidents: '/platform-ops/incidents',
};

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

export interface OperationalIncident {
  id: number;
  title: string;
  severity: string;
  status: string;
  description: string;
  reported_by: number;
  reported_at: string;
  resolved_at?: string | null;
  created_at: string;
  updated_at: string;
}
