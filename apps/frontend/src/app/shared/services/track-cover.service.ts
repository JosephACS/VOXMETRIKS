import { Injectable, inject } from '@angular/core';
import { Observable, of, shareReplay, map, catchError, switchMap } from 'rxjs';
import { TracksService } from '../../packages/streaming/services/tracks.service';
import { ArtistsService } from '../../packages/streaming/services/artists.service';

/**
 * Resolves cover-art URLs (track album art, then artist portrait) with in-memory cache.
 */
@Injectable({ providedIn: 'root' })
export class TrackCoverService {
  private tracksApi = inject(TracksService);
  private artistsApi = inject(ArtistsService);
  private trackCache = new Map<number, Observable<string | null>>();
  private artistCache = new Map<number, Observable<string | null>>();

  /** Album/track artwork for a catalog track id. */
  cover$(trackId: number): Observable<string | null> {
    return this.trackCover$(trackId);
  }

  trackCover$(trackId: number): Observable<string | null> {
    if (!trackId || trackId < 0) return of(null);
    const hit = this.trackCache.get(trackId);
    if (hit) return hit;

    const req = this.tracksApi.getCover(trackId).pipe(
      map((c) => (c.status === 'ok' && c.image_url ? c.image_url : null)),
      catchError(() => of(null)),
      shareReplay(1),
    );
    this.trackCache.set(trackId, req);
    return req;
  }

  artistCover$(artistId: number): Observable<string | null> {
    if (!artistId || artistId < 0) return of(null);
    const hit = this.artistCache.get(artistId);
    if (hit) return hit;

    const req = this.artistsApi.getCover(artistId).pipe(
      map((c) => (c.status === 'ok' && c.image_url ? c.image_url : null)),
      catchError(() => of(null)),
      shareReplay(1),
    );
    this.artistCache.set(artistId, req);
    return req;
  }

  /** Track cover first; if missing, artist portrait. */
  bestCover$(trackId: number, artistId?: number | null): Observable<string | null> {
    return this.trackCover$(trackId).pipe(
      switchMap((url) => {
        if (url) return of(url);
        if (artistId) return this.artistCover$(artistId);
        return of(null);
      }),
    );
  }
}
