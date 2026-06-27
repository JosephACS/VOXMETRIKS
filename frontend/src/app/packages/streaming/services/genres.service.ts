import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  Genero, GeneroCreate, GeneroUpdate,
  GeneroPopularidad, PaginatedResponse,
  GenreSearchParams, DeleteResponse,
} from '../../../shared/models/api.models';

@Injectable({ providedIn: 'root' })
export class GenresService {
  private readonly http = inject(HttpClient);
  private readonly API_URL = `${environment.apiUrl}/genres`;

  getGenres(params?: GenreSearchParams): Observable<PaginatedResponse<Genero>> {
    let httpParams = new HttpParams()
      .set('page', params?.page ?? 1)
      .set('limit', params?.limit ?? 50);
    if (params?.search) httpParams = httpParams.set('search', params.search);
    return this.http.get<PaginatedResponse<Genero>>(this.API_URL, { params: httpParams });
  }

  getGenreStats(page = 1, limit = 50, search?: string): Observable<PaginatedResponse<GeneroPopularidad>> {
    let httpParams = new HttpParams().set('page', page).set('limit', limit);
    if (search) httpParams = httpParams.set('search', search);
    return this.http.get<PaginatedResponse<GeneroPopularidad>>(`${this.API_URL}/stats`, { params: httpParams });
  }

  getGenreById(id: number): Observable<Genero> {
    return this.http.get<Genero>(`${this.API_URL}/${id}`);
  }

  createGenre(body: GeneroCreate): Observable<Genero> {
    return this.http.post<Genero>(this.API_URL, body);
  }

  updateGenre(id: number, body: GeneroUpdate): Observable<Genero> {
    return this.http.put<Genero>(`${this.API_URL}/${id}`, body);
  }

  deleteGenre(id: number): Observable<DeleteResponse> {
    return this.http.delete<DeleteResponse>(`${this.API_URL}/${id}`);
  }
}
