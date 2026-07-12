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
