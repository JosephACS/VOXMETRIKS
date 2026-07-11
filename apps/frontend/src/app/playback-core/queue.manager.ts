import { Injectable, signal } from '@angular/core';
import { PlayableTrack, RepeatMode } from '../shared/models/player.models';
import { PlayerQueue } from '../shared/services/player/player-queue';
import { PlaybackHistoryStack } from './playback-history';

/** Global in-memory playback queue + play history — single source of truth. */
@Injectable({ providedIn: 'root' })
export class QueueManager {
  private readonly inner = new PlayerQueue();
  private readonly history = new PlaybackHistoryStack();

  readonly revision = signal(0);

  get items(): readonly PlayableTrack[] {
    return this.inner.items;
  }

  get currentIndex(): number {
    return this.inner.currentIndex;
  }

  get current(): PlayableTrack | undefined {
    return this.inner.current;
  }

  get playHistory(): PlaybackHistoryStack {
    return this.history;
  }

  private bump(): void {
    this.revision.update((n) => n + 1);
  }

  setAll(tracks: PlayableTrack[], startIndex: number): void {
    this.inner.setAll(tracks, startIndex);
    this.bump();
  }

  setSingle(track: PlayableTrack): void {
    this.inner.setSingle(track);
    this.bump();
  }

  clear(): void {
    this.inner.clear();
    this.bump();
  }

  findIndex(trackId: number): number {
    return this.inner.findIndex(trackId);
  }

  hasNext(shuffle: boolean, repeatMode: RepeatMode): boolean {
    return this.inner.hasNext(shuffle, repeatMode);
  }

  advance(shuffle: boolean, repeatMode: RepeatMode): PlayableTrack | null {
    const next = this.inner.advance(shuffle, repeatMode);
    if (next) this.bump();
    return next;
  }

  recordPlayed(track: PlayableTrack): void {
    this.history.push(track);
  }

  previousFromHistory(): PlayableTrack | null {
    return this.history.pop();
  }

  upcoming(): PlayableTrack[] {
    return this.inner.upcoming();
  }

  upcomingCount(): number {
    return this.inner.upcomingCount();
  }

  appendUnique(incoming: PlayableTrack[]): PlayableTrack[] {
    const added = this.inner.appendUnique(incoming);
    if (added.length) this.bump();
    return added;
  }

  insertNext(track: PlayableTrack): void {
    this.inner.insertNext(track);
    this.bump();
  }

  addToEndUnique(track: PlayableTrack): boolean {
    const ok = this.inner.addToEndUnique(track);
    if (ok) this.bump();
    return ok;
  }

  jumpTo(index: number): PlayableTrack | null {
    const t = this.inner.jumpTo(index);
    if (t) this.bump();
    return t;
  }

  trimToCurrent(): void {
    this.inner.trimToCurrent();
    this.bump();
  }

  removeAt(index: number): boolean {
    const ok = this.inner.removeAt(index);
    if (ok) this.bump();
    return ok;
  }

  move(from: number, to: number): boolean {
    const ok = this.inner.move(from, to);
    if (ok) this.bump();
    return ok;
  }

  restoreQueue(tracks: PlayableTrack[], index: number, history: PlayableTrack[]): void {
    this.inner.replaceItems(tracks, index);
    this.history.restore(history);
    this.bump();
  }

  clearHistory(): void {
    this.history.clear();
  }
}
