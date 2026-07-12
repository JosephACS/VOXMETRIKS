import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  Campaign,
  CampaignApproval,
  CampaignBudget,
  CampaignExpense,
  CampaignRoiSnapshot,
  PaginatedCampaigns,
} from '../models/campaigns.models';

const base = environment.apiUrl;

@Injectable({ providedIn: 'root' })
export class CampaignsApiService {
  private http = inject(HttpClient);

  private orgHeaders(orgId: number): Record<string, string> {
    return { 'X-Organization-Id': String(orgId) };
  }

  list(orgId: number, params?: { status?: string; page?: number; page_size?: number }): Observable<PaginatedCampaigns> {
    let httpParams = new HttpParams();
    if (params?.status) httpParams = httpParams.set('status', params.status);
    if (params?.page) httpParams = httpParams.set('page', String(params.page));
    if (params?.page_size) httpParams = httpParams.set('page_size', String(params.page_size));
    return this.http.get<PaginatedCampaigns>(`${base}/campaigns`, {
      headers: this.orgHeaders(orgId),
      params: httpParams,
    });
  }

  create(orgId: number, body: { name: string; market?: string; segment?: string }): Observable<Campaign> {
    return this.http.post<Campaign>(`${base}/campaigns`, body, { headers: this.orgHeaders(orgId) });
  }

  get(orgId: number, campaignId: number): Observable<Campaign> {
    return this.http.get<Campaign>(`${base}/campaigns/${campaignId}`, { headers: this.orgHeaders(orgId) });
  }

  getBudget(orgId: number, campaignId: number): Observable<CampaignBudget | null> {
    return this.http.get<CampaignBudget | null>(`${base}/campaigns/${campaignId}/budget`, {
      headers: this.orgHeaders(orgId),
    });
  }

  setBudget(orgId: number, campaignId: number, body: { amount: number; currency: string }): Observable<CampaignBudget> {
    return this.http.post<CampaignBudget>(`${base}/campaigns/${campaignId}/budget`, body, {
      headers: this.orgHeaders(orgId),
    });
  }

  listExpenses(orgId: number, campaignId: number): Observable<CampaignExpense[]> {
    return this.http.get<CampaignExpense[]>(`${base}/campaigns/${campaignId}/expenses`, {
      headers: this.orgHeaders(orgId),
    });
  }

  addExpense(
    orgId: number,
    campaignId: number,
    body: { amount: number; currency: string; category: string; expense_date: string },
  ): Observable<CampaignExpense> {
    return this.http.post<CampaignExpense>(`${base}/campaigns/${campaignId}/expenses`, body, {
      headers: this.orgHeaders(orgId),
    });
  }

  listApprovals(orgId: number, campaignId: number): Observable<CampaignApproval[]> {
    return this.http.get<CampaignApproval[]>(`${base}/campaigns/${campaignId}/approvals`, {
      headers: this.orgHeaders(orgId),
    });
  }

  requestApproval(
    orgId: number,
    campaignId: number,
    body: { approval_type: string },
  ): Observable<CampaignApproval> {
    return this.http.post<CampaignApproval>(`${base}/campaigns/${campaignId}/approvals`, body, {
      headers: this.orgHeaders(orgId),
    });
  }

  decideApproval(
    orgId: number,
    approvalId: number,
    body: { approved: boolean; reason?: string },
  ): Observable<CampaignApproval> {
    return this.http.post<CampaignApproval>(`${base}/campaigns/approvals/${approvalId}/decide`, body, {
      headers: this.orgHeaders(orgId),
    });
  }

  computeRoi(orgId: number, campaignId: number): Observable<CampaignRoiSnapshot> {
    return this.http.post<CampaignRoiSnapshot>(`${base}/campaigns/${campaignId}/roi/compute`, null, {
      headers: this.orgHeaders(orgId),
    });
  }

  getRoi(orgId: number, campaignId: number): Observable<CampaignRoiSnapshot | null> {
    return this.http.get<CampaignRoiSnapshot | null>(`${base}/campaigns/${campaignId}/roi`, {
      headers: this.orgHeaders(orgId),
    });
  }
}
