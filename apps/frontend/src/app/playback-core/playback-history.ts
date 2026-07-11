import { PlayableTrack, RepeatMode } from '../shared/models/player.models';

/** Stack of previously played tracks (for Previous button). */
export class PlaybackHistoryStack {
  private stack: PlayableTrack[] = [];
  private readonly maxSize: number;

  constructor(maxSize = 50) {
    this.maxSize = maxSize;
  }

  push(track: PlayableTrack): void {
    if (!track?.id) return;
    const top = this.stack[this.stack.length - 1];
    if (top?.id === track.id) return;
    this.stack.push(track);
    if (this.stack.length > this.maxSize) this.stack.shift();
  }

  pop(): PlayableTrack | null {
    return this.stack.pop() ?? null;
  }

  peek(): PlayableTrack | null {
    return this.stack.length ? this.stack[this.stack.length - 1] : null;
  }

  clear(): void {
    this.stack = [];
  }

  get size(): number {
    return this.stack.length;
  }

  /** Restore from persisted ids + track lookup map. */
  restore(tracks: PlayableTrack[]): void {
    this.stack = tracks.filter((t) => t?.id);
  }

  toArray(): PlayableTrack[] {
    return [...this.stack];
  }
}

export function cycleRepeatMode(current: RepeatMode): RepeatMode {
  if (current === 'off') return 'all';
  if (current === 'all') return 'one';
  return 'off';
}

export function hasNextTrack(
  queueLength: number,
  currentIndex: number,
  shuffle: boolean,
  repeatMode: RepeatMode,
): boolean {
  if (queueLength === 0) return false;
  if (repeatMode === 'one' || repeatMode === 'all') return true;
  if (shuffle) return queueLength > 1;
  return currentIndex < queueLength - 1;
}

export function nextIndex(
  queueLength: number,
  currentIndex: number,
  shuffle: boolean,
  repeatMode: RepeatMode,
): number | null {
  if (queueLength === 0) return null;
  if (repeatMode === 'one') return currentIndex;

  if (shuffle) {
    if (queueLength === 1) return repeatMode === 'all' ? 0 : null;
    let idx = currentIndex;
    let guard = 0;
    while (idx === currentIndex && guard++ < 12) {
      idx = Math.floor(Math.random() * queueLength);
    }
    return idx;
  }

  if (currentIndex < queueLength - 1) return currentIndex + 1;
  if (repeatMode === 'all') return 0;
  return null;
}
