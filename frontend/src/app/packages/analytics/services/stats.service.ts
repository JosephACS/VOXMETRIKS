import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  StatsSummary, TopTrack, DistribucionEnergia, LoadRecord, GeneroPopularidad
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
}
