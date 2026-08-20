import { Injectable, inject, effect } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { BehaviorSubject, firstValueFrom, Observable, of, throwError } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';
import { environment } from '../../../../environments/environment';
import { HistoryEntry } from '../../../shared/models/api.models';
import { AuthService } from '../../../core/services/auth.service';

const STORAGE_PREFIX = 'voxmetrik_history';
const MIGRATED_PREFIX = 'voxmetrik_history_migrated';
/** Cap a single wall-clock tick so tab sleep / seeks cannot inflate listen time. */
const MAX_LISTEN_DELTA_MS = 2_000;
/**
 * Persist a row in personal history after this much real listen time.
 * (Counted / completed listens still use the 30s / 50% rule below.)
 */
const HISTORY_RECORD_MS = 3_000;

export interface ListeningHistoryItem extends HistoryEntry {
  id?: number;
  event_key?: string;
  progress_ms?: number;
  listened_ms?: number;
  completed?: boolean;
  played_at?: string;
  source?: string | null;
}

interface HistoryPage {
  items: ListeningHistoryItem[];
  page: number;
  limit: number;
  total: number;
  has_more: boolean;
}

interface SessionIdentity {
  eventKey: string;
  generation: number;
  userId: number;
}

/**
 * Account-scoped listening history. Backend DuckDB is the source of truth.
 * localStorage is only used for one-time migration and short-lived optimistic cache.
 *
 * Async callbacks capture {eventKey, generation, userId}; only matching
 * identities may mutate the live session.
 */
@Injectable({ providedIn: 'root' })
export class HistoryService {
  private auth = inject(AuthService);
  private http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/listening-history`;

  private entriesSubject = new BehaviorSubject<ListeningHistoryItem[]>([]);
  history$ = this.entriesSubject.asObservable();

  private loadingSubject = new BehaviorSubject<boolean>(false);
  loading$ = this.loadingSubject.asObservable();

  private errorSubject = new BehaviorSubject<boolean>(false);
  error$ = this.errorSubject.asObservable();

  private currentEventKey: string | null = null;
  private sessionGeneration = 0;
  private sessionUserId: number | null = null;
  private lastProgressAt = 0;
  private page = 1;
  private hasMore = false;
  private total = 0;
  private pendingEntry: ListeningHistoryItem | null = null;
  private qualified = false;
  /** Accumulated played time (wall-clock while playing). Never equal to playhead by assignment. */
  private accumulatedListenedMs = 0;
  /** Last wall-clock sample used for listened_ms deltas. */
  private lastListenWallClock = 0;
  private startInFlight = false;

  constructor() {
    effect(() => {
      const authed = this.auth.isAuthenticated();
      const uid = this.auth.userId();
      if (!authed || uid == null) {
        this.clearLocalCache();
        return;
      }
      void this.bootstrapForUser(uid);
    });
  }

  private localKey(userId: number): string {
    return `${STORAGE_PREFIX}_${userId}`;
  }

  private migratedKey(userId: number): string {
    return `${MIGRATED_PREFIX}_${userId}`;
  }

  private async bootstrapForUser(userId: number): Promise<void> {
    await this.migrateLocalIfNeeded(userId);
    this.reload();
  }

  reload(): void {
    this.page = 1;
    this.fetchPage(1, false);
  }

  loadMore(): void {
    if (!this.hasMore || this.loadingSubject.value) return;
    this.fetchPage(this.page + 1, true);
  }

  private fetchPage(page: number, append: boolean): void {
    if (!this.auth.isAuthenticated()) {
      this.entriesSubject.next([]);
      return;
    }
    this.loadingSubject.next(true);
    this.errorSubject.next(false);
    this.http
      .get<HistoryPage>(this.base, { params: { page: String(page), limit: '30' } })
      .subscribe({
        next: (res) => {
          const items = (res.items || []).map((i) => this.normalize(i));
          this.page = res.page;
          this.hasMore = !!res.has_more;
          this.total = res.total ?? items.length;
          let next = append ? [...this.entriesSubject.value, ...items] : items;
          // Keep the in-flight play visible across reload while listening.
          const pending = this.pendingEntry;
          if (
            !append &&
            pending &&
            this.currentEventKey &&
            pending.event_key === this.currentEventKey &&
            !next.some((e) => e.event_key === pending.event_key)
          ) {
            next = [this.normalize(pending), ...next];
          }
          this.entriesSubject.next(next);
          this.loadingSubject.next(false);
        },
        error: () => {
          this.errorSubject.next(true);
          this.loadingSubject.next(false);
        },
      });
  }

  private normalize(item: ListeningHistoryItem): ListeningHistoryItem {
    return {
      ...item,
      id_track: item.id_track,
      nombre_track: item.nombre_track || 'Track',
      viewed_at: item.viewed_at || item.played_at || new Date().toISOString(),
    };
  }

  getRecent(limit = 8): ListeningHistoryItem[] {
    return this.entriesSubject.value.slice(0, limit);
  }

  getTotal(): number {
    return this.total;
  }

  canLoadMore(): boolean {
    return this.hasMore;
  }

  /** Current open session event key (tests / diagnostics). */
  getCurrentEventKey(): string | null {
    return this.currentEventKey;
  }

  /** Current session generation (tests / diagnostics). */
  getSessionGeneration(): number {
    return this.sessionGeneration;
  }

  private captureIdentity(): SessionIdentity | null {
    if (!this.currentEventKey || this.sessionUserId == null) return null;
    return {
      eventKey: this.currentEventKey,
      generation: this.sessionGeneration,
      userId: this.sessionUserId,
    };
  }

  private isLiveSession(id: SessionIdentity): boolean {
    return (
      this.currentEventKey === id.eventKey &&
      this.sessionGeneration === id.generation &&
      this.sessionUserId === id.userId &&
      this.auth.isAuthenticated() &&
      this.auth.userId() === id.userId
    );
  }

  private sameUserStillAuthed(userId: number): boolean {
    return this.auth.isAuthenticated() && this.auth.userId() === userId;
  }

  /**
   * Begin a playback session locally. Invalidates any prior in-flight
   * generation so stale /start callbacks cannot touch the new session.
   */
  add(entry: Omit<HistoryEntry, 'viewed_at'>): string {
    const uid = this.auth.userId();
    const eventKey =
      typeof crypto !== 'undefined' && 'randomUUID' in crypto
        ? `play:${crypto.randomUUID()}`
        : `play:${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;

    // Invalidate prior generation before binding the new session.
    this.sessionGeneration += 1;
    this.currentEventKey = eventKey;
    this.sessionUserId = uid != null ? uid : null;
    this.pendingEntry = {
      id_track: entry.id_track,
      nombre_track: entry.nombre_track,
      nombre_artista: entry.nombre_artista,
      viewed_at: new Date().toISOString(),
      event_key: eventKey,
      completed: false,
      progress_ms: 0,
      listened_ms: 0,
    };
    this.qualified = false;
    this.accumulatedListenedMs = 0;
    this.lastListenWallClock = 0;
    this.lastProgressAt = 0;
    this.startInFlight = false;
    return eventKey;
  }

  /** Stop listen accumulation (pause / seek gap); does not clear progress. */
  pauseListenClock(): void {
    this.lastListenWallClock = 0;
  }

  /** Counted-listen rule: ≥30s, or ≥50% when track duration < 60s. */
  private meetsThreshold(listenedMs: number, durationSec?: number): boolean {
    if (listenedMs >= 30_000) return true;
    const durMs = durationSec != null && durationSec > 0 ? durationSec * 1000 : 0;
    if (durMs > 0 && durMs < 60_000 && listenedMs >= durMs * 0.5) return true;
    return false;
  }

  /** When a play becomes visible / persisted in personal history. */
  private meetsHistoryRecord(listenedMs: number): boolean {
    return listenedMs >= HISTORY_RECORD_MS;
  }

  /** Exposed for unit tests of the listen threshold rule. */
  meetsListenThreshold(listenedMs: number, durationSec?: number): boolean {
    return this.meetsThreshold(listenedMs, durationSec);
  }

  /** Exposed for unit tests of the history-record threshold. */
  meetsHistoryRecordThreshold(listenedMs: number): boolean {
    return this.meetsHistoryRecord(listenedMs);
  }

  /** Current accumulated listen ms for the open session (tests / diagnostics). */
  getAccumulatedListenedMs(): number {
    return this.accumulatedListenedMs;
  }

  /** Whether the open session has passed the listen threshold and /start succeeded. */
  isQualified(): boolean {
    return this.qualified;
  }

  /**
   * Update playhead (`progress_ms`) and accumulate real listen time via wall-clock
   * deltas while this method is invoked (player only calls while playing).
   */
  updateProgress(progressSec: number, durationSec?: number): void {
    const identity = this.captureIdentity();
    if (!identity || !this.auth.isAuthenticated()) return;

    const now = Date.now();
    if (this.lastListenWallClock > 0) {
      const delta = Math.min(Math.max(0, now - this.lastListenWallClock), MAX_LISTEN_DELTA_MS);
      this.accumulatedListenedMs += delta;
    }
    this.lastListenWallClock = now;

    const progress_ms = Math.max(0, Math.floor(progressSec * 1000));
    const listened_ms = Math.max(0, Math.floor(this.accumulatedListenedMs));
    if (this.pendingEntry && this.isLiveSession(identity)) {
      this.pendingEntry = { ...this.pendingEntry, progress_ms, listened_ms };
    }

    if (now - this.lastProgressAt < 5000 && this.qualified) return;
    this.lastProgressAt = now;

    if (
      !this.qualified &&
      !this.startInFlight &&
      this.meetsHistoryRecord(listened_ms) &&
      this.isLiveSession(identity)
    ) {
      this.startInFlight = true;
      const entry = this.pendingEntry;
      const trackId = entry?.id_track;
      if (entry) {
        const rest = this.entriesSubject.value.filter(
          (e) => e.event_key !== entry.event_key && e.id_track !== entry.id_track,
        );
        this.entriesSubject.next([{ ...entry, progress_ms, listened_ms }, ...rest].slice(0, 50));
      }
      this.http
        .post<ListeningHistoryItem>(`${this.base}/start`, {
          track_id: trackId,
          event_key: identity.eventKey,
          source: 'player',
          progress_ms,
          listened_ms,
        })
        .pipe(catchError(() => of(null)))
        .subscribe((res) => this.onStartResponse(identity, entry, progress_ms, listened_ms, res));
      return;
    }

    if (!this.qualified || !this.isLiveSession(identity)) return;

    this.http
      .post(`${this.base}/progress`, {
        event_key: identity.eventKey,
        progress_ms,
        listened_ms,
      })
      .pipe(catchError(() => of(null)))
      .subscribe();
  }

  private onStartResponse(
    identity: SessionIdentity,
    entry: ListeningHistoryItem | null,
    progress_ms: number,
    listened_ms: number,
    res: ListeningHistoryItem | null,
  ): void {
    if (this.isLiveSession(identity)) {
      this.startInFlight = false;
      if (!res) {
        this.qualified = false;
        if (entry) {
          this.entriesSubject.next(
            this.entriesSubject.value.filter((e) => e.event_key !== identity.eventKey),
          );
        }
        this.lastProgressAt = 0;
        return;
      }
      this.qualified = true;
      const mapped = this.normalize(res);
      const next = this.entriesSubject.value.map((e) =>
        e.event_key === identity.eventKey
          ? { ...e, ...mapped, progress_ms, listened_ms }
          : e,
      );
      this.entriesSubject.next(next);
      this.http
        .post(`${this.base}/progress`, {
          event_key: identity.eventKey,
          progress_ms,
          listened_ms,
        })
        .pipe(catchError(() => of(null)))
        .subscribe();
      return;
    }

    // Stale callback: never mutate the live session.
    // If the captured user is still authenticated, finalize the orphaned event
    // when start succeeded (preserve listen) or drop optimistic UI otherwise.
    if (!res) {
      if (this.sameUserStillAuthed(identity.userId) && entry) {
        this.entriesSubject.next(
          this.entriesSubject.value.filter((e) => e.event_key !== identity.eventKey),
        );
      }
      return;
    }

    if (this.sameUserStillAuthed(identity.userId)) {
      this.http
        .post(`${this.base}/complete`, {
          event_key: identity.eventKey,
          progress_ms,
          listened_ms,
        })
        .pipe(catchError(() => of(null)))
        .subscribe();
    }
  }

  /**
   * Close the current playback session. Captures identity before invalidating
   * so a late complete response never applies to a newer session.
   */
  completeCurrent(progressSec?: number): void {
    const identity = this.captureIdentity();
    const wasQualified = this.qualified;
    const listened_ms = Math.max(0, Math.floor(this.accumulatedListenedMs));
    const progress_ms =
      progressSec != null
        ? Math.max(0, Math.floor(progressSec * 1000))
        : this.pendingEntry?.progress_ms;

    const completeUserId = identity?.userId ?? null;
    this.resetSessionFields();

    if (!identity || !wasQualified || completeUserId == null) {
      return;
    }
    if (!this.sameUserStillAuthed(completeUserId)) {
      return;
    }

    this.http
      .post(`${this.base}/complete`, {
        event_key: identity.eventKey,
        progress_ms,
        listened_ms,
      })
      .pipe(catchError(() => of(null)))
      .subscribe((res) => {
        // Only touch list rows for the captured event; never revive session fields.
        if (!this.sameUserStillAuthed(completeUserId)) {
          return;
        }
        if (!res) {
          this.reload();
          return;
        }
        const next = this.entriesSubject.value.map((e) =>
          e.event_key === identity.eventKey
            ? { ...e, completed: true, progress_ms, listened_ms }
            : e,
        );
        this.entriesSubject.next(next);
      });
  }

  remove(id_track: number): void {
    const match = this.entriesSubject.value.find((e) => e.id_track === id_track);
    this.entriesSubject.next(this.entriesSubject.value.filter((e) => e.id_track !== id_track));
    if (match?.id != null && this.auth.isAuthenticated()) {
      this.http
        .delete(`${this.base}/${match.id}`)
        .pipe(catchError(() => of(null)))
        .subscribe();
    }
  }

  removeEntry(entryId: number): Observable<unknown> {
    this.entriesSubject.next(this.entriesSubject.value.filter((e) => e.id !== entryId));
    return this.http.delete(`${this.base}/${entryId}`).pipe(
      catchError(() => {
        this.reload();
        return of(null);
      }),
    );
  }

  pruneAbove(maxId: number): void {
    if (!maxId || maxId <= 0) return;
    const next = this.entriesSubject.value.filter(
      (e) => e.id_track > 0 && e.id_track <= maxId,
    );
    if (next.length !== this.entriesSubject.value.length) {
      this.entriesSubject.next(next);
    }
  }

  /**
   * Destructive account wipe (POST /listening-history/clear).
   * Only the History page may call this after user confirmation.
   */
  clearAccountHistory(): Observable<{ cleared: boolean; deleted?: number }> {
    if (!this.auth.isAuthenticated()) {
      this.entriesSubject.next([]);
      this.total = 0;
      this.hasMore = false;
      this.page = 1;
      return of({ cleared: true, deleted: 0 });
    }
    return this.http
      .post<{ cleared: boolean; deleted?: number }>(`${this.base}/clear?confirm=true`, {})
      .pipe(
        tap(() => {
          this.entriesSubject.next([]);
          this.total = 0;
          this.hasMore = false;
          this.page = 1;
          this.resetSessionFields();
        }),
        catchError((err) => {
          this.reload();
          return throwError(() => err);
        }),
      );
  }

  /**
   * Clear ALL temporary client state. No destructive HTTP.
   * Invalidates session generation so in-flight starts cannot apply.
   */
  clearLocalCache(): void {
    this.entriesSubject.next([]);
    this.loadingSubject.next(false);
    this.errorSubject.next(false);
    this.page = 1;
    this.hasMore = false;
    this.total = 0;
    this.resetSessionFields();
  }

  private resetSessionFields(): void {
    this.sessionGeneration += 1;
    this.currentEventKey = null;
    this.sessionUserId = null;
    this.pendingEntry = null;
    this.qualified = false;
    this.accumulatedListenedMs = 0;
    this.lastListenWallClock = 0;
    this.lastProgressAt = 0;
    this.startInFlight = false;
  }

  /** @internal test hook — runs local→API migration. */
  async migrateLocalIfNeededForTest(userId: number): Promise<void> {
    return this.migrateLocalIfNeeded(userId);
  }

  private async migrateLocalIfNeeded(userId: number): Promise<void> {
    try {
      if (localStorage.getItem(this.migratedKey(userId)) === '1') return;
      const key = this.localKey(userId);
      const raw = localStorage.getItem(key);
      if (!raw) {
        localStorage.setItem(this.migratedKey(userId), '1');
        return;
      }
      let entries: HistoryEntry[] = [];
      try {
        entries = JSON.parse(raw);
      } catch {
        localStorage.setItem(this.migratedKey(userId), '1');
        return;
      }
      if (!Array.isArray(entries) || entries.length === 0) {
        localStorage.setItem(this.migratedKey(userId), '1');
        localStorage.removeItem(key);
        return;
      }
      const valid = entries
        .filter((e) => e && typeof e.id_track === 'number' && e.id_track > 0)
        .map((e) => ({
          id_track: e.id_track,
          viewed_at: e.viewed_at,
          nombre_track: e.nombre_track,
          nombre_artista: e.nombre_artista,
        }));
      const res = await firstValueFrom(
        this.http.post<{ ok?: boolean }>(`${this.base}/migrate`, { entries: valid }),
      );
      if (res?.ok !== false) {
        localStorage.setItem(this.migratedKey(userId), '1');
        localStorage.removeItem(key);
      }
    } catch {
      // Keep local key for a later successful attempt.
    }
  }
}
