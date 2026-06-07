import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  PlaylistSummary, PlaylistDetail, PlaylistCreate, PlaylistUpdate, DeleteResponse,
} from '../../../shared/models/api.models';

@Injectable({ providedIn: 'root' })
export class PlaylistsService {
  private readonly http = inject(HttpClient);
  private readonly API = `${environment.apiUrl}/playlists`;

  list(): Observable<PlaylistSummary[]> {
    return this.http.get<PlaylistSummary[]>(this.API);
  }

  get(id: number): Observable<PlaylistDetail> {
    return this.http.get<PlaylistDetail>(`${this.API}/${id}`);
  }

  create(body: PlaylistCreate): Observable<PlaylistSummary> {
    return this.http.post<PlaylistSummary>(this.API, body);
  }

  addTrack(playlistId: number, trackId: number): Observable<{ added: boolean }> {
    return this.http.post<{ added: boolean }>(`${this.API}/${playlistId}/tracks`, { track_id: trackId });
  }

  removeTrack(playlistId: number, trackId: number): Observable<{ removed: boolean }> {
    return this.http.delete<{ removed: boolean }>(`${this.API}/${playlistId}/tracks/${trackId}`);
  }

  update(id: number, body: PlaylistUpdate): Observable<PlaylistSummary> {
    return this.http.put<PlaylistSummary>(`${this.API}/${id}`, body);
  }

  delete(id: number): Observable<DeleteResponse> {
    return this.http.delete<DeleteResponse>(`${this.API}/${id}`);
  }
}
