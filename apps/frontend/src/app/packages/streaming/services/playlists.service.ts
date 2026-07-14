import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { ReadCache } from '../../../core/http/read-cache';
import {
  PlaylistSummary, PlaylistDetail, PlaylistCreate, PlaylistUpdate, DeleteResponse,
  PaginatedResponse,
} from '../../../shared/models/api.models';

@Injectable({ providedIn: 'root' })
export class PlaylistsService {
  private readonly http = inject(HttpClient);
  private readonly API = `${environment.apiUrl}/playlists`;
  private readonly CATALOG_API = `${environment.apiUrl}/catalog/playlists`;
  private readonly listCache = new ReadCache<PlaylistSummary[]>();

  list(): Observable<PlaylistSummary[]> {
    return this.listCache.get(() => this.http.get<PlaylistSummary[]>(this.API));
  }

  private invalidateList(): void {
    this.listCache.invalidate();
  }

  get(id: number): Observable<PlaylistDetail> {
    return this.http.get<PlaylistDetail>(`${this.API}/${id}`);
  }

  listCatalog(opts: {
    page?: number;
    limit?: number;
    search?: string;
  } = {}): Observable<PaginatedResponse<PlaylistSummary>> {
    let params = new HttpParams()
      .set('page', String(opts.page ?? 1))
      .set('limit', String(opts.limit ?? 24));
    const q = opts.search?.trim();
    if (q) params = params.set('search', q);
    return this.http.get<PaginatedResponse<PlaylistSummary>>(this.CATALOG_API, { params });
  }

  getCatalog(id: number): Observable<PlaylistDetail> {
    return this.http.get<PlaylistDetail>(`${this.CATALOG_API}/${id}`);
  }

  create(body: PlaylistCreate): Observable<PlaylistSummary> {
    return this.http.post<PlaylistSummary>(this.API, body).pipe(
      tap(() => this.invalidateList()),
    );
  }

  addTrack(playlistId: number, trackId: number): Observable<{ added: boolean }> {
    return this.http.post<{ added: boolean }>(`${this.API}/${playlistId}/tracks`, { track_id: trackId }).pipe(
      tap(() => this.invalidateList()),
    );
  }

  removeTrack(playlistId: number, trackId: number): Observable<{ removed: boolean }> {
    return this.http.delete<{ removed: boolean }>(`${this.API}/${playlistId}/tracks/${trackId}`).pipe(
      tap(() => this.invalidateList()),
    );
  }

  update(id: number, body: PlaylistUpdate): Observable<PlaylistSummary> {
    return this.http.put<PlaylistSummary>(`${this.API}/${id}`, body).pipe(
      tap(() => this.invalidateList()),
    );
  }

  delete(id: number): Observable<DeleteResponse> {
    return this.http.delete<DeleteResponse>(`${this.API}/${id}`).pipe(
      tap(() => this.invalidateList()),
    );
  }
}
