import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import {
  Genre,
  GenreStats,
  GeneroPopularidad,
  PaginatedGenres,
  GenreSearchParams,
} from '../shared/models/api.models';

/**
 * GenresService
 * =============
 * Consumidor de endpoints: /api/v1/genres
 * Mapea: backend/routes/genres.py
 *
 * Endpoints:
 * - GET /api/v1/genres?page=1&limit=10&search=...
 * - GET /api/v1/genres/stats?limit=50
 * - GET /api/v1/genres/{id}
 */
@Injectable({ providedIn: 'root' })
export class GenresService {
  private readonly http = inject(HttpClient);
  private readonly API_URL = `${environment.apiUrl}/genres`;

  /**
   * GET /api/v1/genres — lista paginada de géneros
   */
  getGenres(params?: GenreSearchParams): Observable<PaginatedGenres> {
    let httpParams = new HttpParams()
      .set('page', params?.page ?? 1)
      .set('limit', params?.limit ?? 50);
    if (params?.search) httpParams = httpParams.set('search', params.search);
    return this.http.get<PaginatedGenres>(this.API_URL, { params: httpParams });
  }

  /**
   * GET /api/v1/genres/stats — estadísticas agregadas por género
   * Alias getGenreStats() = alias usado por genres.component
   */
  getGenreStats(limit = 50): Observable<GeneroPopularidad[]> {
    const params = new HttpParams().set('limit', limit);
    return this.http.get<GeneroPopularidad[]>(`${this.API_URL}/stats`, { params });
  }

  /** GET /api/v1/genres/{id} */
  getGenreById(id: number): Observable<Genre> {
    return this.http.get<Genre>(`${this.API_URL}/${id}`);
  }
}
