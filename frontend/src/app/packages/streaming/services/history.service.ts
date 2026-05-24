import { Injectable, inject } from '@angular/core';
import { BehaviorSubject } from 'rxjs';
import { HistoryEntry } from '../../../shared/models/api.models';
import { AuthService } from '../../../core/services/auth.service';

const STORAGE_PREFIX = 'voxmetrik_history';
const MAX_ENTRIES = 20;

@Injectable({ providedIn: 'root' })
export class HistoryService {
  private auth = inject(AuthService);
  private entriesSubject = new BehaviorSubject<HistoryEntry[]>([]);
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

  private read(): HistoryEntry[] {
    try {
      const raw = localStorage.getItem(this.storageKey());
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  }

  private persist(entries: HistoryEntry[]): void {
    localStorage.setItem(this.storageKey(), JSON.stringify(entries));
    this.entriesSubject.next(entries);
  }

  add(entry: Omit<HistoryEntry, 'viewed_at'>): void {
    const now = new Date().toISOString();
    const filtered = this.read().filter((e) => e.id_track !== entry.id_track);
    const next: HistoryEntry[] = [{ ...entry, viewed_at: now }, ...filtered].slice(0, MAX_ENTRIES);
    this.persist(next);
  }

  getRecent(limit = 8): HistoryEntry[] {
    return this.read().slice(0, limit);
  }

  clear(): void {
    this.persist([]);
  }
}
