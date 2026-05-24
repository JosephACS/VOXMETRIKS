export interface PlayableTrack {
  id: number;
  title: string;
  artist: string;
  durationMs?: number;
  audioUrl: string;
  coverGradient: string;
  explicit?: boolean;
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
