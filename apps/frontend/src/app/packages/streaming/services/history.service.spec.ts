import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { signal } from '@angular/core';
import { HistoryService } from './history.service';
import { AuthService } from '../../../core/services/auth.service';
import { environment } from '../../../../environments/environment';

describe('HistoryService music-core', () => {
  let svc: HistoryService;
  let http: HttpTestingController;
  let isAuthenticated: ReturnType<typeof signal<boolean>>;
  let userId: ReturnType<typeof signal<number | null>>;
  const base = `${environment.apiUrl}/listening-history`;

  beforeEach(() => {
    localStorage.clear();
    isAuthenticated = signal(false);
    userId = signal<number | null>(null);

    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        HistoryService,
        {
          provide: AuthService,
          useValue: {
            isAuthenticated: () => isAuthenticated(),
            userId: () => userId(),
          },
        },
      ],
    });

    svc = TestBed.inject(HistoryService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    http.verify();
    localStorage.clear();
  });

  async function authAs(uid = 1): Promise<void> {
    isAuthenticated.set(true);
    userId.set(uid);
    TestBed.flushEffects();
    await Promise.resolve();
    await Promise.resolve();
    const pending = http.match((r) => r.url === base && r.method === 'GET');
    for (const req of pending) {
      req.flush({ items: [], page: 1, limit: 30, total: 0, has_more: false });
    }
  }

  it('meets listen threshold at 30s or 50% when duration < 60s', () => {
    expect(svc.meetsListenThreshold(29_999)).toBe(false);
    expect(svc.meetsListenThreshold(30_000)).toBe(true);
    expect(svc.meetsListenThreshold(20_000, 50)).toBe(false);
    expect(svc.meetsListenThreshold(25_000, 50)).toBe(true);
    expect(svc.meetsListenThreshold(40_000, 120)).toBe(true);
  });

  it('migrates localStorage history once and is idempotent', async () => {
    const key = 'voxmetrik_history_42';
    const migrated = 'voxmetrik_history_migrated_42';
    localStorage.setItem(
      key,
      JSON.stringify([
        {
          id_track: 10,
          nombre_track: 'Old',
          viewed_at: '2024-01-01T00:00:00.000Z',
        },
      ]),
    );

    const p1 = svc.migrateLocalIfNeededForTest(42);
    const req = http.expectOne(`${base}/migrate`);
    expect(req.request.body.entries).toHaveLength(1);
    req.flush({ ok: true });
    await p1;

    expect(localStorage.getItem(migrated)).toBe('1');
    expect(localStorage.getItem(key)).toBeNull();

    await svc.migrateLocalIfNeededForTest(42);
    http.expectNone(`${base}/migrate`);
  });

  it('keeps local entries when migrate API fails', async () => {
    const key = 'voxmetrik_history_42';
    localStorage.setItem(
      key,
      JSON.stringify([{ id_track: 3, nombre_track: 'Keep', viewed_at: '2024-01-01T00:00:00.000Z' }]),
    );

    const p = svc.migrateLocalIfNeededForTest(42);
    const req = http.expectOne(`${base}/migrate`);
    req.flush({ detail: 'fail' }, { status: 500, statusText: 'Server Error' });
    await p;

    expect(localStorage.getItem(key)).toBeTruthy();
    expect(localStorage.getItem('voxmetrik_history_migrated_42')).toBeNull();
  });

  /** Simulate N one-second player ticks (matches real onTick cadence). */
  function tickListen(seconds: number, progressSec: number, durationSec: number): void {
    for (let i = 0; i < seconds; i++) {
      vi.advanceTimersByTime(1_000);
      svc.updateProgress(progressSec, durationSec);
    }
  }

  it('accumulates listened_ms via wall-clock deltas, not playhead assignment', async () => {
    await authAs();
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2024-06-01T12:00:00.000Z'));
    svc.add({ id_track: 9, nombre_track: 'A', nombre_artista: 'B' });

    svc.updateProgress(5, 180);
    expect(svc.getAccumulatedListenedMs()).toBe(0);

    tickListen(10, 40, 180); // playhead jumps; listen follows wall clock
    expect(svc.getAccumulatedListenedMs()).toBe(10_000);
    expect(svc.getAccumulatedListenedMs()).not.toBe(40_000);

    tickListen(5, 12, 180); // seek backward playhead
    expect(svc.getAccumulatedListenedMs()).toBe(15_000);

    vi.useRealTimers();
  });

  it('seek-to-30s playhead alone does not meet listen threshold', async () => {
    await authAs();
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2024-06-01T12:00:00.000Z'));
    svc.add({ id_track: 9, nombre_track: 'A', nombre_artista: 'B' });

    svc.updateProgress(0, 180);
    tickListen(1, 30, 180); // only 1s real listen after seek-to-30s playhead
    expect(svc.getAccumulatedListenedMs()).toBe(1_000);
    expect(svc.meetsListenThreshold(svc.getAccumulatedListenedMs(), 180)).toBe(false);
    http.expectNone(`${base}/start`);

    vi.useRealTimers();
  });

  it('qualifies short tracks at ≥50% real listen time', async () => {
    await authAs();
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2024-06-01T12:00:00.000Z'));
    svc.add({ id_track: 3, nombre_track: 'Short', nombre_artista: 'X' });

    svc.updateProgress(0, 50);
    tickListen(25, 25, 50);

    const start = http.expectOne(`${base}/start`);
    expect(start.request.body.track_id).toBe(3);
    expect(start.request.body.listened_ms).toBe(25_000);
    expect(start.request.body.progress_ms).toBe(25_000);
    start.flush({
      id: 1,
      id_track: 3,
      event_key: start.request.body.event_key,
      nombre_track: 'Short',
      viewed_at: '2024-06-01T12:00:00.000Z',
    });
    const progress = http.expectOne(`${base}/progress`);
    expect(progress.request.body.listened_ms).toBe(25_000);
    expect(progress.request.body.progress_ms).toBe(25_000);
    progress.flush({ ok: true });
    expect(svc.isQualified()).toBe(true);

    vi.useRealTimers();
  });

  it('reverts qualified state and retries when /start fails', async () => {
    await authAs();
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2024-06-01T12:00:00.000Z'));
    svc.add({ id_track: 7, nombre_track: 'Retry', nombre_artista: 'Y' });

    svc.updateProgress(0, 180);
    tickListen(30, 30, 180);

    const start1 = http.expectOne(`${base}/start`);
    start1.flush({ detail: 'fail' }, { status: 500, statusText: 'Server Error' });
    expect(svc.isQualified()).toBe(false);
    http.expectNone(`${base}/progress`);

    tickListen(1, 31, 180);
    const start2 = http.expectOne(`${base}/start`);
    start2.flush({
      id: 2,
      id_track: 7,
      event_key: start2.request.body.event_key,
      nombre_track: 'Retry',
      viewed_at: '2024-06-01T12:00:00.000Z',
    });
    http.expectOne(`${base}/progress`).flush({ ok: true });
    expect(svc.isQualified()).toBe(true);

    vi.useRealTimers();
  });

  it('completeCurrent sends accumulated listened_ms and does not mark success on failure', async () => {
    await authAs();
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2024-06-01T12:00:00.000Z'));
    svc.add({ id_track: 11, nombre_track: 'Done', nombre_artista: 'Z' });

    svc.updateProgress(0, 180);
    tickListen(30, 90, 180);
    const start = http.expectOne(`${base}/start`);
    const eventKey = start.request.body.event_key as string;
    start.flush({
      id: 5,
      id_track: 11,
      event_key: eventKey,
      nombre_track: 'Done',
      viewed_at: '2024-06-01T12:00:00.000Z',
    });
    http.expectOne(`${base}/progress`).flush({ ok: true });

    svc.completeCurrent(90);
    const complete = http.expectOne(`${base}/complete`);
    expect(complete.request.body).toEqual({
      event_key: eventKey,
      progress_ms: 90_000,
      listened_ms: 30_000,
    });
    complete.flush({ detail: 'fail' }, { status: 500, statusText: 'Server Error' });
    // Failure triggers reload — must not leave a fake completed flag without refetch.
    const reload = http.expectOne((r) => r.url === base && r.method === 'GET');
    reload.flush({ items: [], page: 1, limit: 30, total: 0, has_more: false });

    vi.useRealTimers();
  });

  it('clearAccountHistory POSTs /clear and restores via reload on failure', async () => {
    await authAs();
    let entries: unknown[] = [{ id_track: 1 }];
    svc.history$.subscribe((h) => {
      entries = h;
    });

    const sub = svc.clearAccountHistory().subscribe({
      error: () => undefined,
    });
    const clearReq = http.expectOne(`${base}/clear?confirm=true`);
    clearReq.flush({ detail: 'nope' }, { status: 500, statusText: 'Server Error' });
    const reload = http.expectOne((r) => r.url === base && r.method === 'GET');
    reload.flush({
      items: [{ id_track: 1, nombre_track: 'Restored', viewed_at: '2024-01-01T00:00:00.000Z' }],
      page: 1,
      limit: 30,
      total: 1,
      has_more: false,
    });
    expect(entries).toHaveLength(1);
    sub.unsubscribe();
  });

  it('clearLocalCache clears temp state without calling /clear', async () => {
    await authAs();
    svc.add({ id_track: 1, nombre_track: 'T', nombre_artista: 'A' });
    svc.clearLocalCache();
    expect(svc.getAccumulatedListenedMs()).toBe(0);
    expect(svc.isQualified()).toBe(false);
    http.expectNone(`${base}/clear?confirm=true`);
  });

  it('stale /start after another song starts never qualifies the new session', async () => {
    await authAs();
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2024-06-01T12:00:00.000Z'));

    const keyA = svc.add({ id_track: 1, nombre_track: 'A', nombre_artista: 'X' });
    svc.updateProgress(0, 180);
    tickListen(30, 30, 180);
    const startA = http.expectOne(`${base}/start`);
    expect(startA.request.body.event_key).toBe(keyA);

    const keyB = svc.add({ id_track: 2, nombre_track: 'B', nombre_artista: 'Y' });
    expect(keyB).not.toBe(keyA);
    expect(svc.isQualified()).toBe(false);

    startA.flush({
      id: 99,
      id_track: 1,
      event_key: keyA,
      nombre_track: 'A',
      viewed_at: '2024-06-01T12:00:00.000Z',
    });
    // Stale success must complete orphaned A for same user — never qualify B.
    const completeA = http.expectOne(`${base}/complete`);
    expect(completeA.request.body.event_key).toBe(keyA);
    completeA.flush({ ok: true });
    expect(svc.getCurrentEventKey()).toBe(keyB);
    expect(svc.isQualified()).toBe(false);
    http.expectNone(`${base}/progress`);

    vi.useRealTimers();
  });

  it('stale /start after clearLocalCache does not re-qualify or post progress', async () => {
    await authAs();
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2024-06-01T12:00:00.000Z'));

    const key = svc.add({ id_track: 4, nombre_track: 'C', nombre_artista: 'Z' });
    svc.updateProgress(0, 180);
    tickListen(30, 30, 180);
    const start = http.expectOne(`${base}/start`);

    svc.clearLocalCache();
    expect(svc.getCurrentEventKey()).toBeNull();

    start.flush({
      id: 3,
      id_track: 4,
      event_key: key,
      nombre_track: 'C',
      viewed_at: '2024-06-01T12:00:00.000Z',
    });
    // Same user still authed → orphaned complete only.
    const complete = http.expectOne(`${base}/complete`);
    expect(complete.request.body.event_key).toBe(key);
    complete.flush({ ok: true });
    expect(svc.isQualified()).toBe(false);
    http.expectNone(`${base}/progress`);

    vi.useRealTimers();
  });

  it('stale /start after ended/completeCurrent does not revive the session', async () => {
    await authAs();
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2024-06-01T12:00:00.000Z'));

    const key = svc.add({ id_track: 5, nombre_track: 'E', nombre_artista: 'Z' });
    svc.updateProgress(0, 180);
    tickListen(30, 30, 180);
    const start = http.expectOne(`${base}/start`);

    // End before start returns — session invalidated (not yet qualified).
    svc.completeCurrent(30);
    expect(svc.getCurrentEventKey()).toBeNull();
    http.expectNone(`${base}/complete`);

    start.flush({
      id: 8,
      id_track: 5,
      event_key: key,
      nombre_track: 'E',
      viewed_at: '2024-06-01T12:00:00.000Z',
    });
    const orphanComplete = http.expectOne(`${base}/complete`);
    expect(orphanComplete.request.body.event_key).toBe(key);
    orphanComplete.flush({ ok: true });
    expect(svc.getCurrentEventKey()).toBeNull();
    expect(svc.isQualified()).toBe(false);

    vi.useRealTimers();
  });

  it('repeat-style second add() creates a new event key', async () => {
    await authAs();
    const first = svc.add({ id_track: 9, nombre_track: 'Same', nombre_artista: 'A' });
    const gen1 = svc.getSessionGeneration();
    const second = svc.add({ id_track: 9, nombre_track: 'Same', nombre_artista: 'A' });
    expect(second).not.toBe(first);
    expect(svc.getSessionGeneration()).toBeGreaterThan(gen1);
    expect(svc.getCurrentEventKey()).toBe(second);
  });

  it('reloading same track closes prior session before add()', async () => {
    await authAs();
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2024-06-01T12:00:00.000Z'));

    const first = svc.add({ id_track: 9, nombre_track: 'Same', nombre_artista: 'A' });
    svc.updateProgress(0, 180);
    tickListen(30, 30, 180);
    const start = http.expectOne(`${base}/start`);
    start.flush({
      id: 1,
      id_track: 9,
      event_key: first,
      nombre_track: 'Same',
      viewed_at: '2024-06-01T12:00:00.000Z',
    });
    http.expectOne(`${base}/progress`).flush({ ok: true });

    // Mimic player: completeCurrent then add for same track.
    svc.completeCurrent(30);
    const complete = http.expectOne(`${base}/complete`);
    expect(complete.request.body.event_key).toBe(first);
    complete.flush({ ok: true });

    const second = svc.add({ id_track: 9, nombre_track: 'Same', nombre_artista: 'A' });
    expect(second).not.toBe(first);
    expect(svc.getCurrentEventKey()).toBe(second);
    expect(svc.isQualified()).toBe(false);

    vi.useRealTimers();
  });
});
