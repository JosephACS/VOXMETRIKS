import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, defer, from, map, of } from 'rxjs';
import { catchError, switchMap } from 'rxjs/operators';
import { environment } from '../../../../environments/environment';
import { SpotifyIntegrationService } from '../../../core/integrations/spotify/spotify-integration.service';
import {
  Artista, ArtistaCreate, ArtistaUpdate,
  ArtistCoverArt, ArtistStats, TopArtista, PaginatedResponse,
  ArtistSearchParams, DeleteResponse,
} from '../../../shared/models/api.models';

export interface ExternalArtistResult {
  id: string;
  name: string;
  imageUrl?: string;
  source: 'spotify' | 'deezer';
}

@Injectable({ providedIn: 'root' })
export class ArtistsService {
  private readonly http = inject(HttpClient);
  private readonly spotify = inject(SpotifyIntegrationService);
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

  /** Local artists are always resolved by the caller first; this is the external fallback. */
  searchExternal(name: string, limit = 6): Observable<ExternalArtistResult[]> {
    const query = name.trim();
    if (!query) return of([]);
    return defer(() => from(this.spotify.searchArtists(query, limit))).pipe(
      switchMap((spotifyArtists) =>
        spotifyArtists.length
          ? of(spotifyArtists)
          : defer(() => fetch(`https://api.deezer.com/search/artist?q=${encodeURIComponent(query)}&limit=${limit}`)).pipe(
              switchMap((response) => response.ok ? from(response.json()) : of({ data: [] })),
              map((payload: { data?: Array<{ id?: number; name?: string; picture_medium?: string }> }) =>
                (payload.data ?? [])
                  .filter((artist): artist is { id: number; name: string; picture_medium?: string } => !!artist.id && !!artist.name)
                  .map((artist) => ({
                    id: String(artist.id),
                    name: artist.name,
                    imageUrl: artist.picture_medium,
                    source: 'deezer' as const,
                  })),
              ),
            ),
      ),
      catchError(() => of([])),
    );
  }
}
