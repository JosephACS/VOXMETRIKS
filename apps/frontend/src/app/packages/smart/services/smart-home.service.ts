import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { SmartArtistItem, SmartHomeResponse, SmartTrackItem } from '../models/smart-home.models';

@Injectable({ providedIn: 'root' })
export class SmartHomeService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/smart`;

  getHome(): Observable<SmartHomeResponse> {
    return this.http.get<SmartHomeResponse>(`${this.base}/home`);
  }

  getProfile(): Observable<SmartHomeResponse['profile']> {
    return this.http.get<SmartHomeResponse['profile']>(`${this.base}/profile`);
  }

  getRecommendations(limit = 20): Observable<{ user_id: number; tracks: SmartTrackItem[] }> {
    return this.http.get<{ user_id: number; tracks: SmartTrackItem[] }>(
      `${this.base}/recommendations`,
      { params: { limit: String(limit) } },
    );
  }

  getSimilarTracks(trackId: number): Observable<{ track_id: number; similar: SmartTrackItem[] }> {
    return this.http.get<{ track_id: number; similar: SmartTrackItem[] }>(
      `${this.base}/similar-tracks/${trackId}`,
    );
  }

  getSimilarArtists(artistId: number): Observable<{ artist_id: number; similar: SmartArtistItem[] }> {
    return this.http.get<{ artist_id: number; similar: SmartArtistItem[] }>(
      `${this.base}/similar-artists/${artistId}`,
    );
  }
}
