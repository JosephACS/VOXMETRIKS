import { Injectable, inject } from '@angular/core';
import { Observable, of, shareReplay, map, catchError } from 'rxjs';
import { TracksService } from '../../packages/streaming/services/tracks.service';

/**
 * Lazily resolves real cover-art image URLs per track id and caches them in
 * memory (sharing in-flight requests) so the same track shown in multiple
 * sections only triggers one backend lookup. Returns `null` when there is no
 * real cover, so consumers fall back to the gradient placeholder.
 */
@Injectable({ providedIn: 'root' })
export class TrackCoverService {
  private tracksApi = inject(TracksService);
  private cache = new Map<number, Observable<string | null>>();

  cover$(trackId: number): Observable<string | null> {
    if (!trackId || trackId < 0) return of(null);
    const hit = this.cache.get(trackId);
    if (hit) return hit;

    const req = this.tracksApi.getCover(trackId).pipe(
      map((c) => (c.status === 'ok' && c.image_url ? c.image_url : null)),
      catchError(() => of(null)),
      shareReplay(1),
    );
    this.cache.set(trackId, req);
    return req;
  }
}
