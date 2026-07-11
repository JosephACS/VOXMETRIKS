import { Injectable, inject, computed } from '@angular/core';
import { MusicPlayerService } from '../shared/services/music-player.service';
import { QueueManager } from './queue.manager';

/**
 * Single read-only source of truth for playback UI state (signals).
 * Mutations go through PlayerController → MusicPlayerService.
 */
@Injectable({ providedIn: 'root' })
export class PlaybackStore {
  private readonly player = inject(MusicPlayerService);
  private readonly queueMgr = inject(QueueManager);

  readonly status = this.player.status;
  readonly currentTrack = this.player.currentTrack;
  readonly isPlaying = this.player.isPlaying;
  readonly currentTime = this.player.currentTime;
  readonly duration = this.player.duration;
  readonly volume = this.player.volume;
  readonly muted = this.player.muted;
  readonly shuffle = this.player.shuffle;
  readonly repeatMode = this.player.repeatMode;
  readonly repeat = this.player.repeat;
  readonly autoplay = this.player.autoplay;
  readonly autoplayLoading = this.player.autoplayLoading;
  readonly progressPct = this.player.progressPct;
  readonly audioMode = this.player.audioMode;
  readonly playbackError = this.player.playbackError;
  readonly currentCover = this.player.currentCover;
  readonly expandedOpen = this.player.expandedOpen;

  readonly queue = this.player.queue;
  readonly queueIndex = this.player.queueIndex;
  readonly queueRevision = this.queueMgr.revision;

  readonly pendingQueue = this.player.upcomingQueue;

  readonly playHistory = computed(() => this.queueMgr.playHistory.toArray());

  readonly hasQueue = computed(() => this.queue().length > 0);
  readonly pendingCount = computed(() => this.pendingQueue().length);
  readonly hasCurrentTrack = computed(() => this.currentTrack() != null);

  isCurrentTrack(trackId: number): boolean {
    return this.currentTrack()?.id === trackId;
  }

  formatTime(seconds: number): string {
    return this.player.formatTime(seconds);
  }
}
