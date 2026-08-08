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
  household_role?: string | null;
  household_plan_code?: string | null;
  household_plan_name?: string | null;
  household_owner_display_name?: string | null;
  can_manage_billing?: boolean;
}

export interface HouseholdMemberCard {
  user_id: number;
  role: string;
  status: string;
  joined_at?: string | null;
  display_name: string;
  initials: string;
  avatar_hue: number;
  is_me?: boolean;
  login_hint?: string | null;
  email?: string | null;
  username?: string | null;
}

export interface HouseholdInvitation {
  id: number;
  email: string;
  status: string;
  expires_at?: string | null;
  created_at?: string | null;
  display_name?: string | null;
}

export interface HouseholdSummary {
  id: number;
  owner_user_id: number;
  owner_display_name: string;
  plan_code: string;
  plan_name: string;
  max_members: number;
  status: string;
  my_role: string;
  seats_used: number;
  seats_available: number;
  current_period_end?: string | null;
  members: HouseholdMemberCard[];
  pending_invitations: HouseholdInvitation[];
}

export interface ProfileSelectorResponse {
  household_id?: number;
  plan_name?: string;
  plan_code?: string | null;
  plan_active?: boolean;
  my_role?: string;
  profiles: Array<{
    profile_key?: string;
    user_id: number;
    display_name: string;
    initials: string;
    avatar_hue: number;
    avatar_url?: string | null;
    avatar_preset?: string | null;
    role: string;
    is_me?: boolean;
    pin_enabled?: boolean;
  }>;
  show_selector?: boolean;
  household?: null;
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

  getHousehold(): Observable<HouseholdSummary | { household: null }> {
    return this.http.get<HouseholdSummary | { household: null }>(`${this.base}/household`);
  }

  getProfiles(): Observable<ProfileSelectorResponse> {
    return this.http.get<ProfileSelectorResponse>(`${this.base}/household/profiles`);
  }

  prepareProfileSwitch(targetUserId: number): Observable<{
    display_name?: string;
    requires_manual_reauth?: boolean;
  }> {
    return this.http.post<{ display_name?: string; requires_manual_reauth?: boolean }>(
      `${this.base}/household/profiles/${targetUserId}/prepare-switch`,
      {},
    );
  }

  invite(email: string, display_name?: string): Observable<Record<string, unknown>> {
    return this.http.post<Record<string, unknown>>(`${this.base}/household/invitations`, {
      email,
      display_name: display_name || undefined,
    });
  }

  cancelInvite(id: number): Observable<{ ok: boolean }> {
    return this.http.post<{ ok: boolean }>(
      `${this.base}/household/invitations/${id}/cancel`,
      {},
    );
  }

  resendInvite(id: number): Observable<Record<string, unknown>> {
    return this.http.post<Record<string, unknown>>(
      `${this.base}/household/invitations/${id}/resend`,
      {},
    );
  }

  acceptInvite(token: string): Observable<Record<string, unknown>> {
    return this.http.post<Record<string, unknown>>(`${this.base}/household/accept`, { token });
  }

  rejectInvite(token: string): Observable<{ ok: boolean; status: string }> {
    return this.http.post<{ ok: boolean; status: string }>(`${this.base}/household/reject`, {
      token,
    });
  }

  leaveHousehold(): Observable<{ ok: boolean }> {
    return this.http.post<{ ok: boolean }>(`${this.base}/household/leave`, {});
  }

  removeMember(userId: number): Observable<Record<string, unknown>> {
    return this.http.post<Record<string, unknown>>(
      `${this.base}/household/members/${userId}/remove`,
      {},
    );
  }
}
