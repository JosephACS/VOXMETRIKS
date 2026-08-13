import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  Track, TrackCreate, TrackUpdate,
  AudioFeatures, PaginatedResponse,
  TrackSearchParams, DeleteResponse,
  TrackSearchResult, TrackDetail, AudioSource, CoverArt,
} from '../../../shared/models/api.models';

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
  external_available: boolean;
}

export interface MusicAdoptResponse {
  track_id: number;
  created: boolean;
  video_id: string;
  title?: string;
  channel_title?: string;
  duration_ms?: number | null;
  thumbnail?: string;
}

/**
 * Catalog CRUD / search / audio-source API (`/api/v1/tracks`).
 * Canonical for streaming catalog.
 * Distinct from `core/services/tracks.service` (EnterpriseTracksService).
 */
@Injectable({ providedIn: 'root' })
export class TracksService {
  private readonly http = inject(HttpClient);
  private readonly API_URL = `${environment.apiUrl}/tracks`;

  listTracks(page = 1, limit = 50, search?: string, genreId?: number, artistId?: number): Observable<PaginatedResponse<Track>> {
    let params = new HttpParams().set('page', page).set('limit', limit);
    if (search?.trim())   params = params.set('search', search.trim());
    if (genreId  != null) params = params.set('genre_id', genreId);
    if (artistId != null) params = params.set('artist_id', artistId);
    return this.http.get<PaginatedResponse<Track>>(this.API_URL, { params });
  }

  getTracks(p?: TrackSearchParams): Observable<PaginatedResponse<Track>> {
    let params = new HttpParams().set('page', p?.page ?? 1).set('limit', p?.limit ?? 50);
    if (p?.search)            params = params.set('search', p.search);
    if (p?.artist_id != null) params = params.set('artist_id', p.artist_id);
    if (p?.genre_id  != null) params = params.set('genre_id', p.genre_id);
    return this.http.get<PaginatedResponse<Track>>(this.API_URL, { params });
  }

  getTrackById(id: number): Observable<Track> {
    return this.http.get<Track>(`${this.API_URL}/${id}`);
  }

  getTrackFeatures(id: number): Observable<AudioFeatures> {
    return this.http.get<AudioFeatures>(`${this.API_URL}/${id}/features`);
  }

  createTrack(body: TrackCreate): Observable<Track> {
    return this.http.post<Track>(this.API_URL, body);
  }

  updateTrack(id: number, body: TrackUpdate): Observable<Track> {
    return this.http.put<Track>(`${this.API_URL}/${id}`, body);
  }

  deleteTrack(id: number): Observable<DeleteResponse> {
    return this.http.delete<DeleteResponse>(`${this.API_URL}/${id}`);
  }

  searchTracks(q: string, page = 1, limit = 20): Observable<PaginatedResponse<TrackSearchResult>> {
    const params = new HttpParams().set('q', q).set('page', page).set('limit', limit);
    return this.http.get<PaginatedResponse<TrackSearchResult>>(`${this.API_URL}/search`, { params });
  }

  musicSearch(
    q: string,
    page = 1,
    limit = 20,
    allowExternal = true,
  ): Observable<MusicSearchResponse> {
    const params = new HttpParams()
      .set('q', q)
      .set('page', page)
      .set('limit', limit)
      .set('allow_external', allowExternal ? 'true' : 'false');
    return this.http.get<MusicSearchResponse>(`${this.API_URL}/music-search`, { params });
  }

  adoptYoutubeResult(
    videoId: string,
    trackId?: number,
    opts?: { requirePreferred?: boolean },
  ): Observable<MusicAdoptResponse> {
    const body: {
      video_id: string;
      track_id?: number;
      require_preferred?: boolean;
    } = { video_id: videoId };
    if (trackId != null) body.track_id = trackId;
    if (opts?.requirePreferred) body.require_preferred = true;
    return this.http.post<MusicAdoptResponse>(`${this.API_URL}/music-search/adopt`, body);
  }

  repairYoutubeSource(videoId: string): Observable<Record<string, unknown>> {
    return this.http.post<Record<string, unknown>>(`${this.API_URL}/music-search/repair-source`, {
      video_id: videoId,
    });
  }

  getTrackDetail(id: number): Observable<TrackDetail> {
    return this.http.get<TrackDetail>(`${this.API_URL}/${id}/detail`);
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
    return this.http.get<CoverArt>(`${this.API_URL}/${id}/cover`);
  }
}
