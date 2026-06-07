import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  StatsSummary, TopTrack, DistribucionEnergia, LoadRecord, GeneroPopularidad,
  SyntheticResult, SyntheticLimits, CatalogGrowthPoint,
  WarehouseStatus, TrendingAnalytics, PlatformAnalytics, EngagementAnalytics,
  WarehouseTableMeta, TablePreview, RecommendationPayload, HealthResponse, HistoryHub,
} from '../../../shared/models/api.models';

@Injectable({ providedIn: 'root' })
export class StatsService {
  private readonly http = inject(HttpClient);
  private readonly BASE = `${environment.apiUrl}/stats`;

  getSummary(): Observable<StatsSummary> {
    return this.http.get<StatsSummary>(`${this.BASE}/summary`);
  }

  getTopTracks(limit = 10): Observable<TopTrack[]> {
    const params = new HttpParams().set('limit', limit);
    return this.http.get<TopTrack[]>(`${this.BASE}/top-tracks`, { params });
  }

  getEnergyDistribution(): Observable<DistribucionEnergia[]> {
    return this.http.get<DistribucionEnergia[]>(`${this.BASE}/energy-distribution`);
  }

  getLastLoads(limit = 5): Observable<LoadRecord[]> {
    const params = new HttpParams().set('limit', limit);
    return this.http.get<LoadRecord[]>(`${this.BASE}/loads`, { params });
  }

  getGenreStats(limit = 20): Observable<GeneroPopularidad[]> {
    const params = new HttpParams().set('limit', limit);
    return this.http.get<GeneroPopularidad[]>(`${environment.apiUrl}/genres/stats`, { params });
  }

  generateSynthetic(body: { target_total?: number; multiplier?: number }): Observable<SyntheticResult> {
    return this.http.post<SyntheticResult>(`${this.BASE}/synthetic`, body);
  }

  getSyntheticLimits(): Observable<SyntheticLimits> {
    return this.http.get<SyntheticLimits>(`${this.BASE}/synthetic/limits`);
  }

  getCatalogGrowth(months = 12): Observable<CatalogGrowthPoint[]> {
    const params = new HttpParams().set('months', months);
    return this.http.get<CatalogGrowthPoint[]>(`${this.BASE}/catalog-growth`, { params });
  }

  getWarehouseStatus(): Observable<WarehouseStatus> {
    return this.http.get<WarehouseStatus>(`${environment.apiUrl}/analytics/warehouse`);
  }

  getTrendingAnalytics(limit = 25): Observable<TrendingAnalytics> {
    const params = new HttpParams().set('limit', limit);
    return this.http.get<TrendingAnalytics>(`${environment.apiUrl}/analytics/trending`, { params });
  }

  getPlatformAnalytics(): Observable<PlatformAnalytics> {
    return this.http.get<PlatformAnalytics>(`${environment.apiUrl}/analytics/platform`);
  }

  getEngagementAnalytics(): Observable<EngagementAnalytics> {
    return this.http.get<EngagementAnalytics>(`${environment.apiUrl}/analytics/engagement`);
  }

  getExplorerTables(): Observable<WarehouseTableMeta[]> {
    return this.http.get<WarehouseTableMeta[]>(`${environment.apiUrl}/analytics/explorer/tables`);
  }

  getTablePreview(table: string, page = 1, limit = 8): Observable<TablePreview> {
    const params = new HttpParams().set('page', page).set('limit', limit);
    return this.http.get<TablePreview>(
      `${environment.apiUrl}/analytics/explorer/preview/${encodeURIComponent(table)}`,
      { params },
    );
  }

  getRecommendations(limit = 12, mood?: string): Observable<RecommendationPayload> {
    let params = new HttpParams().set('limit', limit);
    if (mood) params = params.set('mood', mood);
    return this.http.get<RecommendationPayload>(`${environment.apiUrl}/analytics/recommendations`, { params });
  }

  getHealth(): Observable<HealthResponse> {
    const root = environment.apiUrl.replace(/\/api\/v1\/?$/, '');
    return this.http.get<HealthResponse>(`${root}/health`);
  }

  getHistoryHub(limit = 25): Observable<HistoryHub> {
    const params = new HttpParams().set('limit', limit);
    return this.http.get<HistoryHub>(`${environment.apiUrl}/analytics/history`, { params });
  }
}
