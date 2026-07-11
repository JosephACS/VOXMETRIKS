import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

export interface NLSearchResult {
  query: string;
  intent: Record<string, unknown>;
  tracks: Array<Record<string, unknown>>;
  total: number;
}

export interface PlaylistPreview {
  name: string;
  description: string;
  tracks: Array<{ id_track: number; nombre_track?: string; nombre_artista?: string }>;
  track_count: number;
  requires_confirmation: boolean;
  provider?: string;
}

export interface DJSession {
  blocks: Array<{
    id: string;
    title: string;
    narration: string;
    tracks: Array<Record<string, unknown>>;
  }>;
  primary_mood?: string;
  mood_profile?: Record<string, unknown>;
}

@Injectable({ providedIn: 'root' })
export class AIService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/ai`;

  providerStatus(): Observable<Record<string, unknown>> {
    return this.http.get<Record<string, unknown>>(`${this.base}/provider/status`);
  }

  naturalSearch(query: string): Observable<NLSearchResult> {
    return this.http.post<NLSearchResult>(`${this.base}/search/natural`, { query });
  }

  previewPlaylist(prompt: string, limit = 20): Observable<PlaylistPreview> {
    return this.http.post<PlaylistPreview>(`${this.base}/playlist/preview`, { prompt, limit });
  }

  confirmPlaylist(name: string, description: string, trackIds: number[]): Observable<{ playlist_id: number; tracks_added: number }> {
    return this.http.post<{ playlist_id: number; tracks_added: number }>(`${this.base}/playlist/confirm`, {
      name,
      description,
      track_ids: trackIds,
    });
  }

  explainRecommendation(trackId: number): Observable<{ explanation: string }> {
    return this.http.get<{ explanation: string }>(`${this.base}/explain/recommendation/${trackId}`);
  }

  moodProfile(): Observable<Record<string, unknown>> {
    return this.http.get<Record<string, unknown>>(`${this.base}/mood-profile`);
  }

  djSession(): Observable<DJSession> {
    return this.http.get<DJSession>(`${this.base}/dj/session`);
  }
}
