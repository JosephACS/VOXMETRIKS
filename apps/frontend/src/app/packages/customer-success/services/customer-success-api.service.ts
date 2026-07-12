import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

const base = environment.apiUrl;

@Injectable({ providedIn: 'root' })
export class CustomerSuccessApiService {
  private http = inject(HttpClient);

  private orgHeaders(orgId: number) {
    return { 'X-Organization-Id': String(orgId) };
  }

  dashboard(orgId: number): Observable<unknown> {
    return this.http.get(`${base}/customer-success/dashboard`, { headers: this.orgHeaders(orgId) });
  }

  calculateHealth(orgId: number): Observable<unknown> {
    return this.http.post(`${base}/customer-success/health/calculate`, null, {
      headers: this.orgHeaders(orgId),
    });
  }

  createOnboarding(orgId: number): Observable<unknown> {
    return this.http.post(`${base}/customer-success/onboarding`, null, {
      headers: this.orgHeaders(orgId),
    });
  }

  evaluateRenewal(orgId: number): Observable<unknown> {
    return this.http.post(`${base}/customer-success/renewal/evaluate`, null, {
      headers: this.orgHeaders(orgId),
    });
  }

  listCases(orgId: number): Observable<unknown[]> {
    return this.http.get<unknown[]>(`${base}/support/cases`, { headers: this.orgHeaders(orgId) });
  }

  createCase(orgId: number, subject: string) {
    return this.http.post(`${base}/support/cases`, { subject }, { headers: this.orgHeaders(orgId) });
  }

  getCase(orgId: number, id: number) {
    return this.http.get(`${base}/support/cases/${id}`, { headers: this.orgHeaders(orgId) });
  }

  addMessage(orgId: number, id: number, body: string) {
    return this.http.post(`${base}/support/cases/${id}/messages`, { body }, { headers: this.orgHeaders(orgId) });
  }

  addInternalNote(orgId: number, id: number, body: string) {
    return this.http.post(`${base}/support/cases/${id}/internal-notes`, { body }, { headers: this.orgHeaders(orgId) });
  }

  listMessages(orgId: number, id: number, includeInternal = false) {
    return this.http.get<unknown[]>(`${base}/support/cases/${id}/messages`, {
      headers: this.orgHeaders(orgId),
      params: { include_internal: String(includeInternal) },
    });
  }

  resolve(orgId: number, id: number) {
    return this.http.post(`${base}/support/cases/${id}/resolve`, null, { headers: this.orgHeaders(orgId) });
  }

  close(orgId: number, id: number) {
    return this.http.post(`${base}/support/cases/${id}/close`, null, { headers: this.orgHeaders(orgId) });
  }
}
