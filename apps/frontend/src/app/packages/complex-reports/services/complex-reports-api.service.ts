import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';

export interface ComplexCatalogItem {
  id: string;
  area: string;
  title: string;
  question: string;
  description: string;
  calculation: string;
  chart_type: string;
  access: string;
  available: boolean;
  unavailable_reason: string;
  business_module?: string;
  business_module_label?: string;
  business_process?: string;
  category?: string;
  decision?: string;
  data_classification?: string;
  monetary_classification?: string | null;
  route?: string;
  report_type?: string;
}

export interface ComplexCatalogResponse {
  items: ComplexCatalogItem[];
  total: number;
  modules?: { id: string; label: string }[];
  categories?: string[];
}

export interface ComplexReportData {
  report_id: string;
  title: string;
  question: string;
  calculation: string;
  chart_type: string;
  available: boolean;
  unavailable_reason: string;
  period_start: string;
  period_end_exclusive: string;
  updated_at: string;
  includes_synthetic_events: boolean;
  data_classification?: string;
  monetary_classification?: string | null;
  classification_note?: string | null;
  summary: Record<string, number | null>;
  series: { label: string; value: number | null }[];
  rows: Record<string, unknown>[];
  columns: { key: string; label: string }[];
}

@Injectable({ providedIn: 'root' })
export class ComplexReportsApiService {
  private readonly http = inject(HttpClient);
  private readonly orgCtx = inject(OrganizationContextService);
  private readonly base = `${environment.apiUrl}/reports/complex`;

  catalog(opts?: { module?: string; category?: string; q?: string }): Observable<ComplexCatalogResponse> {
    let params = new HttpParams();
    if (opts?.module) params = params.set('module', opts.module);
    if (opts?.category) params = params.set('category', opts.category);
    if (opts?.q) params = params.set('q', opts.q);
    return this.http.get<ComplexCatalogResponse>(`${this.base}/catalog`, {
      params,
      headers: this.orgHeaders(),
    });
  }

  data(
    reportId: string,
    opts: { from?: string; to?: string; limit?: number } = {},
  ): Observable<ComplexReportData> {
    let params = new HttpParams();
    if (opts.from) params = params.set('from', opts.from);
    if (opts.to) params = params.set('to', opts.to);
    if (opts.limit) params = params.set('limit', String(opts.limit));
    return this.http.get<ComplexReportData>(`${this.base}/${reportId}/data`, {
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
