import { Injectable } from '@angular/core';

/**
 * Thin wrapper around the official YouTube IFrame Player API.
 *
 * Plays real, full-length tracks through YouTube's player (free, ToS-compliant
 * — we never download or re-host audio). The iframe sits in a 1×1 invisible
 * in-viewport container (opacity 0, not display:none) so playback stays alive
 * when the tab is in the background; we drive it via the public API.
 */
declare global {
  interface Window {
    // YouTube IFrame API is injected at runtime.
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    YT?: any;
    onYouTubeIframeAPIReady?: () => void;
  }
}

const CONTAINER_ID = 'vox-yt-player';
const API_SCRIPT_ID = 'vox-yt-iframe-api';

@Injectable({ providedIn: 'root' })
export class YoutubeEngineService {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private player: any = null;
  private ready = false;
  private creating = false;
  private volume = 85; // 0–100
  private desired: { videoId: string; autoplay: boolean } | null = null;

  /** Event hooks wired by the consumer (MusicPlayerService). */
  onPlay: (() => void) | null = null;
  onPause: (() => void) | null = null;
  onEnded: (() => void) | null = null;
  onError: (() => void) | null = null;
  onBuffering: (() => void) | null = null;

  /** Cue/load a video. Autoplay starts immediately; otherwise it's just cued. */
  load(videoId: string, autoplay: boolean): void {
    this.desired = { videoId, autoplay };
    this.ensureApi();
    if (this.ready && this.player) this.applyLoad();
  }

  play(): void {
    if (this.ready && this.player) this.player.playVideo();
  }

  pause(): void {
    if (this.ready && this.player) this.player.pauseVideo();
  }

  stop(): void {
    if (this.ready && this.player) this.player.stopVideo();
  }

  seekTo(seconds: number): void {
    if (this.ready && this.player) this.player.seekTo(Math.max(0, seconds), true);
  }

  setVolume(vol0to100: number): void {
    this.volume = Math.max(0, Math.min(100, Math.round(vol0to100)));
    if (this.ready && this.player) this.player.setVolume(this.volume);
  }

  getCurrentTime(): number {
    return this.ready && this.player ? (this.player.getCurrentTime() || 0) : 0;
  }

  getDuration(): number {
    return this.ready && this.player ? (this.player.getDuration() || 0) : 0;
  }

  // ── internals ──────────────────────────────────────────────────────────────

  private applyLoad(): void {
    if (!this.desired || !this.player) return;
    const { videoId, autoplay } = this.desired;
    if (autoplay) this.player.loadVideoById(videoId);
    else this.player.cueVideoById(videoId);
  }

  private ensureApi(): void {
    if (typeof window === 'undefined' || typeof document === 'undefined') return;
    if (this.player || this.creating) return;
    this.creating = true;
    this.ensureContainer();

    if (window.YT && window.YT.Player) {
      this.createPlayer();
      return;
    }

    const prev = window.onYouTubeIframeAPIReady;
    window.onYouTubeIframeAPIReady = () => {
      prev?.();
      this.createPlayer();
    };

    if (!document.getElementById(API_SCRIPT_ID)) {
      const tag = document.createElement('script');
      tag.id = API_SCRIPT_ID;
      tag.src = 'https://www.youtube.com/iframe_api';
      document.body.appendChild(tag);
    }
  }

  private ensureContainer(): void {
    if (document.getElementById(CONTAINER_ID)) return;
    const wrap = document.createElement('div');
    // Keep the iframe in-viewport and "alive" — off-screen / display:none can
    // make browsers or YouTube pause background playback.
    wrap.style.position = 'absolute';
    wrap.style.left = '0';
    wrap.style.top = '0';
    wrap.style.width = '1px';
    wrap.style.height = '1px';
    wrap.style.opacity = '0';
    wrap.style.overflow = 'hidden';
    wrap.style.pointerEvents = 'none';
    wrap.style.zIndex = '-1';
    wrap.setAttribute('aria-hidden', 'true');

    const inner = document.createElement('div');
    inner.id = CONTAINER_ID;
    wrap.appendChild(inner);
    document.body.appendChild(wrap);
  }

  private createPlayer(): void {
    if (this.player || !window.YT?.Player) return;
    this.player = new window.YT.Player(CONTAINER_ID, {
      height: '180',
      width: '320',
      playerVars: {
        autoplay: 0,
        controls: 0,
        disablekb: 1,
        modestbranding: 1,
        rel: 0,
        playsinline: 1,
        iv_load_policy: 3,
      },
      events: {
        onReady: () => this.handleReady(),
        onStateChange: (e: { data?: number }) => this.handleState(e),
        onError: () => this.onError?.(),
      },
    });
  }

  private handleReady(): void {
    this.ready = true;
    this.player.setVolume(this.volume);
    if (this.desired) this.applyLoad();
  }

  private handleState(e: { data?: number }): void {
    // YT.PlayerState: -1 unstarted, 0 ended, 1 playing, 2 paused, 3 buffering, 5 cued
    switch (e?.data) {
      case 1:
        this.onPlay?.();
        break;
      case 2:
        this.onPause?.();
        break;
      case 0:
        this.onEnded?.();
        break;
      case 3:
        this.onBuffering?.();
        break;
    }
  }
}
