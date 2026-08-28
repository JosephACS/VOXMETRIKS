import { AudioSource } from '../../shared/models/api.models';

/** Providers used by the playback path. Spotify is resolved client-side. */
export type AudioProviderId =
  | 'spotify'
  | 'deezer'
  | 'demo'
  | 'preview'
  | 'local_published'
  | 'pending'
  | 'none';

/** Normalized playback source — engine-agnostic. */
export interface ResolvedPlaybackSource {
  trackId: number;
  provider: AudioProviderId;
  status: AudioSource['status'];
  streamUrl?: string;
  spotifyUri?: string;
  confidenceScore?: number | null;
}

export const RESOLVE_FRIENDLY_ERROR =
  'Esta canción no está disponible temporalmente.';

export type AudioAvailability =
  | 'ok'
  | 'pending'
  | 'failed'
  | 'unavailable'
  | 'restricted';

export function availabilityFromSource(src: ResolvedPlaybackSource): AudioAvailability {
  if (src.status === 'pending') return 'pending';
  if (src.status === 'disabled') return 'restricted';
  if (src.status === 'error') return 'failed';
  if (isPlayableSource(src)) return 'ok';
  return 'unavailable';
}

export function mapAudioSourceResponse(src: AudioSource): ResolvedPlaybackSource {
  const provider = normalizeProvider(src.provider);
  const streamUrl =
    ['deezer', 'demo', 'preview', 'local_published'].includes(provider) && src.playable_url
      ? src.playable_url
      : undefined;

  return {
    trackId: src.track_id,
    provider,
    status: src.status,
    streamUrl,
    confidenceScore: src.confidence_score,
  };
}

function normalizeProvider(raw: string): AudioProviderId {
  if (
    raw === 'spotify' ||
    raw === 'deezer' ||
    raw === 'demo' ||
    raw === 'preview' ||
    raw === 'pending' ||
    raw === 'local_published'
  ) {
    return raw;
  }
  return 'none';
}

export function isPlayableSource(src: ResolvedPlaybackSource): boolean {
  if (src.status !== 'ok') return false;
  if (src.provider === 'spotify') return !!src.spotifyUri;
  if (
    src.provider === 'deezer' ||
    src.provider === 'local_published' ||
    src.provider === 'preview' ||
    src.provider === 'demo'
  ) {
    return !!src.streamUrl;
  }
  return false;
}
