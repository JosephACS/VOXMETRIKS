import { Track } from '../../../shared/models/api.models';

export interface SmartTrackItem {
  id_track: number;
  nombre_track?: string;
  nombre_artista?: string;
  id_artista?: number;
  popularity?: number;
  score?: number;
  reason?: string;
  similarity?: number;
  content_similarity?: number;
  cover_url?: string | null;
  mix_tag?: string;
}

export interface SmartHomeSection {
  id: string;
  type: 'track_rail' | 'playlist' | 'because';
  /** Stable system code (e.g. discover_weekly). Prefer over title for i18n. */
  code?: string;
  /** Legacy display title — only used when code is absent (user content / old API). */
  title?: string;
  subtitle?: string;
  subtitle_code?: string;
  week?: string;
  title_params?: Record<string, string | number>;
  reason_type?: string;
  tracks: SmartTrackItem[];
}

export interface SmartArtistItem {
  id_artista: number;
  nombre_artista?: string;
  similarity?: number;
  same_genre?: boolean;
  popularity?: number;
}

export interface AudioDna {
  energetic?: number;
  dance?: number;
  acoustic?: number;
  instrumental?: number;
  positive?: number;
}

export interface MusicalProfile {
  user_id: number;
  top_genres: { id_genero: number; nombre_genero: string; plays: number }[];
  top_artists: { id_artista: number; nombre_artista: string; plays: number }[];
  top_tracks: SmartTrackItem[];
  hours_listened: number;
  minutes_listened: number;
  favorite_track?: SmartTrackItem;
  audio_dna: AudioDna;
}

export interface SmartHomeResponse {
  user_id: number;
  profile: MusicalProfile;
  sections: SmartHomeSection[];
}

export function smartItemToTrack(item: SmartTrackItem): Track {
  return {
    id_track: item.id_track,
    nombre_track: item.nombre_track ?? `Track ${item.id_track}`,
    nombre_artista: item.nombre_artista ?? undefined,
    id_artista: item.id_artista,
    popularity: item.popularity,
  };
}
