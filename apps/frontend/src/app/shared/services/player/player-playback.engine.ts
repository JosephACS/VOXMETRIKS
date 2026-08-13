import { YoutubeEngineService } from '../youtube-engine.service';

export interface PlaybackEngineHooks {
  onEnded: () => void;
  onYtPlay: () => void;
  onYtPause: () => void;
  onYtEnded: () => void;
  onYtError: () => void;
  onYtBuffering: () => void;
  onDemoMetadata: (duration: number) => void;
  onDemoWaiting: () => void;
  onDemoPlaying: () => void;
}

/** HTML Audio + YouTube engine coordination. */
export class PlayerPlaybackEngine {
  readonly audio = new Audio();
  private usingYt = false;
  private loadedTrackId: number | null = null;
  private activeYoutubeVideoId: string | null = null;
  private tickTimer: ReturnType<typeof setInterval> | null = null;

  constructor(
    private readonly yt: YoutubeEngineService,
    hooks: PlaybackEngineHooks,
  ) {
    this.audio.preload = 'metadata';
    this.audio.addEventListener('ended', () => {
      if (!this.usingYt) hooks.onEnded();
    });
    this.audio.addEventListener('loadedmetadata', () => {
      if (!this.usingYt) hooks.onDemoMetadata(this.audio.duration || 0);
    });
    this.audio.addEventListener('waiting', () => {
      if (!this.usingYt) hooks.onDemoWaiting();
    });
    this.audio.addEventListener('playing', () => {
      if (!this.usingYt) hooks.onDemoPlaying();
    });

    this.yt.onPlay = () => { if (this.usingYt) hooks.onYtPlay(); };
    this.yt.onPause = () => { if (this.usingYt) hooks.onYtPause(); };
    this.yt.onEnded = () => { if (this.usingYt) hooks.onYtEnded(); };
    this.yt.onError = () => { if (this.usingYt) hooks.onYtError(); };
    this.yt.onBuffering = () => { if (this.usingYt) hooks.onYtBuffering(); };
  }

  get isYoutube(): boolean {
    return this.usingYt;
  }

  get currentYoutubeVideoId(): string | null {
    return this.usingYt ? this.activeYoutubeVideoId : null;
  }

  get loadedId(): number | null {
    return this.loadedTrackId;
  }

  setVolume(vol: number): void {
    this.audio.volume = vol;
    this.yt.setVolume(vol * 100);
  }

  primeDemo(url: string): void {
    this.audio.src = url;
  }

  startYoutube(videoId: string, autoplay: boolean): void {
    this.usingYt = true;
    this.activeYoutubeVideoId = videoId;
    this.audio.pause();
    this.yt.load(videoId, autoplay);
  }

  startDemo(url: string, trackId: number, autoplay: boolean): Promise<boolean> {
    this.usingYt = false;
    this.activeYoutubeVideoId = null;
    this.loadedTrackId = trackId;
    this.yt.stop();
    this.audio.src = url;
    if (!autoplay) return Promise.resolve(true);
    return this.audio.play().then(() => true).catch(() => false);
  }

  markLoaded(trackId: number, youtube: boolean): void {
    this.loadedTrackId = trackId;
    this.usingYt = youtube;
  }

  pause(): void {
    if (this.usingYt) this.yt.pause();
    else this.audio.pause();
  }

  playDemo(): Promise<boolean> {
    return this.audio.play().then(() => true).catch(() => false);
  }

  playYoutube(): void {
    this.yt.play();
  }

  seek(seconds: number): number {
    const target = Math.max(0, seconds);
    if (this.usingYt) {
      this.yt.seekTo(target);
      return target;
    }
    this.audio.currentTime = target;
    return this.audio.currentTime;
  }

  getCurrentTime(): number {
    return this.usingYt ? (this.yt.getCurrentTime() || 0) : (this.audio.currentTime || 0);
  }

  getDuration(fallback: number): number {
    if (this.usingYt) return this.yt.getDuration() || fallback;
    return this.audio.duration || fallback;
  }

  stopAll(): void {
    this.audio.pause();
    try {
      this.audio.removeAttribute('src');
      this.audio.load();
    } catch { /* ignore */ }
    this.yt.stop();
    this.usingYt = false;
    this.activeYoutubeVideoId = null;
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
