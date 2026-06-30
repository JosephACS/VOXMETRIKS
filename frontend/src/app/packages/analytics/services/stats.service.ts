import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { ReadCache } from '../../../core/http/read-cache';
import {
  StatsSummary, TopTrack, DistribucionEnergia, LoadRecord, GeneroPopularidad,
  SyntheticResult, SyntheticLimits, CatalogGrowthPoint,
  ImportResult,
  WarehouseStatus, TrendingAnalytics, PlatformAnalytics, EngagementAnalytics,
  WarehouseTableMeta, TablePreview, RecommendationPayload, HealthResponse, HistoryHub,
  PaginatedResponse,
} from '../../../shared/models/api.models';

@Injectable({ providedIn: 'root' })
export class StatsService {
  private readonly http = inject(HttpClient);
  private readonly BASE = `${environment.apiUrl}/stats`;
  private readonly summaryCache = new ReadCache<StatsSummary>();
  private readonly growthCache = new ReadCache<CatalogGrowthPoint[]>();
  private readonly topTracksCaches = new Map<number, ReadCache<TopTrack[]>>();

  getSummary(): Observable<StatsSummary> {
    return this.summaryCache.get(() => this.http.get<StatsSummary>(`${this.BASE}/summary`));
  }

  invalidateSummary(): void {
    this.summaryCache.invalidate();
  }

  getTopTracks(limit = 10): Observable<TopTrack[]> {
    let cache = this.topTracksCaches.get(limit);
    if (!cache) {
      cache = new ReadCache<TopTrack[]>();
      this.topTracksCaches.set(limit, cache);
    }
    const params = new HttpParams().set('limit', limit);
    return cache.get(() => this.http.get<TopTrack[]>(`${this.BASE}/top-tracks`, { params }));
  }

  invalidateTopTracks(limit?: number): void {
    if (limit != null) {
      this.topTracksCaches.get(limit)?.invalidate();
      return;
    }
    this.topTracksCaches.forEach((c) => c.invalidate());
  }

  getEnergyDistribution(): Observable<DistribucionEnergia[]> {
    return this.http.get<DistribucionEnergia[]>(`${this.BASE}/energy-distribution`);
  }

  getLastLoads(limit = 5): Observable<LoadRecord[]> {
    const params = new HttpParams().set('limit', limit);
    return this.http.get<LoadRecord[]>(`${this.BASE}/loads`, { params });
  }

  getGenreStats(page = 1, limit = 20, search?: string): Observable<PaginatedResponse<GeneroPopularidad>> {
    let params = new HttpParams().set('page', page).set('limit', limit);
    if (search) params = params.set('search', search);
    return this.http.get<PaginatedResponse<GeneroPopularidad>>(`${environment.apiUrl}/genres/stats`, { params });
  }

  generateSynthetic(body: { target_total?: number; multiplier?: number }): Observable<SyntheticResult> {
    return this.http.post<SyntheticResult>(`${this.BASE}/synthetic`, body);
  }

  importFromPocketBase(): Observable<ImportResult> {
    return this.http.post<ImportResult>(`${this.BASE}/import`, {});
  }

  getSyntheticLimits(): Observable<SyntheticLimits> {
    return this.http.get<SyntheticLimits>(`${this.BASE}/synthetic/limits`);
  }

  getCatalogGrowth(months = 12): Observable<CatalogGrowthPoint[]> {
    return this.growthCache.get(() => {
      const params = new HttpParams().set('months', months);
      return this.http.get<CatalogGrowthPoint[]>(`${this.BASE}/catalog-growth`, { params });
    });
  }

  invalidateCatalogGrowth(): void {
    this.growthCache.invalidate();
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
    return this.http.get<TablePreview>(`${environment.apiUrl}/analytics/explorer/preview/${table}`, { params });
  }

  getRecommendations(limit = 12, mood?: string): Observable<RecommendationPayload> {
    let params = new HttpParams().set('limit', limit);
    if (mood) params = params.set('mood', mood);
    return this.http.get<RecommendationPayload>(`${environment.apiUrl}/analytics/recommendations`, { params });
  }

  getHealth(): Observable<HealthResponse> {
    return this.http.get<HealthResponse>(`${this.BASE}/health`);
  }

  getHistoryHub(limit = 30): Observable<HistoryHub> {
    const params = new HttpParams().set('limit', limit);
    return this.http.get<HistoryHub>(`${environment.apiUrl}/analytics/history`, { params });
  }
}
