import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  ConsentDefinition,
  ConsentRecord,
  DataRequest,
  PaginatedAudit,
  PaginatedDataRequests,
  PaginatedTerms,
  TermsVersion,
} from '../models/compliance.models';

const base = environment.apiUrl;

@Injectable({ providedIn: 'root' })
export class ComplianceApiService {
  private http = inject(HttpClient);

  private orgHeaders(orgId: number): HttpHeaders {
    return new HttpHeaders({ 'X-Organization-Id': String(orgId) });
  }

  listTerms(orgId: number): Observable<PaginatedTerms> {
    return this.http.get<PaginatedTerms>(`${base}/compliance/terms`, { headers: this.orgHeaders(orgId) });
  }

  createTerms(orgId: number, body: { version_code: string; title: string; content_summary: string; effective_at: string }): Observable<TermsVersion> {
    return this.http.post<TermsVersion>(`${base}/compliance/terms`, body, { headers: this.orgHeaders(orgId) });
  }

  listConsentDefinitions(orgId: number): Observable<{ items: ConsentDefinition[]; total: number }> {
    return this.http.get<{ items: ConsentDefinition[]; total: number }>(`${base}/compliance/consent/definitions`, { headers: this.orgHeaders(orgId) });
  }

  myConsentRecords(orgId?: number): Observable<ConsentRecord[]> {
    const headers = orgId ? this.orgHeaders(orgId) : undefined;
    return this.http.get<ConsentRecord[]>(`${base}/compliance/consent/records/me`, { headers });
  }

  submitDsr(orgId: number, body: { request_type: string; reason?: string }): Observable<DataRequest> {
    return this.http.post<DataRequest>(`${base}/compliance/dsr`, body, { headers: this.orgHeaders(orgId) });
  }

  listDsr(orgId: number): Observable<PaginatedDataRequests> {
    return this.http.get<PaginatedDataRequests>(`${base}/compliance/dsr`, { headers: this.orgHeaders(orgId) });
  }

  searchAudit(orgId: number, params?: { action?: string; source?: string }): Observable<PaginatedAudit> {
    let httpParams = new HttpParams();
    if (params?.action) httpParams = httpParams.set('action', params.action);
    if (params?.source) httpParams = httpParams.set('source', params.source);
    return this.http.get<PaginatedAudit>(`${base}/compliance/audit/search`, { headers: this.orgHeaders(orgId), params: httpParams });
  }
}
