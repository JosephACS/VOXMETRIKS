import { PlayableTrack, RepeatMode } from '../../models/player.models';
import { hasNextTrack, nextIndex } from '../../../playback-core/playback-history';

/** In-memory queue index management (no Angular signals). */
export class PlayerQueue {
  private tracks: PlayableTrack[] = [];
  private index = 0;

  get items(): readonly PlayableTrack[] {
    return this.tracks;
  }

  get currentIndex(): number {
    return this.index;
  }

  get current(): PlayableTrack | undefined {
    return this.tracks[this.index];
  }

  setAll(tracks: PlayableTrack[], startIndex: number): void {
    this.tracks = [...tracks];
    this.index = tracks.length ? Math.max(0, Math.min(startIndex, tracks.length - 1)) : 0;
  }

  setSingle(track: PlayableTrack): void {
    this.tracks = [track];
    this.index = 0;
  }

  clear(): void {
    this.tracks = [];
    this.index = 0;
  }

  findIndex(trackId: number): number {
    return this.tracks.findIndex((q) => q.id === trackId);
  }

  hasNext(shuffle: boolean, repeatMode: RepeatMode = 'off'): boolean {
    return hasNextTrack(this.tracks.length, this.index, shuffle, repeatMode);
  }

  advance(shuffle: boolean, repeatMode: RepeatMode = 'off'): PlayableTrack | null {
    if (!this.tracks.length) return null;
    const next = nextIndex(this.tracks.length, this.index, shuffle, repeatMode);
    if (next == null) return null;
    this.index = next;
    return this.tracks[this.index];
  }

  /** @deprecated use playback history stack — kept for internal fallback */
  retreat(): PlayableTrack | null {
    if (!this.tracks.length) return null;
    this.index = (this.index - 1 + this.tracks.length) % this.tracks.length;
    return this.tracks[this.index];
  }

  upcoming(): PlayableTrack[] {
    if (!this.tracks.length || this.index >= this.tracks.length - 1) return [];
    return this.tracks.slice(this.index + 1);
  }

  upcomingCount(): number {
    return Math.max(0, this.tracks.length - this.index - 1);
  }

  appendUnique(incoming: PlayableTrack[]): PlayableTrack[] {
    const ids = new Set(this.tracks.map((t) => t.id));
    const added: PlayableTrack[] = [];
    for (const t of incoming) {
      if (!t?.id || ids.has(t.id)) continue;
      ids.add(t.id);
      this.tracks.push(t);
      added.push(t);
    }
    return added;
  }

  insertNext(track: PlayableTrack): void {
    if (!track?.id) return;
    if (!this.tracks.length) {
      this.setSingle(track);
      return;
    }
    const existing = this.findIndex(track.id);
    if (existing === this.index) return;
    if (existing >= 0) {
      this.tracks.splice(existing, 1);
      if (existing < this.index) this.index--;
    }
    this.tracks.splice(this.index + 1, 0, track);
  }

  addToEndUnique(track: PlayableTrack): boolean {
    if (!track?.id || this.findIndex(track.id) >= 0) return false;
    this.tracks.push(track);
    return true;
  }

  jumpTo(index: number): PlayableTrack | null {
    if (!this.tracks.length) return null;
    this.index = Math.max(0, Math.min(index, this.tracks.length - 1));
    return this.tracks[this.index];
  }

  trimToCurrent(): void {
    const current = this.current;
    if (!current) {
      this.clear();
      return;
    }
    this.tracks = [current];
    this.index = 0;
  }

  removeAt(index: number): boolean {
    if (index < 0 || index >= this.tracks.length) return false;
    this.tracks.splice(index, 1);
    if (!this.tracks.length) {
      this.index = 0;
      return true;
    }
    if (index < this.index) this.index--;
    else if (index === this.index) this.index = Math.min(this.index, this.tracks.length - 1);
    return true;
  }

  move(from: number, to: number): boolean {
    if (from < 0 || from >= this.tracks.length || to < 0 || to >= this.tracks.length) return false;
    if (from === to) return true;
    const [item] = this.tracks.splice(from, 1);
    this.tracks.splice(to, 0, item);
    if (from === this.index) this.index = to;
    else if (from < this.index && to >= this.index) this.index--;
    else if (from > this.index && to <= this.index) this.index++;
    return true;
  }

  replaceItems(tracks: PlayableTrack[], index: number): void {
    this.tracks = [...tracks];
    this.index = tracks.length ? Math.max(0, Math.min(index, tracks.length - 1)) : 0;
  }
}
