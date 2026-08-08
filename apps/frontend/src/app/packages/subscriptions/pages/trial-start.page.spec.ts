import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter, Router } from '@angular/router';
import { vi } from 'vitest';
import { TrialStartPageComponent } from './trial-start.page';
import { SubscriptionsApiService } from '../services/subscriptions-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { environment } from '../../../../environments/environment';

const base = environment.apiUrl;

describe('TrialStartPageComponent', () => {
  let page: TrialStartPageComponent;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      imports: [TrialStartPageComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        SubscriptionsApiService,
        {
          provide: OrganizationContextService,
          useValue: { activeOrganization: () => ({ id: 7 }) },
        },
        {
          provide: I18nService,
          useValue: {
            lang: () => 'es',
            t: (k: string) => k,
          },
        },
      ],
    });
    http = TestBed.inject(HttpTestingController);
    const router = TestBed.inject(Router);
    vi.spyOn(router, 'navigate').mockResolvedValue(true as never);

    // Avoid template CD (enterprise header required inputs); exercise logic via ngOnInit.
    const fixture = TestBed.createComponent(TrialStartPageComponent);
    page = fixture.componentInstance;
    page.ngOnInit();

    http.expectOne((r) => r.url.startsWith(`${base}/plans`)).flush({
      items: [
        {
          id: 11,
          code: 'pro',
          display_name: 'Pro',
          description: null,
          status: 'active',
          trial_days_default: 14,
          sort_order: 1,
          created_at: '',
          updated_at: '',
        },
      ],
      page: 1,
      limit: 50,
      total: 1,
    });
    http.expectOne((r) => r.url.startsWith(`${base}/plans/11/prices`)).flush([
      {
        id: 101,
        plan_id: 11,
        currency: 'USD',
        billing_period: 'monthly',
        amount: '10.00',
        status: 'active',
        created_at: '',
        updated_at: '',
      },
      {
        id: 102,
        plan_id: 11,
        currency: 'EUR',
        billing_period: 'annual',
        amount: '100.00',
        status: 'active',
        created_at: '',
        updated_at: '',
      },
    ]);
    http.expectOne(`${base}/plans/11/features`).flush([]);
  });

  afterEach(() => http.verify());

  it('loads plans, selects plan/price, and posts startTrial with matching currency', () => {
    expect(page.cards().length).toBe(1);
    const card = page.cards()[0];
    page.selectPlan(card);
    expect(page.selectedPlanId()).toBe(11);
    expect(page.form.value.planPriceId).toBe(101);
    expect(page.form.value.billingCurrency).toBe('USD');
    expect(page.currencyLocked()).toBe(true);

    page.form.patchValue({ planPriceId: 102 });
    expect(page.form.value.billingCurrency).toBe('EUR');
    expect(page.currencyLocked()).toBe(true);

    page.form.patchValue({ planPriceId: null });
    expect(page.currencyLocked()).toBe(false);
    page.form.patchValue({ billingCurrency: 'GBP', planPriceId: 102 });
    expect(page.form.value.billingCurrency).toBe('EUR');

    page.onSubmit();
    const req = http.expectOne(`${base}/subscriptions/trial`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({
      organization_id: 7,
      plan_id: 11,
      plan_price_id: 102,
      billing_currency: 'EUR',
    });
    req.flush({ id: 1, status: 'trialing' });
  });
});
