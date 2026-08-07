import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';

export interface WorkpanelMetric {
  id: string;
  label: string;
  value: number | null;
  unit: string;
  period: string;
  previous_value: number | null;
  variation_pct: number | null;
  explanation: string;
  detail_path: string;
  available: boolean;
  status: string;
  scope?: string;
  display_caption?: string | null;
}

export interface WorkpanelSection {
  id: string;
  title: string;
  description: string;
  badge: string;
  scope: string;
  metric_ids: string[];
  quick_links?: { label: string; path: string }[];
}

export interface WorkpanelResponse {
  title: string;
  subtitle: string;
  period: string;
  period_start: string;
  period_end_exclusive: string;
  updated_at: string;
  analytics_updated_at: string | null;
  includes_synthetic_events: boolean;
  data_classification?: string;
  monetary_classification?: string;
  classification_note?: string | null;
  available_periods?: string[];
  default_period?: string | null;
  period_sources?: Record<string, string[]>;
  sections?: WorkpanelSection[];
  metrics: WorkpanelMetric[];
  pendings: { id: string; label: string; value: number; detail_path: string; severity: string }[];
  links: { label: string; path: string }[];
}

@Injectable({ providedIn: 'root' })
export class WorkpanelApiService {
  private readonly http = inject(HttpClient);
  private readonly orgCtx = inject(OrganizationContextService);
  private readonly base = `${environment.apiUrl}/workpanel`;

  get(period?: string): Observable<WorkpanelResponse> {
    let params = new HttpParams();
    if (period) params = params.set('period', period);
    return this.http.get<WorkpanelResponse>(this.base, {
      params,
      headers: this.orgHeaders(),
    });
  }

  private orgHeaders(): HttpHeaders {
    const orgId = this.orgCtx.organizationId?.();
    let headers = new HttpHeaders();
    if (orgId != null) headers = headers.set('X-Organization-Id', String(orgId));
    return headers;
  }
}
