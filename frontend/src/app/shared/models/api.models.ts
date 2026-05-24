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
  total_streams?: number;
  total_audio_features?: number;
  promedio_popularidad?: number;
  promedio_danceability?: number;
  promedio_energy?: number;
  promedio_valence?: number;
  promedio_tempo?: number;
}

export interface SyntheticResult {
  before: number;
  after: number;
  created: number;
  source_rows: number;
  multiplier: number;
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
}

export interface PlaylistDetail extends PlaylistSummary {
  tracks: PlaylistTrackItem[];
}

export interface PlaylistCreate {
  name: string;
  description?: string;
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
  id_track: number;
  nombre_track: string;
  nombre_artista?: string;
  viewed_at: string;
}

// ── Users (Package 2) ────────────────────────────────────────────────────────

export interface UserPreferences {
  dark_mode: boolean;
  audio_quality: string;
  recommendations_enabled: boolean;
  privacy_public: boolean;
}

export interface AppUser {
  id: number;
  username: string;
  email: string;
  plan: string;
  favorite_genre?: string;
  created_at?: string;
  preferences?: UserPreferences;
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
