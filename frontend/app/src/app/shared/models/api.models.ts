/**
 * VOXMETRIK_V2 — API Models
 *
 * Interfaces TypeScript sincronizadas con los modelos Pydantic del backend.
 * Fuente de verdad para tipado HTTP en toda la aplicación.
 *
 * Mapeo:
 * - Artist / Artista       → backend/schemas/models.py::Artista
 * - Track                  → backend/schemas/models.py::Cancion / dim_track
 * - Genre / Genero         → backend/schemas/models.py::Genero
 * - SummaryStats           → backend/stats_service.py::get_summary()
 * - EnergyDistribution     → backend/schemas/models.py::DistribucionEnergia (agg_distribucion_energia)
 * - TopArtista             → backend/schemas/models.py::TopArtista (agg_top_artistas)
 * - GenreStats             → backend/schemas/models.py::GeneroPopularidad (agg_genero_popularidad)
 * - LoadStats              → backend/schemas/models.py::EstadisticasCarga (ctl_carga_dataset)
 */

// ═══════════════════════════════════════════════════════════════════════════
// ARTISTS / ARTISTAS
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Modelo: Artist
 * Mapea: backend/schemas/models.py::Artista
 * Endpoint: GET /api/v1/artists
 */
export interface Artist {
  id_artista: number;
  nombre_artista: string;
  popularidad: number | null;
  seguidores: number | null;
  generos: string[] | null;
  url_imagen: string | null;
  url_spotify: string | null;
  fecha_creacion: string | null;
}

/**
 * Alias — componentes existentes importan `Artista`
 */
export type Artista = Artist;

/**
 * Modelo: TopArtista
 * Mapea: agg_top_artistas
 * Endpoint: GET /api/v1/artists/top
 */
export interface TopArtista {
  id_artista: number;
  nombre_artista: string | null;
  promedio_popularidad: number | null;
  total_tracks: number | null;
}

/**
 * Modelo: ArtistStats
 * Respuesta: GET /api/v1/artists/{id}/stats
 */
export interface ArtistStats {
  id_artista: number;
  nombre_artista: string;
  total_canciones: number;
  popularidad_promedio: number | null;
  energia_promedio: number | null;
  danzabilidad_promedio: number | null;
  acousticness_promedio: number | null;
  speechiness_promedio: number | null;
  instrumentalness_promedio: number | null;
  liveness_promedio: number | null;
  valence_promedio: number | null;
  tempo_promedio: number | null;
  duracion_promedio: number | null;
}

/**
 * Modelo: PaginatedArtists
 * Respuesta paginada: GET /api/v1/artists?page=1&limit=10
 */
export interface PaginatedArtists {
  items: Artist[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

/**
 * Alias genérico — componentes usan PaginatedResponse<Artista>
 */
export type PaginatedResponse<T> = {
  items: T[];
  total: number;
  page: number;
  limit: number;
  pages?: number;
};

// ═══════════════════════════════════════════════════════════════════════════
// TRACKS / CANCIONES
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Modelo: Track
 * Mapea: dim_track + fact_audio_features
 * Endpoint: GET /api/v1/tracks
 */
export interface Track {
  id_track: number;
  spotify_track_id: string | null;
  nombre_track: string;
  id_artista: number | null;
  id_album: number | null;
  id_genero: number | null;
  explicit: boolean | null;
  duration_ms: number | null;
  // Campos de audio features (si el backend los incluye en el JOIN)
  popularity?: number | null;
  energy?: number | null;
  danceability?: number | null;
  valence?: number | null;
}

/**
 * Modelo: TopTrack
 * Mapea: fact_audio_features JOIN dim_track
 * Endpoint: GET /api/v1/stats/top-tracks
 */
export interface TopTrack {
  id_track: number;
  nombre_track: string;
  id_artista: number | null;
  id_genero: number | null;
  popularity: number;
  energy: number | null;
  danceability: number | null;
  valence: number | null;
}

/**
 * Modelo: TrackFeatures
 * Respuesta: GET /api/v1/tracks/{id}/features
 */
export interface TrackFeatures {
  id_cancion: number;
  nombre_cancion: string;
  energia: number | null;
  danzabilidad: number | null;
  acousticness: number | null;
  speechiness: number | null;
  instrumentalness: number | null;
  liveness: number | null;
  valence: number | null;
  tempo: number | null;
  key: number | null;
  mode: number | null;
  time_signature: number | null;
}

/**
 * Modelo: PaginatedTracks
 * Respuesta paginada: GET /api/v1/tracks
 */
export interface PaginatedTracks {
  items: Track[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

// ═══════════════════════════════════════════════════════════════════════════
// GENRES / GÉNEROS
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Modelo: Genre
 * Mapea: dim_genero
 * Endpoint: GET /api/v1/genres
 */
export interface Genre {
  id_genero: number;
  nombre_genero: string;
  fecha_creacion: string | null;
}

/** Alias — componentes importan `Genero` */
export type Genero = Genre;

/**
 * Modelo: GenreStats
 * Mapea: agg_genero_popularidad
 * Endpoint: GET /api/v1/genres/stats
 */
export interface GenreStats {
  id_genero: number;
  nombre_genero: string | null;
  total_tracks: number | null;
  total_artistas: number | null;
  popularidad_promedio: number | null;
  energia_promedio: number | null;
}

/**
 * Aliases — componentes importan ambas formas
 */
export type GeneroPopularidad = GenreStats;

/**
 * Modelo: PaginatedGenres
 * Respuesta paginada: GET /api/v1/genres
 */
export interface PaginatedGenres {
  items: Genre[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

// ═══════════════════════════════════════════════════════════════════════════
// STATISTICS / ESTADÍSTICAS
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Modelo: SummaryStats
 * Respuesta: GET /api/v1/stats/summary
 * Resumen general del data warehouse.
 */
export interface SummaryStats {
  total_tracks: number;
  total_artistas: number;
  total_generos: number;
  total_albums: number;
  total_audio_features: number;
  fecha_ultima_actualizacion?: string | null;
}

/**
 * Alias — dashboard.component.ts importa `StatsSummary`
 */
export type StatsSummary = SummaryStats;

/**
 * Modelo: EnergyDistribution
 * Mapea: agg_distribucion_energia
 * Endpoint: GET /api/v1/stats/energia
 */
export interface EnergyDistribution {
  rango_energia: string;
  cantidad_tracks: number | null;
  popularidad_promedio: number | null;
  danceability_promedio: number | null;
}

/**
 * Aliases — componentes usan ambas formas
 */
export type DistribucionEnergia = EnergyDistribution;

/**
 * Modelo: LoadRecord
 * Mapea: ctl_carga_dataset
 * Endpoint: GET /api/v1/stats/loads
 */
export interface LoadRecord {
  id_carga: number;
  fecha_carga: string;
  modo: string;
  registros_nuevos: number | null;
  total_raw: number | null;
  estado: string;
}

/**
 * Alias — legacy
 */
export type LoadStats = LoadRecord;
export type EstadisticasCarga = LoadRecord;

// ═══════════════════════════════════════════════════════════════════════════
// QUERY PARAMETERS / PARÁMETROS DE BÚSQUEDA
// ═══════════════════════════════════════════════════════════════════════════

export interface PaginationParams {
  page?: number;
  limit?: number;
  skip?: number;
}

export interface ArtistSearchParams extends PaginationParams {
  search?: string;
  genre_id?: number;
}

export interface TrackSearchParams extends PaginationParams {
  search?: string;
  artist_id?: number;
  genre_id?: number;
}

export interface GenreSearchParams extends PaginationParams {
  search?: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// RESPONSE WRAPPERS / HELPERS
// ═══════════════════════════════════════════════════════════════════════════

export interface ApiError {
  detail: string | string[];
  status?: number;
}

export type ListResponse<T> = T[];
export type SingleResponse<T> = T;
