import { PlayableTrack } from '../../models/player.models';

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
    this.tracks = tracks;
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

  /**
   * ¿Hay una siguiente pista para auto-avance al terminar?
   * Sin envolver: con una sola pista (o ya en la última) devuelve false,
   * evitando que la misma canción se repita sola al acabar.
   */
  hasNext(shuffle: boolean): boolean {
    if (this.tracks.length <= 1) return false;
    if (shuffle) return true;
    return this.index < this.tracks.length - 1;
  }

  advance(shuffle: boolean): PlayableTrack | null {
    if (!this.tracks.length) return null;
    if (shuffle) {
      this.index = Math.floor(Math.random() * this.tracks.length);
    } else {
      this.index = (this.index + 1) % this.tracks.length;
    }
    return this.tracks[this.index];
  }

  retreat(): PlayableTrack | null {
    if (!this.tracks.length) return null;
    this.index = (this.index - 1 + this.tracks.length) % this.tracks.length;
    return this.tracks[this.index];
  }

  /** Pistas que vienen después de la actual (sin envolver). */
  upcoming(): PlayableTrack[] {
    if (!this.tracks.length || this.index >= this.tracks.length - 1) return [];
    return this.tracks.slice(this.index + 1);
  }

  upcomingCount(): number {
    return Math.max(0, this.tracks.length - this.index - 1);
  }

  /** Añade pistas al final omitiendo ids ya presentes. Devuelve las añadidas. */
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
}
