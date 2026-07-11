import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { ApiService } from './api.service';
import { TopTrack, TrackRecommendation } from '../models/enterprise-api.models';

@Injectable({ providedIn: 'root' })
export class EnterpriseTracksService {
  private readonly api = inject(ApiService);

  getTopTracks(limit = 20): Observable<TopTrack[]> {
    return this.api.get<TopTrack[]>('/tracks/top', { limit });
  }

  getTopTracksPage(page: number, pageSize = 20): Observable<{ items: TopTrack[]; total: number }> {
    return this.api
      .getPaginated<TopTrack[]>('/tracks/top', { page, page_size: pageSize })
      .pipe(map((res) => ({ items: res.items, total: res.total })));
  }

  getRecommendations(userId: number, limit = 20): Observable<TrackRecommendation[]> {
    return this.api.get<TrackRecommendation[]>(`/tracks/recommendations/${userId}`, {
      limit,
    });
  }
}
