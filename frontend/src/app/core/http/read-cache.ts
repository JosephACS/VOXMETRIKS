import { Observable, shareReplay } from 'rxjs';

const DEFAULT_TTL_MS = 30_000;

/** Short-lived in-memory cache for idempotent GET responses (shareReplay + TTL). */
export class ReadCache<T> {
  private entry: { obs: Observable<T>; at: number } | null = null;

  constructor(private readonly ttlMs = DEFAULT_TTL_MS) {}

  get(factory: () => Observable<T>): Observable<T> {
    const now = Date.now();
    if (!this.entry || now - this.entry.at > this.ttlMs) {
      this.entry = { at: now, obs: factory().pipe(shareReplay(1)) };
    }
    return this.entry.obs;
  }

  invalidate(): void {
    this.entry = null;
  }
}
