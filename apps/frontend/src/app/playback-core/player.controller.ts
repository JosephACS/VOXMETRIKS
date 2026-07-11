import { Injectable, inject } from '@angular/core';
import { MusicPlayerService } from '../shared/services/music-player.service';
import { PlayableTrack, RepeatMode } from '../shared/models/player.models';
import { Track, TopTrack } from '../shared/models/api.models';
import { PlaybackStore } from './playback.store';

/** Public facade for playback intents + global store access. */
@Injectable({ providedIn: 'root' })
export class PlayerController {
  private readonly player = inject(MusicPlayerService);
  readonly playback = inject(PlaybackStore);

  playNow(track: PlayableTrack, contextQueue?: PlayableTrack[]): void {
    this.player.playNow(track, contextQueue);
  }

  playTrack(track: PlayableTrack, queue?: PlayableTrack[]): void {
    this.player.playTrack(track, queue);
  }

  toggle(): void { this.player.toggle(); }
  pause(): void { this.player.pause(); }
  resume(): void { this.player.resume(); }
  next(): void { this.player.next(); }
  previous(): void { this.player.previous(); }
  seek(seconds: number): void { this.player.seek(seconds); }
  seekPct(pct: number): void { this.player.seekPct(pct); }

  setVolume(v: number): void { this.player.setVolume(v); }
  toggleMute(): void { this.player.toggleMute(); }
  toggleShuffle(): void { this.player.toggleShuffle(); }
  cycleRepeat(): void { this.player.cycleRepeat(); }
  setRepeatMode(mode: RepeatMode): void { this.player.setRepeatMode(mode); }
  toggleAutoplay(): void { this.player.toggleAutoplay(); }

  addToQueue(track: PlayableTrack): boolean { return this.player.addToQueue(track); }
  playNextInQueue(track: PlayableTrack): void { this.player.playNextInQueue(track); }
  removeFromQueue(index: number): boolean { return this.player.removeFromQueue(index); }
  moveInQueue(from: number, to: number): boolean { return this.player.moveInQueue(from, to); }
  clearQueue(): void { this.player.clearQueue(); }
  clearPendingQueue(): void { this.player.clearPendingQueue(); }

  retryCurrent(): void { this.player.retryCurrent(); }
  openExpandedView(): void { this.player.openExpandedView(); }
  closeExpandedView(): void { this.player.closeExpandedView(); }
  toggleExpandedView(): void { this.player.toggleExpandedView(); }
  clearCover(): void { this.player.clearCover(); }
  stopPlayback(): void { this.player.stopPlayback(); }
  formatTime(sec: number): string { return this.player.formatTime(sec); }

  fromTrack(t: Track, artistName?: string): PlayableTrack {
    return this.player.fromTrack(t, artistName);
  }

  fromTopTrack(t: TopTrack): PlayableTrack {
    return this.player.fromTopTrack(t);
  }

  setQueue(tracks: PlayableTrack[], startIndex = 0): void {
    this.player.setQueue(tracks, startIndex);
  }
}
