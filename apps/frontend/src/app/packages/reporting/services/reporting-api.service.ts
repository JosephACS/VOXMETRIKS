import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of, throwError } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';
import { environment } from '../../../../environments/environment';
import {
  BusinessDecision,
  DecisionAction,
  DecisionFollowUp,
  ExecutiveReport,
  Paginated,
  ReportDefinition,
} from '../models/reporting.models';
import { CatalogCacheService } from '../../../core/services/catalog-cache.service';

const base = environment.apiUrl;

@Injectable({ providedIn: 'root' })
export class ReportingApiService {
  private http = inject(HttpClient);
  private cache = inject(CatalogCacheService);

  private orgHeaders(orgId: number) {
    return { 'X-Organization-Id': String(orgId) };
  }

  listDefinitions(orgId: number): Observable<Paginated<ReportDefinition>> {
    return this.cachedGet(`report-definitions:${orgId}`, () => this.http.get<Paginated<ReportDefinition>>(`${base}/reports/definitions`, {
      headers: this.orgHeaders(orgId),
    }));
  }

  createDefinition(orgId: number, body: { code: string; title: string; description?: string }) {
    return this.http.post<ReportDefinition>(`${base}/reports/definitions`, body, {
      headers: this.orgHeaders(orgId),
    });
  }

  requestGeneration(orgId: number, definitionId: number) {
    return this.http.post<{ id: number }>(
      `${base}/reports/generations`,
      { definition_id: definitionId },
      { headers: this.orgHeaders(orgId) },
    );
  }

  generate(orgId: number, generationId: number) {
    return this.http.post<{ executive_report: ExecutiveReport }>(
      `${base}/reports/generations/${generationId}/generate`,
      null,
      { headers: this.orgHeaders(orgId) },
    );
  }

  listExecutive(orgId: number): Observable<Paginated<ExecutiveReport>> {
    return this.cachedGet(`executive-reports:${orgId}`, () => this.http.get<Paginated<ExecutiveReport>>(`${base}/reports/executive`, {
      headers: this.orgHeaders(orgId),
    }));
  }

  getExecutive(orgId: number, id: number) {
    return this.cachedGet(`executive-report:${orgId}:${id}`, () => this.http.get<ExecutiveReport>(`${base}/reports/executive/${id}`, {
      headers: this.orgHeaders(orgId),
    }), 30_000);
  }

  approve(orgId: number, id: number) {
    return this.http.post<ExecutiveReport>(`${base}/reports/executive/${id}/approve`, {}, {
      headers: this.orgHeaders(orgId),
    });
  }

  publish(orgId: number, id: number) {
    return this.http.post<ExecutiveReport>(`${base}/reports/executive/${id}/publish`, null, {
      headers: this.orgHeaders(orgId),
    });
  }

  archive(orgId: number, id: number) {
    return this.http.post<ExecutiveReport>(`${base}/reports/executive/${id}/archive`, null, {
      headers: this.orgHeaders(orgId),
    });
  }

  exportCsv(orgId: number, id: number): Observable<Blob> {
    return this.http.get(`${base}/reports/executive/${id}/export`, {
      headers: this.orgHeaders(orgId),
      responseType: 'blob',
    });
  }

  listDecisions(orgId: number): Observable<Paginated<BusinessDecision>> {
    return this.cachedGet(`business-decisions:${orgId}`, () => this.http.get<Paginated<BusinessDecision>>(`${base}/business-decisions`, {
      headers: this.orgHeaders(orgId),
    }));
  }

  createDecision(orgId: number, body: { title: string; proposal: string; executive_report_id?: number }) {
    return this.http.post<BusinessDecision>(`${base}/business-decisions`, body, {
      headers: this.orgHeaders(orgId),
    });
  }

  getDecision(orgId: number, id: number) {
    return this.cachedGet(`business-decision:${orgId}:${id}`, () => this.http.get<BusinessDecision>(`${base}/business-decisions/${id}`, {
      headers: this.orgHeaders(orgId),
    }), 30_000);
  }

  approveDecision(orgId: number, id: number) {
    return this.http.post<BusinessDecision>(`${base}/business-decisions/${id}/approve`, null, {
      headers: this.orgHeaders(orgId),
    });
  }

  cancelDecision(orgId: number, id: number, reason?: string) {
    return this.http.post<BusinessDecision>(
      `${base}/business-decisions/${id}/cancel`,
      { reason: reason || null },
      { headers: this.orgHeaders(orgId) },
    );
  }

  addAction(orgId: number, id: number, title: string) {
    return this.http.post<DecisionAction>(`${base}/business-decisions/${id}/actions`, { title }, {
      headers: this.orgHeaders(orgId),
    });
  }

  listActions(orgId: number, id: number) {
    return this.cachedGet(`decision-actions:${orgId}:${id}`, () => this.http.get<DecisionAction[]>(`${base}/business-decisions/${id}/actions`, {
      headers: this.orgHeaders(orgId),
    }));
  }

  completeDecision(orgId: number, id: number) {
    return this.http.post<BusinessDecision>(`${base}/business-decisions/${id}/complete`, null, {
      headers: this.orgHeaders(orgId),
    });
  }

  listFollowUps(orgId: number, id: number) {
    return this.cachedGet(`decision-followups:${orgId}:${id}`, () => this.http.get<DecisionFollowUp[]>(`${base}/business-decisions/${id}/follow-ups`, {
      headers: this.orgHeaders(orgId),
    }));
  }

  addFollowUp(orgId: number, id: number, note: string) {
    return this.http.post<DecisionFollowUp>(`${base}/business-decisions/${id}/follow-ups`, { note }, {
      headers: this.orgHeaders(orgId),
    });
  }

  private cachedGet<T>(key: string, request: () => Observable<T>, ttlMs = 60_000): Observable<T> {
    const cached = this.cache.get<T>(key, ttlMs);
    if (cached !== null) return of(cached);
    return request().pipe(
      tap((value) => this.cache.set(key, value, ttlMs)),
      catchError((error) => {
        this.cache.invalidate(key);
        return throwError(() => error);
      }),
    );
  }
}
