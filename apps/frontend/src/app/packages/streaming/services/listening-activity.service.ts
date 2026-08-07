import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

export type ActivityPeriod = '7d' | '30d' | '90d' | 'all';

export interface ListeningActivityResponse {
  period: string;
  period_start: string | null;
  period_end: string;
  timezone: string;
  empty: boolean;
  message: string;
  summary: {
    plays: number;
    distinct_tracks: number;
    distinct_artists: number;
    listened_ms: number;
    listened_minutes: number;
    active_days: number;
  };
  top_tracks: Array<{
    rank: number;
    id_track: number;
    nombre_track: string;
    nombre_artista?: string;
    id_artista?: number;
    plays: number;
    listened_ms: number;
    playback_status?: string;
    source_unavailable?: boolean;
    duration_ms?: number;
  }>;
  top_artists: Array<{
    rank: number;
    id_artista: number;
    nombre_artista: string;
    plays: number;
    listened_ms: number;
    listened_minutes: number;
  }>;
  top_genres: Array<{
    rank: number;
    id_genero: number;
    nombre_genero: string;
    plays: number;
    share_pct: number;
  }>;
  timeline: Array<{ date: string; plays: number; listened_minutes: number }>;
  recent: Array<{
    id: number;
    id_track: number;
    played_at?: string;
    listened_ms: number;
    nombre_track: string;
    nombre_artista?: string;
    id_artista?: number;
    playback_status?: string;
    source_unavailable?: boolean;
  }>;
}

@Injectable({ providedIn: 'root' })
export class ListeningActivityService {
  private http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/me/listening-activity`;

  getActivity(period: ActivityPeriod = '30d'): Observable<ListeningActivityResponse> {
    const params = new HttpParams().set('period', period);
    return this.http.get<ListeningActivityResponse>(this.base, { params });
  }
}
