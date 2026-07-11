import { Injectable, inject } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { SearchHistoryEntry } from '../../../shared/models/api.models';
import { AuthService } from '../../../core/services/auth.service';

const STORAGE_PREFIX = 'voxmetrik_search_history';
const MAX_ENTRIES = 25;

@Injectable({ providedIn: 'root' })
export class SearchHistoryService {
  private auth = inject(AuthService);
  private entriesSubject = new BehaviorSubject<SearchHistoryEntry[]>([]);
  history$ = this.entriesSubject.asObservable();

  constructor() {
    this.reload();
  }

  private storageKey(): string {
    const id = this.auth.userId() ?? 'guest';
    return `${STORAGE_PREFIX}_${id}`;
  }

  reload(): void {
    this.entriesSubject.next(this.read());
  }

  private read(): SearchHistoryEntry[] {
    try {
      const raw = localStorage.getItem(this.storageKey());
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  }

  private persist(entries: SearchHistoryEntry[]): void {
    localStorage.setItem(this.storageKey(), JSON.stringify(entries));
    this.entriesSubject.next(entries);
  }

  add(query: string, trackCount = 0, artistCount = 0): void {
    const q = query.trim();
    if (!q) return;
    const now = new Date().toISOString();
    const filtered = this.read().filter(
      (e) => e.query.toLowerCase() !== q.toLowerCase(),
    );
    const next: SearchHistoryEntry[] = [
      { query: q, searched_at: now, track_count: trackCount, artist_count: artistCount },
      ...filtered,
    ].slice(0, MAX_ENTRIES);
    this.persist(next);
  }

  getRecent(limit = 25): SearchHistoryEntry[] {
    return this.read().slice(0, limit);
  }

  clear(): void {
    this.persist([]);
  }
}
