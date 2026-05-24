import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import {
  Track,
  TrackFeatures,
  PaginatedTracks,
  PaginatedResponse,
  TrackSearchParams,
} from '../shared/models/api.models';

/**
 * TracksService
 * =============
 * Consumidor de endpoints: /api/v1/tracks
 * Mapea: backend/routes/tracks.py
 *
 * Endpoints:
 * - GET /api/v1/tracks?page=1&limit=10&search=...&artist_id=...&genre_id=...
 * - GET /api/v1/tracks/{id}
 * - GET /api/v1/tracks/{id}/features
 */
@Injectable({ providedIn: 'root' })
export class TracksService {
  private readonly http = inject(HttpClient);
  private readonly API_URL = `${environment.apiUrl}/tracks`;

  /**
   * GET /api/v1/tracks — lista paginada de tracks
   * listTracks() es el alias llamado por tracks.component
   */
  listTracks(
    page = 1,
    limit = 50,
    search?: string,
    genreId?: number,
    artistId?: number
  ): Observable<PaginatedResponse<Track>> {
    let params = new HttpParams()
      .set('page', page)
      .set('limit', limit);
    if (search?.trim())   params = params.set('search',    search.trim());
    if (genreId  != null) params = params.set('genre_id',  genreId);
    if (artistId != null) params = params.set('artist_id', artistId);
    return this.http.get<PaginatedResponse<Track>>(this.API_URL, { params });
  }

  /**
   * getTracks() — overload alias para compatibilidad con params object
   */
  getTracks(p?: TrackSearchParams): Observable<PaginatedTracks> {
    let params = new HttpParams()
      .set('page',  p?.page  ?? 1)
      .set('limit', p?.limit ?? 50);
    if (p?.search)    params = params.set('search',    p.search);
    if (p?.artist_id != null) params = params.set('artist_id', p.artist_id);
    if (p?.genre_id  != null) params = params.set('genre_id',  p.genre_id);
    return this.http.get<PaginatedTracks>(this.API_URL, { params });
  }

  /** GET /api/v1/tracks/{id} */
  getTrackById(id: number): Observable<Track> {
    return this.http.get<Track>(`${this.API_URL}/${id}`);
  }

  /** GET /api/v1/tracks/{id}/features */
  getTrackFeatures(id: number): Observable<TrackFeatures> {
    return this.http.get<TrackFeatures>(`${this.API_URL}/${id}/features`);
  }
}
