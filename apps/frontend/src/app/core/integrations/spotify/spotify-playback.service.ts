import { Injectable, inject } from '@angular/core';
import { SpotifyIntegrationService } from './spotify-integration.service';

interface SpotifySdkState {
  paused: boolean;
  position: number;
  duration: number;
}

type SpotifySdkErrorEvent =
  | 'initialization_error'
  | 'authentication_error'
  | 'account_error'
  | 'playback_error';

interface SpotifySdkPlayer {
  addListener(event: 'ready', callback: (value: { device_id: string }) => void): boolean;
  addListener(event: 'not_ready', callback: () => void): boolean;
  addListener(event: SpotifySdkErrorEvent, callback: (value: { message?: string }) => void): boolean;
  addListener(event: 'player_state_changed', callback: (value: SpotifySdkState | null) => void): boolean;
  connect(): Promise<boolean>;
  disconnect(): void;
  pause(): Promise<void>;
  resume(): Promise<void>;
  seek(positionMs: number): Promise<void>;
  setVolume(volume: number): Promise<void>;
}

type SpotifyPlayerConstructor = new (options: {
    name: string;
    getOAuthToken: (callback: (token: string) => void) => void;
    volume?: number;
  }) => SpotifySdkPlayer;

declare global {
  interface Window {
    Spotify?: { Player: SpotifyPlayerConstructor };
    onSpotifyWebPlaybackSDKReady?: () => void;
  }
}

export interface SpotifyPlaybackHooks {
  onPlay: () => void;
  onPause: () => void;
  onEnded: () => void;
  onError: (message: string) => void;
}

/** Official Spotify Web Playback SDK adapter. No video element is created. */
@Injectable({ providedIn: 'root' })
export class SpotifyPlaybackService {
  private readonly integration = inject(SpotifyIntegrationService);
  private player: SpotifySdkPlayer | null = null;
  private deviceId: string | null = null;
  private state: SpotifySdkState | null = null;
  private currentUri: string | null = null;
  private readyPromise: Promise<void> | null = null;
  private hooks: SpotifyPlaybackHooks = {
    onPlay: () => undefined,
    onPause: () => undefined,
    onEnded: () => undefined,
    onError: () => undefined,
  };

  setHooks(hooks: SpotifyPlaybackHooks): void {
    this.hooks = hooks;
  }

  async start(uri: string, autoplay: boolean): Promise<boolean> {
    if (!this.integration.connected()) return false;
    this.currentUri = uri;
    try {
      await this.ensureReady();
      if (!autoplay) return true;
      return this.playUri(uri);
    } catch (error) {
      this.hooks.onError(error instanceof Error ? error.message : 'Spotify playback unavailable');
      return false;
    }
  }

  async resume(): Promise<boolean> {
    try {
      await this.ensureReady();
      if (!this.player) return false;
      if (!this.state && this.currentUri) return this.playUri(this.currentUri);
      await this.player.resume();
      return true;
    } catch {
      return false;
    }
  }

  pause(): void {
    void this.player?.pause().catch(() => undefined);
  }

  seek(seconds: number): void {
    void this.player?.seek(Math.max(0, seconds) * 1000).catch(() => undefined);
  }

  setVolume(volume: number): void {
    void this.player?.setVolume(Math.max(0, Math.min(1, volume))).catch(() => undefined);
  }

  getCurrentTime(): number {
    return (this.state?.position ?? 0) / 1000;
  }

  getDuration(): number {
    return (this.state?.duration ?? 0) / 1000;
  }

  stop(): void {
    this.pause();
    this.state = null;
    this.currentUri = null;
  }

  private async playUri(uri: string): Promise<boolean> {
    if (!this.deviceId) return false;
    const token = await this.integration.getAccessToken();
    const response = await fetch(
      `https://api.spotify.com/v1/me/player/play?device_id=${encodeURIComponent(this.deviceId)}`,
      {
        method: 'PUT',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ uris: [uri] }),
      },
    );
    if (response.ok || response.status === 204) return true;
    if (response.status === 403) {
      throw new Error('La reproducción completa de Spotify requiere una cuenta Premium.');
    }
    throw new Error(`Spotify no pudo iniciar la reproducción (${response.status}).`);
  }

  private ensureReady(): Promise<void> {
    if (this.player && this.deviceId) return Promise.resolve();
    if (this.readyPromise) return this.readyPromise;
    this.readyPromise = new Promise<void>((resolve, reject) => {
      const timeout = window.setTimeout(() => reject(new Error('Spotify tardó demasiado en preparar el reproductor.')), 12_000);
      const createPlayer = () => {
        if (!window.Spotify?.Player) return;
        this.player = new window.Spotify.Player({
          name: 'VOXMETRIKS Player',
          volume: 0.8,
          getOAuthToken: (callback) => {
            void this.integration.getAccessToken().then(callback).catch(() => this.hooks.onError('Vuelve a conectar Spotify.'));
          },
        });
        this.player.addListener('ready', ({ device_id }: { device_id: string }) => {
          window.clearTimeout(timeout);
          this.deviceId = device_id;
          resolve();
        });
        this.player.addListener('not_ready', () => {
          this.deviceId = null;
          this.hooks.onError('Spotify perdió la conexión con este navegador.');
        });
        const errorEvents: SpotifySdkErrorEvent[] = [
          'initialization_error',
          'authentication_error',
          'account_error',
          'playback_error',
        ];
        errorEvents.forEach((event) => {
          this.player?.addListener(event, ({ message }: { message?: string }) => {
            this.hooks.onError(message || 'Spotify playback error');
          });
        });
        this.player.addListener('player_state_changed', (next: SpotifySdkState | null) => {
          if (!next) return;
          const previous = this.state;
          this.state = next;
          if (!next.paused) this.hooks.onPlay();
          else if (previous && previous.position > 0 && next.position === 0) this.hooks.onEnded();
          else this.hooks.onPause();
        });
        void this.player.connect().then((ok) => {
          if (!ok) reject(new Error('Spotify no aceptó este reproductor.'));
        }).catch(reject);
      };

      if (window.Spotify?.Player) {
        createPlayer();
        return;
      }
      window.onSpotifyWebPlaybackSDKReady = createPlayer;
      if (!document.getElementById('spotify-player-sdk')) {
        const script = document.createElement('script');
        script.id = 'spotify-player-sdk';
        script.src = 'https://sdk.scdn.co/spotify-player.js';
        script.async = true;
        script.onerror = () => reject(new Error('No se pudo descargar el reproductor de Spotify.'));
        document.head.appendChild(script);
      }
    }).finally(() => {
      if (!this.deviceId) this.readyPromise = null;
    });
    return this.readyPromise;
  }
}
