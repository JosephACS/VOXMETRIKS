import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  PayoutBatch,
  RoyaltyMetrics,
  RoyaltyPool,
  RoyaltySettlement,
  RoyaltyStatement,
} from '../models/royalties.models';

const BASE = environment.apiUrl;

@Injectable({ providedIn: 'root' })
export class RoyaltiesApiService {
  private http = inject(HttpClient);

  private orgHeaders(orgId: number): HttpHeaders {
    return new HttpHeaders({ 'X-Organization-Id': String(orgId) });
  }

  // ── Metrics / dashboard ─────────────────────────────────────────────────

  getMetrics(orgId: number): Observable<RoyaltyMetrics> {
    return this.http.get<RoyaltyMetrics>(`${BASE}/royalties/metrics`, {
      headers: this.orgHeaders(orgId),
    });
  }

  // ── Pools ───────────────────────────────────────────────────────────────

  listPools(
    orgId: number,
    params?: { limit?: number; offset?: number },
  ): Observable<RoyaltyPool[]> {
    let p = new HttpParams();
    if (params?.limit != null) p = p.set('limit', String(params.limit));
    if (params?.offset != null) p = p.set('offset', String(params.offset));
    return this.http.get<RoyaltyPool[]>(`${BASE}/royalties/pools`, {
      headers: this.orgHeaders(orgId),
      params: p,
    });
  }

  getPool(orgId: number, poolId: number): Observable<RoyaltyPool> {
    return this.http.get<RoyaltyPool>(`${BASE}/royalties/pools/${poolId}`, {
      headers: this.orgHeaders(orgId),
    });
  }

  createPool(orgId: number, body: object): Observable<RoyaltyPool> {
    return this.http.post<RoyaltyPool>(`${BASE}/royalties/pools`, body, {
      headers: this.orgHeaders(orgId),
    });
  }

  approvePool(orgId: number, poolId: number): Observable<RoyaltyPool> {
    return this.http.post<RoyaltyPool>(
      `${BASE}/royalties/pools/${poolId}/approve`,
      {},
      { headers: this.orgHeaders(orgId) },
    );
  }

  settleProRata(orgId: number, poolId: number, body: object): Observable<RoyaltySettlement> {
    return this.http.post<RoyaltySettlement>(
      `${BASE}/royalties/pools/${poolId}/settle/pro-rata`,
      body,
      { headers: this.orgHeaders(orgId) },
    );
  }

  // ── Statements ──────────────────────────────────────────────────────────

  listStatements(
    orgId: number,
    params?: { settlement_run_id?: number; limit?: number; offset?: number },
  ): Observable<RoyaltyStatement[]> {
    let p = new HttpParams();
    if (params?.settlement_run_id != null) {
      p = p.set('settlement_run_id', String(params.settlement_run_id));
    }
    if (params?.limit != null) p = p.set('limit', String(params.limit));
    if (params?.offset != null) p = p.set('offset', String(params.offset));
    return this.http.get<RoyaltyStatement[]>(`${BASE}/royalties/statements`, {
      headers: this.orgHeaders(orgId),
      params: p,
    });
  }

  // ── Settlements ─────────────────────────────────────────────────────────

  getSettlement(orgId: number, settlementId: number): Observable<RoyaltySettlement> {
    return this.http.get<RoyaltySettlement>(`${BASE}/settlements/${settlementId}`, {
      headers: this.orgHeaders(orgId),
    });
  }

  contractSplits(orgId: number, settlementId: number): Observable<RoyaltySettlement> {
    return this.http.post<RoyaltySettlement>(
      `${BASE}/settlements/${settlementId}/contract-splits`,
      {},
      { headers: this.orgHeaders(orgId) },
    );
  }

  generateStatements(orgId: number, settlementId: number): Observable<RoyaltyStatement[]> {
    return this.http.post<RoyaltyStatement[]>(
      `${BASE}/settlements/${settlementId}/statements`,
      {},
      { headers: this.orgHeaders(orgId) },
    );
  }

  submitSettlement(orgId: number, settlementId: number): Observable<RoyaltySettlement> {
    return this.http.post<RoyaltySettlement>(
      `${BASE}/settlements/${settlementId}/submit`,
      {},
      { headers: this.orgHeaders(orgId) },
    );
  }

  approveSettlement(orgId: number, settlementId: number): Observable<RoyaltySettlement> {
    return this.http.post<RoyaltySettlement>(
      `${BASE}/settlements/${settlementId}/approve`,
      {},
      { headers: this.orgHeaders(orgId) },
    );
  }

  rejectSettlement(
    orgId: number,
    settlementId: number,
    reason = 'rejected',
  ): Observable<RoyaltySettlement> {
    return this.http.post<RoyaltySettlement>(
      `${BASE}/settlements/${settlementId}/reject`,
      { reason },
      { headers: this.orgHeaders(orgId) },
    );
  }

  finalizeSettlement(orgId: number, settlementId: number): Observable<RoyaltySettlement> {
    return this.http.post<RoyaltySettlement>(
      `${BASE}/settlements/${settlementId}/finalize`,
      {},
      { headers: this.orgHeaders(orgId) },
    );
  }

  createPayoutBatch(orgId: number, settlementId: number, body: object): Observable<PayoutBatch> {
    return this.http.post<PayoutBatch>(
      `${BASE}/settlements/${settlementId}/payout-batches`,
      body,
      { headers: this.orgHeaders(orgId) },
    );
  }

  // ── Payouts (simulated) ─────────────────────────────────────────────────

  getPayoutBatch(orgId: number, batchId: number): Observable<PayoutBatch> {
    return this.http.get<PayoutBatch>(`${BASE}/payouts/batches/${batchId}`, {
      headers: this.orgHeaders(orgId),
    });
  }

  simulatePayouts(
    orgId: number,
    batchId: number,
    scenario = 'succeed',
  ): Observable<PayoutBatch> {
    return this.http.post<PayoutBatch>(
      `${BASE}/payouts/batches/${batchId}/simulate`,
      { scenario },
      { headers: this.orgHeaders(orgId) },
    );
  }

  retryPayout(
    orgId: number,
    instructionId: number,
    scenario = 'succeed',
  ): Observable<PayoutBatch> {
    return this.http.post<PayoutBatch>(
      `${BASE}/payouts/instructions/${instructionId}/retry`,
      { scenario },
      { headers: this.orgHeaders(orgId) },
    );
  }

  reversePayout(orgId: number, batchId: number): Observable<PayoutBatch> {
    return this.http.post<PayoutBatch>(
      `${BASE}/payouts/batches/${batchId}/reverse`,
      {},
      { headers: this.orgHeaders(orgId) },
    );
  }
}
