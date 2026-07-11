import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { RecommendationPayload } from '../../../shared/models/api.models';

@Injectable({ providedIn: 'root' })
export class StatsRecommendationsApi {
  private readonly http = inject(HttpClient);

  getRecommendations(limit = 12, mood?: string): Observable<RecommendationPayload> {
    let params = new HttpParams().set('limit', limit);
    if (mood) params = params.set('mood', mood);
    return this.http.get<RecommendationPayload>(`${environment.apiUrl}/analytics/recommendations`, { params });
  }
}
