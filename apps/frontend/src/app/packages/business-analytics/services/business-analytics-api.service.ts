import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  BusinessAlert, DashboardOverview, KpiDefinition, KpiSnapshot, Recommendation,
} from '../models/business-analytics.models';

const base = environment.apiUrl;

@Injectable({ providedIn: 'root' })
export class BusinessAnalyticsApiService {
  private http = inject(HttpClient);

  private orgHeaders(orgId: number) {
    return { 'X-Organization-Id': String(orgId) };
  }

  getDashboard(orgId: number): Observable<DashboardOverview> {
    return this.http.get<DashboardOverview>(`${base}/business-analytics/dashboard`, {
      headers: this.orgHeaders(orgId),
    });
  }

  listKpis(orgId: number): Observable<KpiDefinition[]> {
    return this.http.get<KpiDefinition[]>(`${base}/business-analytics/kpis`, {
      headers: this.orgHeaders(orgId),
    });
  }

  listSnapshots(orgId: number): Observable<KpiSnapshot[]> {
    return this.http.get<KpiSnapshot[]>(`${base}/business-analytics/snapshots`, {
      headers: this.orgHeaders(orgId),
    });
  }

  listAlerts(orgId: number): Observable<BusinessAlert[]> {
    return this.http.get<BusinessAlert[]>(`${base}/business-analytics/alerts`, {
      headers: this.orgHeaders(orgId),
    });
  }

  generateRecommendations(orgId: number): Observable<Recommendation[]> {
    return this.http.post<Recommendation[]>(`${base}/business-analytics/recommendations/generate`, null, {
      headers: this.orgHeaders(orgId),
    });
  }

  listQuality(orgId: number): Observable<unknown[]> {
    return this.http.get<unknown[]>(`${base}/business-analytics/quality`, {
      headers: this.orgHeaders(orgId),
    });
  }
}
