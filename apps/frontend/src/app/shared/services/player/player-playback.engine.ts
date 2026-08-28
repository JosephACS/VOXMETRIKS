import { SpotifyPlaybackService } from '../../../core/integrations/spotify/spotify-playback.service';

export interface PlaybackEngineHooks {
  onEnded: () => void;
  onSpotifyPlay: () => void;
  onSpotifyPause: () => void;
  onSpotifyEnded: () => void;
  onSpotifyError: () => void;
  onDemoMetadata: (duration: number) => void;
  onDemoWaiting: () => void;
  onDemoPlaying: () => void;
}

/** HTML Audio for Deezer previews/local audio plus Spotify Web Playback SDK. */
export class PlayerPlaybackEngine {
  readonly audio = new Audio();
  private usingSpotify = false;
  private loadedTrackId: number | null = null;
  private tickTimer: ReturnType<typeof setInterval> | null = null;

  constructor(
    private readonly spotify: SpotifyPlaybackService,
    hooks: PlaybackEngineHooks,
  ) {
    this.audio.preload = 'metadata';
    this.audio.addEventListener('ended', () => {
      if (!this.usingSpotify) hooks.onEnded();
    });
    this.audio.addEventListener('loadedmetadata', () => {
      if (!this.usingSpotify) hooks.onDemoMetadata(this.audio.duration || 0);
    });
    this.audio.addEventListener('waiting', () => {
      if (!this.usingSpotify) hooks.onDemoWaiting();
    });
    this.audio.addEventListener('playing', () => {
      if (!this.usingSpotify) hooks.onDemoPlaying();
    });

    this.spotify.setHooks({
      onPlay: () => { if (this.usingSpotify) hooks.onSpotifyPlay(); },
      onPause: () => { if (this.usingSpotify) hooks.onSpotifyPause(); },
      onEnded: () => { if (this.usingSpotify) hooks.onSpotifyEnded(); },
      onError: () => { if (this.usingSpotify) hooks.onSpotifyError(); },
    });
  }

  get isSpotify(): boolean {
    return this.usingSpotify;
  }

  get loadedId(): number | null {
    return this.loadedTrackId;
  }

  setVolume(vol: number): void {
    this.audio.volume = vol;
    this.spotify.setVolume(vol);
  }

  primeDemo(url: string): void {
    this.audio.src = url;
  }

  startSpotify(uri: string, trackId: number, autoplay: boolean): Promise<boolean> {
    this.usingSpotify = true;
    this.loadedTrackId = trackId;
    this.audio.pause();
    return this.spotify.start(uri, autoplay);
  }

  startDemo(url: string, trackId: number, autoplay: boolean): Promise<boolean> {
    this.usingSpotify = false;
    this.loadedTrackId = trackId;
    this.audio.src = url;
    if (!autoplay) return Promise.resolve(true);
    return this.audio.play().then(() => true).catch(() => false);
  }

  markSpotifyLoaded(trackId: number): void {
    this.loadedTrackId = trackId;
    this.usingSpotify = true;
  }

  pause(): void {
    if (this.usingSpotify) this.spotify.pause();
    else this.audio.pause();
  }

  playDemo(): Promise<boolean> {
    return this.audio.play().then(() => true).catch(() => false);
  }

  playSpotify(): Promise<boolean> {
    return this.spotify.resume();
  }

  seek(seconds: number): number {
    const target = Math.max(0, seconds);
    if (this.usingSpotify) {
      this.spotify.seek(target);
      return target;
    }
    this.audio.currentTime = target;
    return this.audio.currentTime;
  }

  getCurrentTime(): number {
    return this.usingSpotify ? this.spotify.getCurrentTime() : (this.audio.currentTime || 0);
  }

  getDuration(fallback: number): number {
    return this.usingSpotify
      ? this.spotify.getDuration() || fallback
      : this.audio.duration || fallback;
  }

  stopAll(): void {
    this.audio.pause();
    try {
      this.audio.removeAttribute('src');
      this.audio.load();
    } catch { /* ignore */ }
    this.spotify.stop();
    this.usingSpotify = false;
    this.loadedTrackId = null;
  }

  startTick(onTick: () => void): void {
    if (this.tickTimer) clearInterval(this.tickTimer);
    this.tickTimer = setInterval(onTick, 250);
  }

  destroy(): void {
    if (this.tickTimer) clearInterval(this.tickTimer);
    this.stopAll();
  }
}
