import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../../environments/environment';
import {
  Addon,
  AccessStateInfo,
  Paginated,
  Plan,
  PlanFeature,
  PlanPrice,
  Subscription,
  SubscriptionAddon,
  SubscriptionChange,
  SubscriptionEntitlement,
  UsageRecord,
} from '../models/subscriptions.models';

@Injectable({ providedIn: 'root' })
export class SubscriptionsApiService {
  private readonly http = inject(HttpClient);
  private readonly base = environment.apiUrl;

  // ── Plans ──────────────────────────────────────────────────────────────────

  listPlans(params?: { status?: string; page?: number; limit?: number }): Observable<Paginated<Plan>> {
    let query = new HttpParams();
    if (params?.status) query = query.set('status', params.status);
    if (params?.page) query = query.set('page', String(params.page));
    if (params?.limit) query = query.set('limit', String(params.limit));
    return this.http.get<Paginated<Plan>>(`${this.base}/plans`, { params: query });
  }

  getPlan(planId: number): Observable<Plan> {
    return this.http.get<Plan>(`${this.base}/plans/${planId}`);
  }

  createPlan(body: {
    code: string;
    display_name: string;
    description?: string;
    trial_days_default?: number;
    sort_order?: number;
  }): Observable<Plan> {
    return this.http.post<Plan>(`${this.base}/plans`, body);
  }

  updatePlan(planId: number, body: Partial<Plan>): Observable<Plan> {
    return this.http.patch<Plan>(`${this.base}/plans/${planId}`, body);
  }

  activatePlan(planId: number): Observable<Plan> {
    return this.http.post<Plan>(`${this.base}/plans/${planId}/activate`, {});
  }

  archivePlan(planId: number): Observable<Plan> {
    return this.http.post<Plan>(`${this.base}/plans/${planId}/archive`, {});
  }

  listPlanPrices(planId: number, activeOnly = true): Observable<PlanPrice[]> {
    const params = new HttpParams().set('active_only', String(activeOnly));
    return this.http.get<PlanPrice[]>(`${this.base}/plans/${planId}/prices`, { params });
  }

  setPlanPrice(planId: number, body: { currency: string; billing_period: string; amount: string }): Observable<PlanPrice> {
    return this.http.post<PlanPrice>(`${this.base}/plans/${planId}/prices`, body);
  }

  listPlanFeatures(planId: number): Observable<PlanFeature[]> {
    return this.http.get<PlanFeature[]>(`${this.base}/plans/${planId}/features`);
  }

  configurePlanFeature(planId: number, body: { feature_code: string; limit_value?: number; enabled?: boolean }): Observable<PlanFeature> {
    return this.http.post<PlanFeature>(`${this.base}/plans/${planId}/features`, body);
  }

  // ── Addons ─────────────────────────────────────────────────────────────────

  listAddons(params?: { status?: string; page?: number; limit?: number }): Observable<Paginated<Addon>> {
    let query = new HttpParams();
    if (params?.status) query = query.set('status', params.status);
    if (params?.page) query = query.set('page', String(params.page));
    if (params?.limit) query = query.set('limit', String(params.limit));
    return this.http.get<Paginated<Addon>>(`${this.base}/addons`, { params: query });
  }

  getAddon(addonId: number): Observable<Addon> {
    return this.http.get<Addon>(`${this.base}/addons/${addonId}`);
  }

  createAddon(body: {
    code: string;
    display_name: string;
    description?: string;
    feature_code?: string;
    amount?: string;
    currency?: string;
    billing_period?: string;
  }): Observable<Addon> {
    return this.http.post<Addon>(`${this.base}/addons`, body);
  }

  // ── Subscriptions ──────────────────────────────────────────────────────────

  private orgHeaders(organizationId: number): HttpHeaders {
    return new HttpHeaders({ 'X-Organization-Id': String(organizationId) });
  }

  listSubscriptions(organizationId: number, params?: { status?: string; page?: number; limit?: number }): Observable<Paginated<Subscription>> {
    let query = new HttpParams();
    if (params?.status) query = query.set('status', params.status);
    if (params?.page) query = query.set('page', String(params.page));
    if (params?.limit) query = query.set('limit', String(params.limit));
    return this.http.get<Paginated<Subscription>>(`${this.base}/subscriptions`, {
      headers: this.orgHeaders(organizationId),
      params: query,
    });
  }

  getSubscription(organizationId: number, subscriptionId: number): Observable<Subscription> {
    return this.http.get<Subscription>(`${this.base}/subscriptions/${subscriptionId}`, {
      headers: this.orgHeaders(organizationId),
    });
  }

  createSubscription(organizationId: number, body: {
    organization_id: number;
    plan_id: number;
    plan_price_id: number;
    billing_currency: string;
  }): Observable<Subscription> {
    return this.http.post<Subscription>(`${this.base}/subscriptions`, body, {
      headers: this.orgHeaders(organizationId),
    });
  }

  startTrial(organizationId: number, body: {
    organization_id: number;
    plan_id: number;
    billing_currency: string;
    plan_price_id?: number;
    trial_days?: number;
  }): Observable<Subscription> {
    return this.http.post<Subscription>(`${this.base}/subscriptions/trial`, body, {
      headers: this.orgHeaders(organizationId),
    });
  }

  cancelSubscription(organizationId: number, subscriptionId: number, body: { mode: string; reason?: string }): Observable<Subscription> {
    return this.http.post<Subscription>(`${this.base}/subscriptions/${subscriptionId}/cancel`, body, {
      headers: this.orgHeaders(organizationId),
    });
  }

  reactivateSubscription(organizationId: number, subscriptionId: number, body: { reason?: string }): Observable<Subscription> {
    return this.http.post<Subscription>(`${this.base}/subscriptions/${subscriptionId}/reactivate`, body, {
      headers: this.orgHeaders(organizationId),
    });
  }

  scheduleChange(organizationId: number, subscriptionId: number, body: {
    to_plan_id: number;
    to_price_id?: number;
    scheduled_for?: string;
    reason?: string;
  }): Observable<SubscriptionChange> {
    return this.http.post<SubscriptionChange>(`${this.base}/subscriptions/${subscriptionId}/change`, body, {
      headers: this.orgHeaders(organizationId),
    });
  }

  listChanges(organizationId: number, subscriptionId: number): Observable<Paginated<SubscriptionChange>> {
    return this.http.get<Paginated<SubscriptionChange>>(`${this.base}/subscriptions/${subscriptionId}/changes`, {
      headers: this.orgHeaders(organizationId),
    });
  }

  listEntitlements(organizationId: number, subscriptionId: number): Observable<SubscriptionEntitlement[]> {
    return this.http.get<SubscriptionEntitlement[]>(`${this.base}/subscriptions/${subscriptionId}/entitlements`, {
      headers: this.orgHeaders(organizationId),
    });
  }

  listUsage(organizationId: number, subscriptionId: number, params?: { feature_code?: string; page?: number; limit?: number }): Observable<Paginated<UsageRecord>> {
    let query = new HttpParams();
    if (params?.feature_code) query = query.set('feature_code', params.feature_code);
    if (params?.page) query = query.set('page', String(params.page));
    if (params?.limit) query = query.set('limit', String(params.limit));
    return this.http.get<Paginated<UsageRecord>>(`${this.base}/subscriptions/${subscriptionId}/usage`, {
      headers: this.orgHeaders(organizationId),
      params: query,
    });
  }

  recordUsage(organizationId: number, subscriptionId: number, body: {
    feature_code: string;
    quantity: string;
    period_start: string;
    period_end: string;
    idempotency_key?: string;
  }): Observable<UsageRecord> {
    return this.http.post<UsageRecord>(`${this.base}/subscriptions/${subscriptionId}/usage`, body, {
      headers: this.orgHeaders(organizationId),
    });
  }

  listSubscriptionAddons(organizationId: number, subscriptionId: number): Observable<SubscriptionAddon[]> {
    return this.http.get<SubscriptionAddon[]>(`${this.base}/subscriptions/${subscriptionId}/addons`, {
      headers: this.orgHeaders(organizationId),
    });
  }

  addAddon(organizationId: number, subscriptionId: number, addonId: number): Observable<SubscriptionAddon> {
    return this.http.post<SubscriptionAddon>(`${this.base}/subscriptions/${subscriptionId}/addons`, { addon_id: addonId }, {
      headers: this.orgHeaders(organizationId),
    });
  }

  removeAddon(organizationId: number, subscriptionId: number, addonId: number): Observable<SubscriptionAddon> {
    return this.http.delete<SubscriptionAddon>(`${this.base}/subscriptions/${subscriptionId}/addons/${addonId}`, {
      headers: this.orgHeaders(organizationId),
    });
  }

  getAccessState(organizationId: number, subscriptionId: number): Observable<AccessStateInfo> {
    return this.http.get<AccessStateInfo>(`${this.base}/subscriptions/${subscriptionId}/access-state`, {
      headers: this.orgHeaders(organizationId),
    });
  }
}
