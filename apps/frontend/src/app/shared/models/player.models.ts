export interface PlayableTrack {
  id: number;
  title: string;
  artist: string;
  artistId?: number;
  durationMs?: number;
  /** Stream / preview URL once resolved — empty until a real source is known. */
  audioUrl: string;
  coverGradient: string;
  explicit?: boolean;
  /** Resolved YouTube video id for real full-length playback (lazy-loaded). */
  youtubeVideoId?: string;
}

/** Playback engine status (transport). */
export type PlaybackStatus = 'idle' | 'loading' | 'playing' | 'paused' | 'buffering' | 'error';

/** Audio source resolve lifecycle (user-facing). */
export type AudioResolvePhase =
  | 'idle'
  | 'resolving'
  | 'ready'
  | 'playing'
  | 'failed'
  | 'unavailable';

export type RepeatMode = 'off' | 'all' | 'one';

export interface PlayerState {
  track: PlayableTrack | null;
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  volume: number;
  shuffle: boolean;
  repeat: boolean;
}
