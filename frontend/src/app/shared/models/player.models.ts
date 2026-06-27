export interface PlayableTrack {
  id: number;
  title: string;
  artist: string;
  durationMs?: number;
  audioUrl: string;
  coverGradient: string;
  explicit?: boolean;
  /** Resolved YouTube video id for real full-length playback (lazy-loaded). */
  youtubeVideoId?: string;
}

export interface PlayerState {
  track: PlayableTrack | null;
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  volume: number;
  shuffle: boolean;
  repeat: boolean;
}
