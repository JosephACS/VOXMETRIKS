import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { StatsAnalyticsApi } from '../api/stats-analytics.api';
import { StatsDashboardApi } from '../api/stats-dashboard.api';
import { StatsExplorerApi } from '../api/stats-explorer.api';
import { StatsRecommendationsApi } from '../api/stats-recommendations.api';
import {
  StatsSummary, TopTrack, DistribucionEnergia, LoadRecord, GeneroPopularidad,
  SyntheticResult, SyntheticLimits, CatalogGrowthPoint,
  ImportResult,
  WarehouseStatus, TrendingAnalytics, PlatformAnalytics, EngagementAnalytics,
  WarehouseTableMeta, TablePreview, RecommendationPayload, HealthResponse, HistoryHub,
  PaginatedResponse, EventsBreakdown,
} from '../../../shared/models/api.models';

/** Facade over domain-scoped stats/analytics HTTP APIs. */
@Injectable({ providedIn: 'root' })
export class StatsService {
  private readonly dashboard = inject(StatsDashboardApi);
  private readonly analytics = inject(StatsAnalyticsApi);
  private readonly explorer = inject(StatsExplorerApi);
  private readonly recommendations = inject(StatsRecommendationsApi);

  getSummary(): Observable<StatsSummary> { return this.dashboard.getSummary(); }
  getEventsBreakdown(): Observable<EventsBreakdown> { return this.dashboard.getEventsBreakdown(); }
  invalidateSummary(): void { this.dashboard.invalidateSummary(); }
  getTopTracks(limit = 10): Observable<TopTrack[]> { return this.dashboard.getTopTracks(limit); }
  invalidateTopTracks(limit?: number): void { this.dashboard.invalidateTopTracks(limit); }
  getEnergyDistribution(): Observable<DistribucionEnergia[]> { return this.dashboard.getEnergyDistribution(); }
  getLastLoads(limit = 5): Observable<LoadRecord[]> { return this.dashboard.getLastLoads(limit); }
  getGenreStats(page = 1, limit = 20, search?: string): Observable<PaginatedResponse<GeneroPopularidad>> {
    return this.dashboard.getGenreStats(page, limit, search);
  }
  generateSynthetic(body: { target_total?: number; multiplier?: number }): Observable<SyntheticResult> {
    return this.dashboard.generateSynthetic(body);
  }
  importFromPocketBase(): Observable<ImportResult> { return this.dashboard.importFromPocketBase(); }
  getSyntheticLimits(): Observable<SyntheticLimits> { return this.dashboard.getSyntheticLimits(); }
  getCatalogGrowth(months = 12): Observable<CatalogGrowthPoint[]> { return this.dashboard.getCatalogGrowth(months); }
  invalidateCatalogGrowth(): void { this.dashboard.invalidateCatalogGrowth(); }
  getHealth(): Observable<HealthResponse> { return this.dashboard.getHealth(); }

  getWarehouseStatus(): Observable<WarehouseStatus> { return this.analytics.getWarehouseStatus(); }
  getTrendingAnalytics(limit = 25): Observable<TrendingAnalytics> { return this.analytics.getTrendingAnalytics(limit); }
  getPlatformAnalytics(): Observable<PlatformAnalytics> { return this.analytics.getPlatformAnalytics(); }
  getEngagementAnalytics(): Observable<EngagementAnalytics> { return this.analytics.getEngagementAnalytics(); }
  getHistoryHub(limit = 30): Observable<HistoryHub> { return this.analytics.getHistoryHub(limit); }

  getExplorerTables(): Observable<WarehouseTableMeta[]> { return this.explorer.getExplorerTables(); }
  getTablePreview(table: string, page = 1, limit = 50): Observable<TablePreview> {
    return this.explorer.getTablePreview(table, page, limit);
  }

  getRecommendations(limit = 12, mood?: string): Observable<RecommendationPayload> {
    return this.recommendations.getRecommendations(limit, mood);
  }
}
