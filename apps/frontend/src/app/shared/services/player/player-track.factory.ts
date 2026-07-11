import { TopTrack, Track } from '../../models/api.models';
import { PlayableTrack } from '../../models/player.models';
import { demoAudioUrlForTrack } from '../../config/demo-audio.config';
import { primaryArtistName } from '../../utils/artist.util';
import { displayTrackTitle, displayTrackSubtitle } from '../../utils/track-display.util';
import { CoverArtService } from '../cover-art.service';

export function playableFromTrack(
  coverArt: CoverArtService,
  t: Track,
  artistName?: string,
): PlayableTrack {
  const artist = t.nombre_artista?.trim()
    ? primaryArtistName(t.nombre_artista)
    : (artistName?.trim() || '—');
  return {
    id: t.id_track,
    title: displayTrackTitle(t.nombre_track),
    artist: displayTrackSubtitle(artist, t.nombre_genero, t.id_track),
    artistId: t.id_artista,
    durationMs: t.duration_ms,
    audioUrl: demoAudioUrlForTrack(t.id_track),
    coverGradient: coverArt.gradientFor(t.id_track),
    explicit: t.explicit,
  };
}

export function playableFromTopTrack(coverArt: CoverArtService, t: TopTrack): PlayableTrack {
  return {
    id: t.id_track,
    title: displayTrackTitle(t.nombre_track),
    artist: displayTrackSubtitle(t.nombre_artista, undefined, t.id_track),
    artistId: t.id_artista,
    audioUrl: demoAudioUrlForTrack(t.id_track),
    coverGradient: coverArt.gradientFor(t.id_track),
  };
}

export function formatPlaybackTime(sec: number): string {
  if (!Number.isFinite(sec)) return '0:00';
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}
