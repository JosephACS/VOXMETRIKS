import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { SubscriptionsApiService } from './subscriptions-api.service';
import { environment } from '../../../../environments/environment';

const base = environment.apiUrl;

describe('SubscriptionsApiService (K4)', () => {
  let api: SubscriptionsApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        SubscriptionsApiService,
      ],
    });
    api = TestBed.inject(SubscriptionsApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  // ── Plans ──────────────────────────────────────────────────────────────────

  it('listPlans hits GET /plans with status param', () => {
    let result: unknown;
    api.listPlans({ status: 'active' }).subscribe((v) => (result = v));
    const req = http.expectOne((r) => r.url === `${base}/plans`);
    expect(req.request.method).toBe('GET');
    expect(req.request.params.get('status')).toBe('active');
    req.flush({ items: [], page: 1, limit: 25, total: 0 });
    expect((result as { total: number }).total).toBe(0);
  });

  it('getPlan hits GET /plans/:id', () => {
    let result: unknown;
    api.getPlan(42).subscribe((v) => (result = v));
    const req = http.expectOne(`${base}/plans/42`);
    expect(req.request.method).toBe('GET');
    req.flush({ id: 42, code: 'starter', display_name: 'Starter', status: 'active' });
    expect((result as { id: number }).id).toBe(42);
  });

  it('createPlan hits POST /plans', () => {
    api.createPlan({ code: 'test', display_name: 'Test' }).subscribe();
    const req = http.expectOne(`${base}/plans`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body['code']).toBe('test');
    req.flush({ id: 1, code: 'test', display_name: 'Test', status: 'draft' });
  });

  it('activatePlan hits POST /plans/:id/activate', () => {
    api.activatePlan(1).subscribe();
    const req = http.expectOne(`${base}/plans/1/activate`);
    expect(req.request.method).toBe('POST');
    req.flush({ id: 1, status: 'active' });
  });

  it('archivePlan hits POST /plans/:id/archive', () => {
    api.archivePlan(1).subscribe();
    const req = http.expectOne(`${base}/plans/1/archive`);
    expect(req.request.method).toBe('POST');
    req.flush({ id: 1, status: 'archived' });
  });

  // ── Plan prices ────────────────────────────────────────────────────────────

  it('listPlanPrices hits GET /plans/:id/prices', () => {
    api.listPlanPrices(5, true).subscribe();
    const req = http.expectOne((r) => r.url === `${base}/plans/5/prices`);
    expect(req.request.method).toBe('GET');
    expect(req.request.params.get('active_only')).toBe('true');
    req.flush([]);
  });

  it('setPlanPrice hits POST /plans/:id/prices', () => {
    api.setPlanPrice(5, { currency: 'USD', billing_period: 'monthly', amount: '29.99' }).subscribe();
    const req = http.expectOne(`${base}/plans/5/prices`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body['currency']).toBe('USD');
    req.flush({ id: 10, plan_id: 5, currency: 'USD', status: 'active' });
  });

  // ── Plan features ──────────────────────────────────────────────────────────

  it('listPlanFeatures hits GET /plans/:id/features', () => {
    api.listPlanFeatures(5).subscribe();
    const req = http.expectOne(`${base}/plans/5/features`);
    expect(req.request.method).toBe('GET');
    req.flush([]);
  });

  it('configurePlanFeature hits POST /plans/:id/features', () => {
    api.configurePlanFeature(5, { feature_code: 'api_calls', limit_value: 1000 }).subscribe();
    const req = http.expectOne(`${base}/plans/5/features`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body['feature_code']).toBe('api_calls');
    req.flush({ id: 1, plan_id: 5, feature_code: 'api_calls', limit_value: 1000, enabled: true });
  });

  // ── Addons ─────────────────────────────────────────────────────────────────

  it('listAddons hits GET /addons', () => {
    api.listAddons({ status: 'active' }).subscribe();
    const req = http.expectOne((r) => r.url === `${base}/addons`);
    expect(req.request.method).toBe('GET');
    req.flush({ items: [], page: 1, limit: 25, total: 0 });
  });

  it('createAddon hits POST /addons', () => {
    api.createAddon({ code: 'extra', display_name: 'Extra', feature_code: 'storage' }).subscribe();
    const req = http.expectOne(`${base}/addons`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body['code']).toBe('extra');
    req.flush({ id: 1, code: 'extra', display_name: 'Extra', status: 'active' });
  });

  // ── Subscriptions ──────────────────────────────────────────────────────────

  it('listSubscriptions sends X-Organization-Id header', () => {
    api.listSubscriptions(99).subscribe();
    const req = http.expectOne((r) => r.url === `${base}/subscriptions`);
    expect(req.request.headers.get('X-Organization-Id')).toBe('99');
    req.flush({ items: [], page: 1, limit: 25, total: 0 });
  });

  it('startTrial hits POST /subscriptions/trial with org header', () => {
    api.startTrial(99, {
      organization_id: 99,
      plan_id: 1,
      billing_currency: 'USD',
    }).subscribe();
    const req = http.expectOne(`${base}/subscriptions/trial`);
    expect(req.request.method).toBe('POST');
    expect(req.request.headers.get('X-Organization-Id')).toBe('99');
    expect(req.request.body['billing_currency']).toBe('USD');
    req.flush({ id: 1, status: 'trialing' });
  });

  it('cancelSubscription hits POST /subscriptions/:id/cancel', () => {
    api.cancelSubscription(99, 42, { mode: 'period_end' }).subscribe();
    const req = http.expectOne(`${base}/subscriptions/42/cancel`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body['mode']).toBe('period_end');
    req.flush({ id: 42, status: 'active', cancel_at_period_end: true });
  });

  it('reactivateSubscription hits POST /subscriptions/:id/reactivate', () => {
    api.reactivateSubscription(99, 42, {}).subscribe();
    const req = http.expectOne(`${base}/subscriptions/42/reactivate`);
    expect(req.request.method).toBe('POST');
    req.flush({ id: 42, status: 'active' });
  });

  it('listEntitlements hits GET /subscriptions/:id/entitlements', () => {
    api.listEntitlements(99, 42).subscribe();
    const req = http.expectOne(`${base}/subscriptions/42/entitlements`);
    expect(req.request.method).toBe('GET');
    expect(req.request.headers.get('X-Organization-Id')).toBe('99');
    req.flush([]);
  });

  it('listUsage hits GET /subscriptions/:id/usage', () => {
    api.listUsage(99, 42).subscribe();
    const req = http.expectOne((r) => r.url === `${base}/subscriptions/42/usage`);
    expect(req.request.method).toBe('GET');
    req.flush({ items: [], page: 1, limit: 50, total: 0 });
  });

  it('addAddon hits POST /subscriptions/:id/addons', () => {
    api.addAddon(99, 42, 7).subscribe();
    const req = http.expectOne(`${base}/subscriptions/42/addons`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body['addon_id']).toBe(7);
    req.flush({ id: 1, subscription_id: 42, addon_id: 7, status: 'active' });
  });

  it('removeAddon hits DELETE /subscriptions/:id/addons/:addonId', () => {
    api.removeAddon(99, 42, 7).subscribe();
    const req = http.expectOne(`${base}/subscriptions/42/addons/7`);
    expect(req.request.method).toBe('DELETE');
    req.flush({ id: 1, subscription_id: 42, addon_id: 7, status: 'removed' });
  });

  it('getAccessState hits GET /subscriptions/:id/access-state', () => {
    api.getAccessState(99, 42).subscribe();
    const req = http.expectOne(`${base}/subscriptions/42/access-state`);
    expect(req.request.method).toBe('GET');
    req.flush({ subscription_id: 42, access_state: 'full', reason: null, updated_at: '' });
  });

  // ── Org isolation proof ────────────────────────────────────────────────────

  it('different org ids produce different X-Organization-Id headers', () => {
    api.listSubscriptions(100).subscribe();
    const req1 = http.expectOne((r) => r.url === `${base}/subscriptions`);
    expect(req1.request.headers.get('X-Organization-Id')).toBe('100');
    req1.flush({ items: [], page: 1, limit: 25, total: 0 });
  });
});
