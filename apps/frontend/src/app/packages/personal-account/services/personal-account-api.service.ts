import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';

export interface PersonalPlan {
  id: number;
  code: string;
  display_name: string;
  description: string;
  max_members: number;
  is_free: boolean;
  sort_order: number;
  prices: { id: number; billing_period: string; amount: number; currency: string }[];
  features: { feature_code: string; limit_value: number | null; enabled: boolean }[];
}

export interface PersonalSubscription {
  id: number;
  plan_code: string;
  plan_name: string;
  status: string;
  is_free: boolean;
  billing_period?: string | null;
  amount?: number;
  current_period_end?: string | null;
  cancel_at_period_end?: boolean;
  access_state?: string;
  owner_type: string;
  household_id?: number | null;
  max_members?: number;
}

@Injectable({ providedIn: 'root' })
export class PersonalAccountApiService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/personal`;

  listPlans(): Observable<{ items: PersonalPlan[]; owner_type: string }> {
    return this.http.get<{ items: PersonalPlan[]; owner_type: string }>(`${this.base}/plans`);
  }

  getSubscription(): Observable<PersonalSubscription> {
    return this.http.get<PersonalSubscription>(`${this.base}/subscription`);
  }

  getEntitlements(): Observable<Record<string, unknown>> {
    return this.http.get<Record<string, unknown>>(`${this.base}/entitlements`);
  }

  checkout(plan_code: string, billing_period: string): Observable<{
    attempt_id: number;
    invoice_id: number;
    amount: number;
    plan_code: string;
  }> {
    return this.http.post<{
      attempt_id: number;
      invoice_id: number;
      amount: number;
      plan_code: string;
    }>(`${this.base}/checkout`, { plan_code, billing_period });
  }

  simulatePayment(attemptId: number, scenario: string): Observable<{ status: string }> {
    return this.http.post<{ status: string }>(
      `${this.base}/payment-attempts/${attemptId}/simulate`,
      { scenario },
    );
  }

  cancel(at_period_end = true): Observable<PersonalSubscription> {
    return this.http.post<PersonalSubscription>(`${this.base}/subscription/cancel`, {
      at_period_end,
    });
  }

  listInvoices(): Observable<{ items: unknown[] }> {
    return this.http.get<{ items: unknown[] }>(`${this.base}/invoices`);
  }

  getHousehold(): Observable<Record<string, unknown>> {
    return this.http.get<Record<string, unknown>>(`${this.base}/household`);
  }

  invite(email: string): Observable<Record<string, unknown>> {
    return this.http.post<Record<string, unknown>>(`${this.base}/household/invitations`, {
      email,
    });
  }

  cancelInvite(id: number): Observable<{ ok: boolean }> {
    return this.http.post<{ ok: boolean }>(
      `${this.base}/household/invitations/${id}/cancel`,
      {},
    );
  }

  acceptInvite(token: string): Observable<Record<string, unknown>> {
    return this.http.post<Record<string, unknown>>(`${this.base}/household/accept`, { token });
  }

  removeMember(userId: number): Observable<Record<string, unknown>> {
    return this.http.post<Record<string, unknown>>(
      `${this.base}/household/members/${userId}/remove`,
      {},
    );
  }
}
