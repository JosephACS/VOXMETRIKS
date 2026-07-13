import { Injectable, inject } from '@angular/core';
import { TracksService } from '../packages/streaming/services/tracks.service';

/**
 * Fire-and-forget audio pre-resolution for hot tracks (home, queue, history).
 * Uses existing /audio-source cache — does not start playback.
 */
@Injectable({ providedIn: 'root' })
export class AudioPrefetchService {
  private readonly tracks = inject(TracksService);
  private readonly warmed = new Set<number>();
  private queue: number[] = [];
  private active = 0;
  private readonly concurrency = 2;

  /** Warm cache for up to `limit` track ids (deduped, non-blocking). */
  warm(trackIds: Array<number | null | undefined>, limit = 12): void {
    const ids = [...new Set(
      trackIds
        .filter((id): id is number => typeof id === 'number' && id > 0)
        .filter((id) => !this.warmed.has(id)),
    )].slice(0, limit);

    for (const id of ids) {
      this.warmed.add(id);
      this.queue.push(id);
    }
    this.pump();
  }

  private pump(): void {
    while (this.active < this.concurrency && this.queue.length) {
      const id = this.queue.shift()!;
      this.active++;
      this.tracks.getAudioSource(id).subscribe({
        next: () => this.done(),
        error: () => this.done(),
      });
    }
  }

  private done(): void {
    this.active = Math.max(0, this.active - 1);
    this.pump();
  }
}
