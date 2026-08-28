import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, of, throwError } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';
import { environment } from '../../../../environments/environment';
import {
  Track, TrackCreate, TrackUpdate,
  AudioFeatures, PaginatedResponse,
  TrackSearchParams, DeleteResponse,
  TrackSearchResult, TrackDetail, AudioSource, CoverArt,
} from '../../../shared/models/api.models';
import { CatalogCacheService } from '../../../core/services/catalog-cache.service';

export interface MusicSearchExternalItem {
  video_id: string;
  title: string;
  channel_title?: string;
  duration_sec?: number;
  thumbnail?: string;
  score?: number;
  origin?: string;
}

export interface MusicSearchResponse {
  query: string;
  phase: string;
  message: string;
  local: { items: TrackSearchResult[]; total: number; page: number; limit: number };
  external: MusicSearchExternalItem[];
  missing_local?: TrackSearchResult[];
  match_mode?: 'exact' | 'related';
  external_available: boolean;
  catalog_source?: 'spotify';
  audio_fallback?: 'deezer';
}

/**
 * Catalog CRUD / search / audio-source API (`/api/v1/tracks`).
 * Canonical for streaming catalog.
 * Distinct from `core/services/tracks.service` (EnterpriseTracksService).
 */
@Injectable({ providedIn: 'root' })
export class TracksService {
  private readonly http = inject(HttpClient);
  private readonly cache = inject(CatalogCacheService);
  private readonly API_URL = `${environment.apiUrl}/tracks`;

  listTracks(
    page = 1,
    limit = 50,
    search?: string,
    genreId?: number,
    artistId?: number,
    playableOnly = false,
  ): Observable<PaginatedResponse<Track>> {
    let params = new HttpParams().set('page', page).set('limit', limit);
    if (search?.trim())   params = params.set('search', search.trim());
    if (genreId  != null) params = params.set('genre_id', genreId);
    if (artistId != null) params = params.set('artist_id', artistId);
    params = params.set('playable_only', playableOnly ? 'true' : 'false');
    const key = `tracks:${params.toString()}`;
    return this.cachedGet(key, () => this.http.get<PaginatedResponse<Track>>(this.API_URL, { params }));
  }

  getTracks(p?: TrackSearchParams): Observable<PaginatedResponse<Track>> {
    let params = new HttpParams().set('page', p?.page ?? 1).set('limit', p?.limit ?? 50);
    if (p?.search)            params = params.set('search', p.search);
    if (p?.artist_id != null) params = params.set('artist_id', p.artist_id);
    if (p?.genre_id  != null) params = params.set('genre_id', p.genre_id);
    params = params.set('playable_only', p?.playable_only ? 'true' : 'false');
    const key = `tracks:${params.toString()}`;
    return this.cachedGet(key, () => this.http.get<PaginatedResponse<Track>>(this.API_URL, { params }));
  }

  getTrackById(id: number): Observable<Track> {
    return this.cachedGet(`track:${id}`, () => this.http.get<Track>(`${this.API_URL}/${id}`));
  }

  getTrackFeatures(id: number): Observable<AudioFeatures> {
    return this.cachedGet(`track-features:${id}`, () => this.http.get<AudioFeatures>(`${this.API_URL}/${id}/features`));
  }

  createTrack(body: TrackCreate): Observable<Track> {
    return this.http.post<Track>(this.API_URL, body).pipe(
      tap(() => this.invalidateCatalogCache()),
    );
  }

  updateTrack(id: number, body: TrackUpdate): Observable<Track> {
    return this.http.put<Track>(`${this.API_URL}/${id}`, body).pipe(
      tap(() => {
        this.invalidateCatalogCache();
        this.cache.invalidate(`track:${id}`);
        this.cache.invalidate(`track-features:${id}`);
        this.cache.invalidate(`track-detail:${id}`);
        this.cache.invalidate(`track-cover:${id}`);
      }),
    );
  }

  deleteTrack(id: number): Observable<DeleteResponse> {
    return this.http.delete<DeleteResponse>(`${this.API_URL}/${id}`).pipe(
      tap(() => {
        this.invalidateCatalogCache();
        this.cache.invalidate(`track:${id}`);
        this.cache.invalidate(`track-features:${id}`);
        this.cache.invalidate(`track-detail:${id}`);
        this.cache.invalidate(`track-cover:${id}`);
      }),
    );
  }

  searchTracks(q: string, page = 1, limit = 20, playableOnly = false): Observable<PaginatedResponse<TrackSearchResult>> {
    const params = new HttpParams()
      .set('q', q)
      .set('page', page)
      .set('limit', limit)
      .set('playable_only', playableOnly ? 'true' : 'false');
    return this.cachedGet(`track-search:${params.toString()}`, () =>
      this.http.get<PaginatedResponse<TrackSearchResult>>(`${this.API_URL}/search`, { params }),
    );
  }

  musicSearch(
    q: string,
    page = 1,
    limit = 20,
    allowExternal = true,
    includeRelated = false,
  ): Observable<MusicSearchResponse> {
    const params = new HttpParams()
      .set('q', q)
      .set('page', page)
      .set('limit', limit)
      .set('allow_external', allowExternal ? 'true' : 'false')
      .set('include_related', includeRelated ? 'true' : 'false');
    return this.cachedGet(`music-search:${params.toString()}`, () =>
      this.http.get<MusicSearchResponse>(`${this.API_URL}/music-search`, { params }),
    );
  }

  getTrackDetail(id: number): Observable<TrackDetail> {
    return this.cachedGet(`track-detail:${id}`, () => this.http.get<TrackDetail>(`${this.API_URL}/${id}/detail`));
  }

  getAudioSource(
    id: number,
    opts: boolean | {
      force?: boolean;
      skipProvider?: string;
      excludeSourceRef?: string;
      asyncResolve?: boolean;
    } = false,
    skipProvider?: string,
  ): Observable<AudioSource> {
    // Back-compat: getAudioSource(id, force, skipProvider)
    const options =
      typeof opts === 'boolean'
        ? { force: opts, skipProvider, asyncResolve: opts ? false : true }
        : opts;

    let params = new HttpParams();
    if (options.force) params = params.set('force', 'true');
    if (options.skipProvider) params = params.set('skip_provider', options.skipProvider);
    if (options.excludeSourceRef) {
      params = params.set('exclude_source_ref', options.excludeSourceRef);
    }
    if (options.asyncResolve === false) params = params.set('async_resolve', 'false');
    return this.http.get<AudioSource>(`${this.API_URL}/${id}/audio-source`, {
      params: params.keys().length ? params : undefined,
    });
  }

  reportAudioSourceFailure(id: number): Observable<{ track_id: number; status: string }> {
    return this.http.post<{ track_id: number; status: string }>(
      `${this.API_URL}/${id}/audio-source/failure`,
      {},
    );
  }

  getCover(id: number): Observable<CoverArt> {
    return this.cachedGet(`track-cover:${id}`, () => this.http.get<CoverArt>(`${this.API_URL}/${id}/cover`), 10 * 60_000);
  }

  private cachedGet<T>(key: string, request: () => Observable<T>, ttlMs = 60_000): Observable<T> {
    const cached = this.cache.get<T>(key, ttlMs);
    if (cached !== null) return of(cached);
    return request().pipe(
      tap((value) => this.cache.set(key, value, ttlMs)),
      catchError((error) => {
        this.cache.invalidate(key);
        return throwError(() => error);
      }),
    );
  }

  private invalidateCatalogCache(): void {
    this.cache.invalidate('tracks:');
    this.cache.invalidate('track-search:');
    this.cache.invalidate('music-search:');
  }
}
