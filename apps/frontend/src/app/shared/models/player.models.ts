export interface PlayableTrack {
  id: number;
  title: string;
  artist: string;
  artistId?: number;
  durationMs?: number;
  audioUrl: string;
  coverGradient: string;
  explicit?: boolean;
  /** Resolved YouTube video id for real full-length playback (lazy-loaded). */
  youtubeVideoId?: string;
}

export type PlaybackStatus = 'idle' | 'loading' | 'playing' | 'paused' | 'buffering' | 'error';

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
