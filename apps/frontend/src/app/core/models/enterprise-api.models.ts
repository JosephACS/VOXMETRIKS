/** Enterprise API envelope + domain types (FastAPI /api/v1). */

export interface ApiMeta {
  count?: number;
  limit?: number;
  page?: number;
  page_size?: number;
  total?: number;
  source?: string;
}

export interface ApiResponse<T> {
  status: string;
  data: T;
  meta?: ApiMeta;
}

export interface GenreTrend {
  id_genero: number;
  nombre_genero: string;
  streams_7d: number;
  trend_pct: number;
}

export interface DeviceUsage {
  platform: string;
  device_type: string;
  total_streams: number;
  share_pct: number;
}

export interface GrowthTrendPoint {
  fecha: string;
  total_streams: number;
  unique_users: number;
}

export interface ArtistGrowth {
  id_artista: number;
  nombre_artista: string;
  streams_7d: number;
  growth_pct: number;
  total_followers?: number;
  streams_30d?: number;
}

export interface DashboardOverview {
  total_streams: number;
  active_users: number;
  top_genres: GenreTrend[];
  top_artists: ArtistGrowth[];
  device_usage: DeviceUsage[];
  growth_trends: GrowthTrendPoint[];
}

export interface StreamSeriesPoint {
  fecha: string;
  total_streams: number;
  unique_users: number;
  skip_count?: number;
  avg_duration_ms?: number;
}

export interface PeakHour {
  hour_of_day: number;
  stream_count: number;
}

export interface StreamsAnalytics {
  start_date: string;
  end_date: string;
  series: StreamSeriesPoint[];
  peak_hours: PeakHour[];
  trending_artists: ArtistGrowth[];
  top_genres: GenreTrend[];
  device_breakdown: DeviceUsage[];
}

export interface TopTrack {
  id_track: number;
  nombre_track: string;
  nombre_artista: string;
  nombre_genero?: string | null;
  popularity: number;
  total_streams: number;
  energy?: number | null;
  danceability?: number | null;
}

export interface UserInsights {
  user_id: number;
  engagement_score: number;
  total_plays: number;
  skips: number;
  favorites: number;
  segment?: string | null;
}

export interface TrackRecommendation {
  track_id: number;
  score: number;
  reason: string;
  track_name?: string;
  popularity?: number;
  engagement_score?: number;
}
