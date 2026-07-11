import { AudioSource } from '../../shared/models/api.models';

/** Provider identifiers returned by the backend Audio Resolver. */
export type AudioProviderId = 'youtube' | 'audius' | 'demo' | 'pending' | 'none';

/** Normalized playback source — engine-agnostic. */
export interface ResolvedPlaybackSource {
  trackId: number;
  provider: AudioProviderId;
  status: AudioSource['status'];
  youtubeVideoId?: string;
  streamUrl?: string;
  confidenceScore?: number | null;
}

export const RESOLVE_FRIENDLY_ERROR =
  'No se encontró una fuente reproducible para esta canción.';

export function mapAudioSourceResponse(src: AudioSource): ResolvedPlaybackSource {
  const provider = normalizeProvider(src.provider);
  const youtubeVideoId =
    src.youtube_video_id ?? (provider === 'youtube' ? src.source_ref ?? undefined : undefined);
  const streamUrl =
    provider === 'audius' && src.playable_url ? src.playable_url : undefined;

  return {
    trackId: src.track_id,
    provider,
    status: src.status,
    youtubeVideoId: youtubeVideoId ?? undefined,
    streamUrl,
    confidenceScore: src.confidence_score,
  };
}

function normalizeProvider(raw: string): AudioProviderId {
  if (raw === 'youtube' || raw === 'audius' || raw === 'demo' || raw === 'pending') {
    return raw;
  }
  return 'none';
}

export function isPlayableSource(src: ResolvedPlaybackSource): boolean {
  if (src.status !== 'ok') return false;
  if (src.provider === 'youtube') return !!src.youtubeVideoId;
  if (src.provider === 'audius') return !!src.streamUrl;
  return false;
}
