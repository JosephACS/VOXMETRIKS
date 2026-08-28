// ─── Modelos base — alineados con backend FastAPI/DuckDB ─────────────────────

export interface Artista {
  id_artista: number;
  nombre_artista: string;
}
export type Artist = Artista;

export interface Genero {
  id_genero: number;
  nombre_genero: string;
}
export type Genre = Genero;

export interface Track {
  id_track: number;
  spotify_track_id?: string;
  nombre_track: string;
  id_artista?: number;
  id_album?: number;
  id_genero?: number;
  explicit?: boolean;
  duration_ms?: number;
  popularity?: number;
  nombre_artista?: string;
  nombre_genero?: string;
}

export interface AudioSource {
  track_id: number;
  provider: string;
  source_ref?: string | null;
  playable_url?: string | null;
  query?: string | null;
  status: 'ok' | 'not_found' | 'disabled' | 'pending' | 'error';
  confidence_score?: number | null;
}

export interface CoverArt {
  track_id: number;
  image_url?: string | null;
  status: 'ok' | 'not_found';
}

export interface ArtistCoverArt {
  artist_id: number;
  image_url?: string | null;
  status: 'ok' | 'not_found';
}

export interface AudioFeatures {
  id_fact: number;
  id_track?: number;
  popularity?: number;
  danceability?: number;
  energy?: number;
  loudness?: number;
  speechiness?: number;
  acousticness?: number;
  instrumentalness?: number;
  liveness?: number;
  valence?: number;
  tempo?: number;
  key_col?: number;
  mode_col?: number;
  time_signature?: number;
}
export type TrackFeatures = AudioFeatures;

export interface TopArtista {
  id_artista: number;
  nombre_artista?: string;
  promedio_popularidad?: number;
  total_tracks?: number;
}

export interface GeneroPopularidad {
  id_genero: number;
  nombre_genero?: string;
  popularidad_promedio?: number;
  energia_promedio?: number;
  total_tracks?: number;
  total_artistas?: number;
}

export interface CatalogGrowthPoint {
  label: string;
  total: number;
  added: number;
}

export interface DistribucionEnergia {
  rango_energia: string;
  cantidad_tracks?: number;
  popularidad_promedio?: number;
  danceability_promedio?: number;
}
export type EnergyDistribution = DistribucionEnergia;

export interface PaginatedResponse<T> {
  total: number;
  page: number;
  limit: number;
  items: T[];
}
export type PaginatedArtists = PaginatedResponse<Artista>;
export type PaginatedTracks  = PaginatedResponse<Track>;
export type PaginatedGenres  = PaginatedResponse<Genero>;

export interface ArtistSearchParams {
  page?: number;
  limit?: number;
  search?: string;
  genre_id?: number;
}

export interface TrackSearchParams {
  page?: number;
  limit?: number;
  search?: string;
  artist_id?: number;
  genre_id?: number;
  playable_only?: boolean;
}

export interface GenreSearchParams {
  page?: number;
  limit?: number;
  search?: string;
}

// Stats Summary — /api/v1/stats/summary
export interface StatsSummary {
  total_tracks: number;
  total_artistas: number;
  total_generos: number;
  total_albumes: number;
  total_events?: number;
  total_streams?: number;
  total_audio_features?: number;
  active_users?: number;
  total_playlists?: number;
  skip_rate?: number;
  completion_rate?: number;
  engagement_score?: number;
  promedio_popularidad?: number;
  promedio_danceability?: number;
  promedio_energy?: number;
  promedio_valence?: number;
  promedio_tempo?: number;
  tracks_scope?: string;
  artists_scope?: string;
  albums_scope?: string;
  playlists_scope?: string;
  streams_scope?: string;
  events_scope?: string;
  events_updated_at?: string | null;
  events_classification_totals?: Record<string, number> | null;
}

export interface EventsBreakdownRow {
  table: string;
  row_count: number;
  kind: string;
  category: string;
  origin: string;
  classification: 'real' | 'imported' | 'demo' | 'synthetic' | 'unknown' | string;
  updated_at?: string | null;
  pct_of_total: number;
}

export interface EventsBreakdown {
  total_events: number;
  formula: string;
  activity_fact_tables: string[];
  tables: EventsBreakdownRow[];
  classification_totals: Record<string, number>;
  classification_basis?: string;
  latest_load?: {
    modo?: string | null;
    estado?: string | null;
    fecha_carga?: string | null;
    total_raw?: number | null;
  };
  updated_at?: string | null;
  generated_at?: string;
  tooltip?: string;
}

export interface WarehouseStatus {
  pipeline_status: string;
  db_size_mb: number;
  layers: {
    bronze: { file: string; size_mb: number };
    silver: { file: string; size_mb: number };
    gold: {
      parquet_dir: string;
      parquet_files: number;
      dimensions: Record<string, number>;
      facts: Record<string, number>;
      aggregates: Record<string, number>;
      total_rows: number;
    };
  };
  kpis: Record<string, number>;
  last_load?: LoadRecord | null;
  recent_stages?: Array<{
    stage: string; layer: string; duration_ms: number;
    rows_in: number; rows_out: number; status: string;
  }>;
}

export interface TrendingAnalytics {
  top_tracks: Array<{
    id_track: number; nombre_track?: string;
    recommendation_score?: number; engagement_score?: number; popularity?: number;
  }>;
  top_genres: Array<{
    id_genero: number; nombre_genero?: string;
    streams_7d?: number; trend_pct?: number; avg_popularity?: number;
  }>;
  daily_streams: Array<{ fecha: string; total_streams?: number; unique_users?: number; skip_count?: number }>;
  trending_score_avg: number;
}

export interface PlatformAnalytics {
  devices: Array<{ device_type: string; stream_count?: number; unique_users?: number; share_pct?: number }>;
  platform_usage: Array<{ platform: string; device_type?: string; session_count?: number; total_streams?: number; share_pct?: number }>;
  active_users: number;
  sessions: number;
  total_streams: number;
}

export interface EngagementAnalytics {
  skip_rate: number;
  completion_rate: number;
  avg_session_time_min: number;
  engagement_score?: number | null;
  user_segments: Array<{ segment: string; user_count?: number; avg_plays?: number; retention_pct?: number }>;
  user_retention: Array<{ cohort_week: string; week_1_pct?: number; week_2_pct?: number; week_4_pct?: number }>;
  top_searches: Array<{ query_text: string; search_count?: number }>;
  recommendation_avg?: number;
}

export interface ImportResult {
  status: string;
  rows_loaded: number;
  rows_bronze: number;
  rows_silver: number;
  elapsed_s: number;
  warehouse: string;
  source: string;
}

export interface SyntheticResult {
  before: number;
  after: number;
  created: number;
  target_total: number;
  source_rows: number;
  track_total?: number;
  purged_synthetic_tracks?: number;
  activity_counts?: Record<string, number>;
  dimensions?: Record<string, number>;
  batches?: number;
  warning?: string | null;
}

export interface SyntheticLimits {
  max_target_total: number;
  max_create_per_run: number;
  warn_create_above: number;
  batch_size: number;
  duckdb_note: string;
}
export type SummaryStats = StatsSummary;

// Top Tracks — /api/v1/stats/top-tracks
export interface TopTrack {
  id_track: number;
  nombre_track?: string;
  nombre_artista?: string;
  id_artista?: number;
  id_genero?: number;
  popularity?: number;
  energy?: number;
  danceability?: number;
  valence?: number;
  total_streams?: number | null;
  engagement_score?: number | null;
}

// Load Records — /api/v1/stats/loads (matches backend ctl_carga_dataset)
export interface LoadRecord {
  id_carga?: number;
  fecha_carga?: string;
  modo?: string;
  registros_nuevos?: number;
  total_raw?: number;
  estado?: string;
}
export type LoadStats = LoadRecord;

// Artist Stats
export interface ArtistStats {
  id_artista: number;
  nombre_artista?: string;
  promedio_popularidad?: number;
  total_tracks?: number;
}

// CRUD payloads
export interface ArtistaCreate {
  nombre_artista: string;
}
export interface ArtistaUpdate {
  nombre_artista: string;
}

export interface GeneroCreate {
  nombre_genero: string;
}
export interface GeneroUpdate {
  nombre_genero: string;
}

export interface TrackCreate {
  nombre_track: string;
  spotify_track_id?: string;
  id_artista?: number;
  id_album?: number;
  id_genero?: number;
  explicit?: boolean;
  duration_ms?: number;
}
export interface TrackUpdate {
  nombre_track?: string;
  spotify_track_id?: string;
  id_artista?: number;
  id_album?: number;
  id_genero?: number;
  explicit?: boolean;
  duration_ms?: number;
}

export interface DeleteResponse {
  deleted: boolean;
  id: number;
}

// ── Streaming app: playlists & favorites ─────────────────────────────────────

export interface PlaylistSummary {
  id: number;
  name: string;
  description?: string;
  created_at?: string;
  total_tracks: number;
  cover_track_id?: number | null;
  /** Up to 4 track ids for Spotify-style mosaic covers. */
  preview_track_ids?: number[];
  /** "catalog" for warehouse dim_playlist; omit/mine for personal. */
  source?: string;
}

export interface PlaylistTrackItem {
  id_track: number;
  nombre_track?: string;
  id_artista?: number;
  id_genero?: number;
  duration_ms?: number;
  popularity?: number;
  nombre_artista?: string;
  nombre_genero?: string;
  playback_status?: string;
  source_unavailable?: boolean;
}

export interface PlaylistDetail extends PlaylistSummary {
  tracks: PlaylistTrackItem[];
}

export interface PlaylistCreate {
  name: string;
  description?: string;
}

export interface PlaylistUpdate {
  name?: string;
  description?: string;
}

export interface WarehouseTableMeta {
  name: string;
  kind: string;
  layer: string;
  row_count: number;
  columns: { name: string; type: string }[];
}

export interface TablePreview {
  table: string;
  total: number;
  page: number;
  limit: number;
  columns: string[];
  rows: Record<string, unknown>[];
  query: string;
}

export interface RecommendationPayload {
  for_you: {
    id_track?: number;
    id_artista?: number;
    nombre_track?: string;
    nombre_artista?: string;
    nombre_genero?: string;
    recommendation_score?: number;
    popularity?: number;
  }[];
  artists: {
    id_artista?: number;
    nombre_artista?: string;
    promedio_popularidad?: number;
    total_tracks?: number;
    affinity?: number;
  }[];
  genres: { genre?: string; score?: number; total_tracks?: number }[];
  moods: { id?: string; name?: string; description?: string; tracks?: number }[];
  mood_filter?: string | null;
  mood_label?: string | null;
  mood_tracks?: {
    id_track?: number;
    id_artista?: number;
    nombre_track?: string;
    nombre_artista?: string;
    nombre_genero?: string;
    popularity?: number;
    energy?: number;
    recommendation_score?: number;
  }[];
  mood_count?: number;
}

export interface HealthResponse {
  status: string;
  version: string;
  table_count: number;
  database?: string | null;
  tables?: string[];
}

export interface FavoriteTrack extends PlaylistTrackItem {
  added_at?: string;
}

export interface TrackSearchResult extends PlaylistTrackItem {
  spotify_track_id?: string;
}

export interface TrackDetail {
  id_track: number;
  spotify_track_id?: string;
  nombre_track?: string;
  id_artista?: number;
  id_album?: number;
  id_genero?: number;
  explicit?: boolean;
  duration_ms?: number;
  popularity?: number;
  danceability?: number;
  energy?: number;
  loudness?: number;
  speechiness?: number;
  acousticness?: number;
  instrumentalness?: number;
  liveness?: number;
  valence?: number;
  tempo?: number;
  nombre_artista?: string;
  nombre_genero?: string;
}

export interface HistoryEntry {
  id?: number;
  id_track: number;
  nombre_track: string;
  nombre_artista?: string;
  viewed_at: string;
  played_at?: string;
  event_key?: string;
  progress_ms?: number;
  listened_ms?: number;
  completed?: boolean;
  source?: string | null;
  duration_ms?: number | null;
}

export interface AuditRecord {
  id_auditoria?: number;
  accion?: string;
  tabla_afectada?: string;
  fecha_evento?: string;
  detalles?: string;
}

export interface PipelineStageRecord {
  run_id?: number;
  stage?: string;
  layer?: string;
  started_at?: string;
  duration_ms?: number;
  rows_in?: number;
  rows_out?: number;
  status?: string;
  details?: string;
}

export interface StreamingHistoryItem {
  id_streaming?: number;
  fecha_evento?: string;
  device_type?: string;
  platform?: string;
  id_track?: number;
  nombre_track?: string;
  nombre_artista?: string;
  nombre_genero?: string;
}

export interface UserHistoryEvent {
  event_type?: string;
  label?: string;
  fecha_evento?: string;
  detalle?: string;
  device_type?: string;
  id_track?: number;
  nombre_track?: string;
  nombre_artista?: string;
}

export interface UserHistoryPayload {
  user_id?: number;
  warehouse_user_id?: number;
  sessions?: UserHistoryEvent[];
  favorites?: UserHistoryEvent[];
  activity?: UserHistoryEvent[];
  timeline?: UserHistoryEvent[];
}

export interface SearchHistoryEntry {
  query: string;
  searched_at: string;
  track_count?: number;
  artist_count?: number;
}

export interface WarehouseSearchItem {
  id_search?: number;
  query?: string;
  results_count?: number;
  fecha_evento?: string;
}

export interface HistoryHub {
  search: WarehouseSearchItem[];
  user: UserHistoryPayload | null;
}

// ── Users (Package 2) ────────────────────────────────────────────────────────

export interface UserPreferences {
  dark_mode: boolean;
  audio_quality: string;
  recommendations_enabled: boolean;
  privacy_public: boolean;
  /** Opt-in UI hint for reduced presentation navigation. */
  presentation_nav?: boolean;
  presentation_role?: string;
  demo?: boolean;
  language?: string;
}

export interface AppUser {
  id: number;
  username: string;
  email: string;
  role?: 'user' | 'engineer' | 'admin' | string;
  plan: string;
  favorite_genre?: string;
  created_at?: string;
  preferences?: UserPreferences;
  email_verified?: boolean;
  auth_provider?: string;
}

export interface AuthConfig {
  google_client_id: string;
  email_verification_enabled: boolean;
}

export type UserPublic = AppUser;

export interface UserStats {
  favorites_count: number;
  playlists_count: number;
}

export interface UserProfile extends AppUser {
  stats: UserStats;
  playlists: PlaylistSummary[];
}

export interface AuthResponse {
  token: string;
  user: AppUser;
}

export interface UserPreferencesUpdate {
  dark_mode?: boolean;
  audio_quality?: string;
  recommendations_enabled?: boolean;
  privacy_public?: boolean;
  favorite_genre?: string;
}
