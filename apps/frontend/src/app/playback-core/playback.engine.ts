import { Injectable, inject } from '@angular/core';
import { YoutubeEngineService } from '../shared/services/youtube-engine.service';
import {
  PlayerPlaybackEngine,
  PlaybackEngineHooks,
} from '../shared/services/player/player-playback.engine';

/** Injectable wrapper around the low-level audio engine (HTML5 + YouTube). */
@Injectable({ providedIn: 'root' })
export class PlaybackEngine {
  private readonly yt = inject(YoutubeEngineService);
  private inner: PlayerPlaybackEngine | null = null;

  init(hooks: PlaybackEngineHooks): void {
    if (this.inner) this.inner.destroy();
    this.inner = new PlayerPlaybackEngine(this.yt, hooks);
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
