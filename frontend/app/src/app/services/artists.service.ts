import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../environments/environment';
import {
  Artist,
  ArtistStats,
  PaginatedArtists,
  PaginatedResponse,
  TopArtista,
  Artista,
  ArtistSearchParams,
} from '../shared/models/api.models';

/**
 * ArtistsService
 * ==============
 * Consumidor de endpoints: /api/v1/artists
 * Mapea: backend/routes/artists.py
 *
 * Endpoints:
 * - GET /api/v1/artists?page=1&limit=10&search=...&genre_id=...
 * - GET /api/v1/artists/top?limit=10
 * - GET /api/v1/artists/{id}
 * - GET /api/v1/artists/{id}/stats
 */
@Injectable({ providedIn: 'root' })
export class ArtistsService {
  private readonly http = inject(HttpClient);
  private readonly API_URL = `${environment.apiUrl}/artists`;

  // ── Alias map: backend devuelve lista directa o paginada ─────────────────

  /**
   * GET /api/v1/artists — lista paginada
   * Alias: getArtists() — compatible con artists.component que llama listArtists()
   */
  listArtists(
    page = 1,
    limit = 50,
    search?: string
  ): Observable<PaginatedResponse<Artista>> {
    let params = new HttpParams()
      .set('page', page)
      .set('limit', limit);
    if (search?.trim()) params = params.set('search', search.trim());
    return this.http.get<PaginatedResponse<Artista>>(this.API_URL, { params });
  }

  /** Overload alias used by legacy call sites */
  getArtists(p?: ArtistSearchParams): Observable<PaginatedArtists> {
    let params = new HttpParams()
      .set('page', p?.page ?? 1)
      .set('limit', p?.limit ?? 50);
    if (p?.search) params = params.set('search', p.search);
    if (p?.genre_id != null) params = params.set('genre_id', p.genre_id);
    return this.http.get<PaginatedArtists>(this.API_URL, { params });
  }

  /**
   * GET /api/v1/artists/top — top artistas por popularidad.
   *
   * El backend puede devolver:
   *   a) TopArtista[]          (array directo)
   *   b) { artistas: TopArtista[], total: number }
   *
   * Este método normaliza ambas formas y siempre devuelve TopArtista[].
   */
  getTopArtists(limit = 10): Observable<TopArtista[]> {
    const params = new HttpParams().set('limit', limit);
    return this.http
      .get<TopArtista[] | { artistas: TopArtista[]; total: number }>(
        `${this.API_URL}/top`,
        { params }
      )
      .pipe(
        map(res => (Array.isArray(res) ? res : (res as any).artistas ?? []))
      );
  }

  /** GET /api/v1/artists/{id} */
  getArtistById(id: number): Observable<Artist> {
    return this.http.get<Artist>(`${this.API_URL}/${id}`);
  }

  /** GET /api/v1/artists/{id}/stats */
  getArtistStats(id: number): Observable<ArtistStats> {
    return this.http.get<ArtistStats>(`${this.API_URL}/${id}/stats`);
  }
}
