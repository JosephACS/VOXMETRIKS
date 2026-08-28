import { Injectable, inject } from '@angular/core';
import {
  PlayerPlaybackEngine,
  PlaybackEngineHooks,
} from '../shared/services/player/player-playback.engine';
import { SpotifyPlaybackService } from '../core/integrations/spotify/spotify-playback.service';

/** Injectable wrapper around Spotify Web Playback SDK + HTML Audio previews. */
@Injectable({ providedIn: 'root' })
export class PlaybackEngine {
  private readonly spotify = inject(SpotifyPlaybackService);
  private inner: PlayerPlaybackEngine | null = null;

  init(hooks: PlaybackEngineHooks): void {
    if (this.inner) this.inner.destroy();
    this.inner = new PlayerPlaybackEngine(this.spotify, hooks);
  }

  get instance(): PlayerPlaybackEngine {
    if (!this.inner) throw new Error('PlaybackEngine not initialized');
    return this.inner;
  }

  get isReady(): boolean {
    return this.inner != null;
  }

  destroy(): void {
    this.inner?.destroy();
    this.inner = null;
  }
}
