import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  EngagementAnalytics,
  HistoryHub,
  PlatformAnalytics,
  TrendingAnalytics,
  WarehouseStatus,
} from '../../../shared/models/api.models';

@Injectable({ providedIn: 'root' })
export class StatsAnalyticsApi {
  private readonly http = inject(HttpClient);
  private readonly BASE = `${environment.apiUrl}/analytics`;

  getWarehouseStatus(): Observable<WarehouseStatus> {
    return this.http.get<WarehouseStatus>(`${this.BASE}/warehouse`);
  }

  getTrendingAnalytics(limit = 25): Observable<TrendingAnalytics> {
    const params = new HttpParams().set('limit', limit);
    return this.http.get<TrendingAnalytics>(`${this.BASE}/trending`, { params });
  }

  getPlatformAnalytics(): Observable<PlatformAnalytics> {
    return this.http.get<PlatformAnalytics>(`${this.BASE}/platform`);
  }

  getEngagementAnalytics(): Observable<EngagementAnalytics> {
    return this.http.get<EngagementAnalytics>(`${this.BASE}/engagement`);
  }

  getHistoryHub(limit = 30): Observable<HistoryHub> {
    const params = new HttpParams().set('limit', limit);
    return this.http.get<HistoryHub>(`${this.BASE}/history`, { params });
  }
}
