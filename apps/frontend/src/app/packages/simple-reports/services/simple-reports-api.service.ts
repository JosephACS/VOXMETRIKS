import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';

export interface SimpleReportColumn {
  key: string;
  label: string;
}

export interface SimpleReportFilter {
  key: string;
  label: string;
  kind: string;
  options: string[];
}

export interface SimpleReportCatalogItem {
  id: string;
  area: string;
  title: string;
  description: string;
  objective: string;
  access: string;
  org_scoped: boolean;
  implementation: string;
  pending_reason: string;
  columns: SimpleReportColumn[];
  filters: SimpleReportFilter[];
  business_module?: string;
  business_module_label?: string;
  business_process?: string;
  category?: string;
  decision?: string;
  data_classification?: string;
  monetary_classification?: string | null;
  route?: string;
  demo_backend_dependency?: string;
  report_type?: string;
}

export interface SimpleReportCatalogResponse {
  items: SimpleReportCatalogItem[];
  total: number;
  modules?: { id: string; label: string }[];
  categories?: string[];
}

export interface SimpleReportData {
  report_id: string;
  title: string;
  description: string;
  columns: SimpleReportColumn[];
  items: Record<string, unknown>[];
  page: number;
  page_size: number;
  total: number;
  implementation: string;
  empty_message: string;
  data_classification?: string;
  monetary_classification?: string | null;
  classification_note?: string | null;
}

@Injectable({ providedIn: 'root' })
export class SimpleReportsApiService {
  private readonly http = inject(HttpClient);
  private readonly orgCtx = inject(OrganizationContextService);
  private readonly base = `${environment.apiUrl}/reports/simple`;

  catalog(opts?: {
    area?: string;
    module?: string;
    category?: string;
    q?: string;
  }): Observable<SimpleReportCatalogResponse> {
    let params = new HttpParams();
    if (opts?.area) params = params.set('area', opts.area);
    if (opts?.module) params = params.set('module', opts.module);
    if (opts?.category) params = params.set('category', opts.category);
    if (opts?.q) params = params.set('q', opts.q);
    return this.http.get<SimpleReportCatalogResponse>(`${this.base}/catalog`, {
      params,
      headers: this.orgHeaders(),
    });
  }

  getData(
    reportId: string,
    opts: {
      page?: number;
      page_size?: number;
      search?: string;
      filters?: Record<string, string>;
    } = {},
  ): Observable<SimpleReportData> {
    let params = new HttpParams()
      .set('page', String(opts.page ?? 1))
      .set('page_size', String(opts.page_size ?? 25));
    if (opts.search) params = params.set('search', opts.search);
    if (opts.filters) {
      for (const [k, v] of Object.entries(opts.filters)) {
        if (v) params = params.set(k, v);
      }
    }
    return this.http.get<SimpleReportData>(`${this.base}/${reportId}/data`, {
      params,
      headers: this.orgHeaders(),
    });
  }

  private orgHeaders(): Record<string, string> {
    const orgId = this.orgCtx.organizationId();
    return orgId ? { 'X-Organization-Id': String(orgId) } : {};
  }
}
