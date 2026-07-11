import {
  FavoriteTrack,
  HistoryEntry,
  TopTrack,
  Track,
  TrackSearchResult,
} from '../../shared/models/api.models';
import { PlayableTrack } from '../../shared/models/player.models';
import { demoAudioUrlForTrack } from '../../shared/config/demo-audio.config';
import { CoverArtService } from '../../shared/services/cover-art.service';
import {
  playableFromTopTrack,
  playableFromTrack,
} from '../../shared/services/player/player-track.factory';
import { displayTrackTitle } from '../../shared/utils/track-display.util';
import { primaryArtistName } from '../../shared/utils/artist.util';

/** Canonical PlayableTrack builders — single source for UI surfaces. */
export function toPlayableFromTrack(
  coverArt: CoverArtService,
  t: Track,
  artistName?: string,
): PlayableTrack {
  return playableFromTrack(coverArt, t, artistName);
}

export function toPlayableFromTopTrack(coverArt: CoverArtService, t: TopTrack): PlayableTrack {
  return playableFromTopTrack(coverArt, t);
}

export function toPlayableFromHistory(coverArt: CoverArtService, h: HistoryEntry): PlayableTrack {
  return {
    id: h.id_track,
    title: displayTrackTitle(h.nombre_track),
    artist: primaryArtistName(h.nombre_artista) || '—',
    audioUrl: demoAudioUrlForTrack(h.id_track),
    coverGradient: coverArt.gradientFor(h.id_track),
  };
}

export function toPlayableFromSearch(coverArt: CoverArtService, r: TrackSearchResult): PlayableTrack {
  return {
    id: r.id_track,
    title: displayTrackTitle(r.nombre_track),
    artist: primaryArtistName(r.nombre_artista) || '—',
    artistId: r.id_artista,
    durationMs: r.duration_ms,
    audioUrl: demoAudioUrlForTrack(r.id_track),
    coverGradient: coverArt.gradientFor(r.id_track),
  };
}

export function toPlayableFromFavorite(coverArt: CoverArtService, t: FavoriteTrack): PlayableTrack {
  return {
    id: t.id_track,
    title: t.nombre_track ?? '—',
    artist: t.nombre_artista ?? '—',
    durationMs: t.duration_ms,
    audioUrl: demoAudioUrlForTrack(t.id_track),
    coverGradient: coverArt.gradientFor(t.id_track),
  };
}
