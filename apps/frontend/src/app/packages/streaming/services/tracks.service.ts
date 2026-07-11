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

  getTrackDetail(id: number): Observable<TrackDetail> {
    return this.http.get<TrackDetail>(`${this.API_URL}/${id}/detail`);
  }

  getAudioSource(id: number, force = false, skipProvider?: string): Observable<AudioSource> {
    let params = new HttpParams();
    if (force) params = params.set('force', 'true');
    if (skipProvider) params = params.set('skip_provider', skipProvider);
    return this.http.get<AudioSource>(`${this.API_URL}/${id}/audio-source`, {
      params: params.keys().length ? params : undefined,
    });
  }

  getCover(id: number): Observable<CoverArt> {
    return this.http.get<CoverArt>(`${this.API_URL}/${id}/cover`);
  }
}
