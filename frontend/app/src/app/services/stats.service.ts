import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';
import {
  SummaryStats,
  StatsSummary,
  EnergyDistribution,
  DistribucionEnergia,
  TopTrack,
  LoadRecord,
  LoadStats,
  Track,
} from '../shared/models/api.models';

/**
 * StatsService
 * ============
 * Consumidor de endpoints: /api/v1/stats
 * Mapea: backend/routes/stats.py
 *
 * Endpoints:
 * - GET /api/v1/stats/summary
 * - GET /api/v1/stats/energia
 * - GET /api/v1/stats/top-tracks?limit=10
 * - GET /api/v1/stats/loads?limit=10
 */
@Injectable({ providedIn: 'root' })
export class StatsService {
  private readonly http = inject(HttpClient);
  private readonly API_URL = `${environment.apiUrl}/stats`;

  /**
   * GET /api/v1/stats/summary — conteos totales del warehouse
   *
   * getSummary()      ← llamado por dashboard.component
   * getSummaryStats() ← overload para compatibilidad
   */
  getSummary(): Observable<StatsSummary> {
    return this.http.get<StatsSummary>(`${this.API_URL}/summary`);
  }

  getSummaryStats(): Observable<SummaryStats> {
    return this.getSummary();
  }

  /**
   * GET /api/v1/stats/energia — distribución de energía (agg_distribucion_energia)
   *
   * getEnergiaDistribution() ← llamado por dashboard.component
   * getEnergyDistribution()  ← overload para compatibilidad
   */
  getEnergiaDistribution(): Observable<DistribucionEnergia[]> {
    return this.http.get<DistribucionEnergia[]>(`${this.API_URL}/energia`);
  }

  getEnergyDistribution(): Observable<EnergyDistribution[]> {
    return this.getEnergiaDistribution();
  }

  /**
   * GET /api/v1/stats/top-tracks — top tracks por popularidad
   */
  getTopTracks(limit = 10): Observable<TopTrack[]> {
    const params = new HttpParams().set('limit', limit);
    return this.http.get<TopTrack[]>(`${this.API_URL}/top-tracks`, { params });
  }

  /**
   * GET /api/v1/stats/loads — historial de cargas ELT (ctl_carga_dataset)
   *
   * getLoadHistory() ← llamado por dashboard.component
   * getLoadStats()   ← overload para compatibilidad
   */
  getLoadHistory(limit = 5): Observable<LoadRecord[]> {
    const params = new HttpParams().set('limit', limit);
    return this.http.get<LoadRecord[]>(`${this.API_URL}/loads`, { params });
  }

  getLoadStats(limit = 10): Observable<LoadStats[]> {
    return this.getLoadHistory(limit);
  }
}
