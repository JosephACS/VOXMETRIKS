import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  Artista, ArtistaCreate, ArtistaUpdate,
  ArtistCoverArt, ArtistStats, TopArtista, PaginatedResponse,
  ArtistSearchParams, DeleteResponse,
} from '../../../shared/models/api.models';

@Injectable({ providedIn: 'root' })
export class ArtistsService {
  private readonly http = inject(HttpClient);
  private readonly API_URL = `${environment.apiUrl}/catalog/artists`;

  listArtists(page = 1, limit = 50, search?: string): Observable<PaginatedResponse<Artista>> {
    let params = new HttpParams().set('page', page).set('limit', limit);
    if (search?.trim()) params = params.set('search', search.trim());
    return this.http.get<PaginatedResponse<Artista>>(this.API_URL, { params });
  }

  getArtists(p?: ArtistSearchParams): Observable<PaginatedResponse<Artista>> {
    let params = new HttpParams()
      .set('page', p?.page ?? 1)
      .set('limit', p?.limit ?? 50);
    if (p?.search) params = params.set('search', p.search);
    return this.http.get<PaginatedResponse<Artista>>(this.API_URL, { params });
  }

  getTopArtists(limit = 10): Observable<TopArtista[]> {
    const params = new HttpParams().set('limit', limit);
    return this.http
      .get<TopArtista[] | { artistas: TopArtista[] }>(`${this.API_URL}/top`, { params })
      .pipe(map(res => (Array.isArray(res) ? res : (res as { artistas?: TopArtista[] }).artistas ?? [])));
  }

  getArtistById(id: number): Observable<Artista> {
    return this.http.get<Artista>(`${this.API_URL}/${id}`);
  }

  getArtistStats(id: number): Observable<ArtistStats> {
    return this.http.get<ArtistStats>(`${this.API_URL}/${id}/stats`);
  }

  getCover(id: number): Observable<ArtistCoverArt> {
    return this.http.get<ArtistCoverArt>(`${this.API_URL}/${id}/cover`);
  }

  createArtist(body: ArtistaCreate): Observable<Artista> {
    return this.http.post<Artista>(this.API_URL, body);
  }

  updateArtist(id: number, body: ArtistaUpdate): Observable<Artista> {
    return this.http.put<Artista>(`${this.API_URL}/${id}`, body);
  }

  deleteArtist(id: number): Observable<DeleteResponse> {
    return this.http.delete<DeleteResponse>(`${this.API_URL}/${id}`);
  }
}
