import { Injectable, inject } from '@angular/core';
import {
  Observable,
  of,
  shareReplay,
  map,
  catchError,
  switchMap,
  defer,
  finalize,
  timer,
} from 'rxjs';
import { retry } from 'rxjs/operators';
import { TracksService } from '../../packages/streaming/services/tracks.service';
import { ArtistsService } from '../../packages/streaming/services/artists.service';

/**
 * Resolves cover-art URLs with:
 * - positive URL memory (never flash placeholder over a known-good cover)
 * - soft TTL for not_found (retry later)
 * - limited concurrency + backoff (even if global rate limit is 0)
 */
@Injectable({ providedIn: 'root' })
export class TrackCoverService {
  private tracksApi = inject(TracksService);
  private artistsApi = inject(ArtistsService);

  /** Known-good URLs — never replaced by a later null/placeholder. */
  private positiveTrackUrls = new Map<number, string>();
  private positiveArtistUrls = new Map<number, string>();

  private trackCache = new Map<number, Observable<string | null>>();
  private artistCache = new Map<number, Observable<string | null>>();
  private trackNullExpiry = new Map<number, number>();
  private artistNullExpiry = new Map<number, number>();

  /** Configurable concurrency — keep low to avoid saturating iTunes. */
  private readonly maxConcurrent = 4;
  private readonly notFoundTtlMs = 60 * 60 * 1000;
  private active = 0;
  private readonly waiters: Array<() => void> = [];

  /** Album/track artwork for a catalog track id. */
  cover$(trackId: number): Observable<string | null> {
    return this.trackCover$(trackId);
  }

  trackCover$(trackId: number): Observable<string | null> {
    if (!trackId || trackId < 0) return of(null);

    const known = this.positiveTrackUrls.get(trackId);
    if (known) return of(known);

    this.evictExpiredNull('track', trackId);
    const hit = this.trackCache.get(trackId);
    if (hit) return hit;

    const req = defer(() =>
      this.acquire().pipe(
        switchMap(() =>
          this.tracksApi.getCover(trackId).pipe(
            retry({
              count: 2,
              delay: (_err, retryCount) => timer(300 * Math.pow(2, retryCount - 1)),
            }),
            finalize(() => this.release()),
          ),
        ),
      ),
    ).pipe(
      map((c) => (c.status === 'ok' && c.image_url ? c.image_url : null)),
      catchError(() => of(null)),
      map((url) => {
        if (url) {
          this.positiveTrackUrls.set(trackId, url);
          this.trackNullExpiry.delete(trackId);
          return url;
        }
        this.trackNullExpiry.set(trackId, Date.now() + this.notFoundTtlMs);
        return null;
      }),
      shareReplay(1),
    );
    this.trackCache.set(trackId, req);
    return req;
  }

  artistCover$(artistId: number): Observable<string | null> {
    if (!artistId || artistId < 0) return of(null);

    const known = this.positiveArtistUrls.get(artistId);
    if (known) return of(known);

    this.evictExpiredNull('artist', artistId);
    const hit = this.artistCache.get(artistId);
    if (hit) return hit;

    const req = defer(() =>
      this.acquire().pipe(
        switchMap(() =>
          this.artistsApi.getCover(artistId).pipe(
            retry({
              count: 2,
              delay: (_err, retryCount) => timer(300 * Math.pow(2, retryCount - 1)),
            }),
            finalize(() => this.release()),
          ),
        ),
      ),
    ).pipe(
      map((c) => (c.status === 'ok' && c.image_url ? c.image_url : null)),
      catchError(() => of(null)),
      map((url) => {
        if (url) {
          this.positiveArtistUrls.set(artistId, url);
          this.artistNullExpiry.delete(artistId);
          return url;
        }
        this.artistNullExpiry.set(artistId, Date.now() + this.notFoundTtlMs);
        return null;
      }),
      shareReplay(1),
    );
    this.artistCache.set(artistId, req);
    return req;
  }

  /** Track cover first; if missing, artist portrait. Never clears a known-good track cover. */
  bestCover$(trackId: number, artistId?: number | null): Observable<string | null> {
    return this.trackCover$(trackId).pipe(
      switchMap((url) => {
        if (url) return of(url);
        const known = this.positiveTrackUrls.get(trackId);
        if (known) return of(known);
        if (artistId) return this.artistCover$(artistId);
        return of(null);
      }),
    );
  }

  private evictExpiredNull(kind: 'track' | 'artist', id: number): void {
    const expiryMap = kind === 'track' ? this.trackNullExpiry : this.artistNullExpiry;
    const cache = kind === 'track' ? this.trackCache : this.artistCache;
    const until = expiryMap.get(id);
    if (until != null && Date.now() >= until) {
      expiryMap.delete(id);
      cache.delete(id);
    }
  }

  private acquire(): Observable<void> {
    return new Observable<void>((subscriber) => {
      const grant = () => {
        this.active += 1;
        subscriber.next();
        subscriber.complete();
      };
      if (this.active < this.maxConcurrent) {
        grant();
        return;
      }
      this.waiters.push(grant);
    });
  }

  private release(): void {
    this.active = Math.max(0, this.active - 1);
    const next = this.waiters.shift();
    if (next) next();
  }
}
