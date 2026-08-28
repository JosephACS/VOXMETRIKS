import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter, ActivatedRoute } from '@angular/router';
import { vi } from 'vitest';
import { I18nService } from '../../../core/services/i18n.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { environment } from '../../../../environments/environment';
import { CheckoutJourneyPage } from './checkout-journey.page';
import { CheckoutSession } from '../models/checkout.models';

const base = environment.apiUrl;

function readySession(overrides: Partial<CheckoutSession> = {}): CheckoutSession {
  return {
    id: 42,
    scope_type: 'personal',
    scope_id: 1,
    actor_user_id: 1,
    plan_code: 'premium_individual',
    plan_id: 2,
    plan_price_id: 3,
    billing_period: 'monthly',
    amount: 9.99,
    currency: 'USD',
    status: 'ready',
    next_action: 'confirm',
    subscription_id: null,
    invoice_id: 9,
    payment_attempt_id: null,
    payment_method_id: 5,
    idempotency_key: 'create-key',
    failure_code: null,
    created_at: '',
    updated_at: '',
    expires_at: null,
    completed_at: null,
    is_simulated: true,
    payment_method: { brand: 'visa', last4: '4242' },
    ...overrides,
  };
}

describe('CheckoutJourneyPage', () => {
  let page: CheckoutJourneyPage;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      imports: [CheckoutJourneyPage],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              data: { checkoutScope: 'personal' },
              queryParamMap: {
                get: (k: string) =>
                  ({ plan_code: 'premium_individual', billing_period: 'monthly' } as Record<
                    string,
                    string
                  >)[k] ?? null,
              },
            },
          },
        },
        {
          provide: OrganizationContextService,
          useValue: {
            organizationId: () => null,
            bootstrap: vi.fn().mockResolvedValue(undefined),
          },
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
    const fixture = TestBed.createComponent(CheckoutJourneyPage);
    page = fixture.componentInstance;
    // Avoid full template CD; exercise logic after ngOnInit create.
    page.ngOnInit();
    const create = http.expectOne(`${base}/personal/checkout-sessions`);
    create.flush(
      readySession({
        status: 'awaiting_method',
        next_action: 'attach_payment_method',
        payment_method_id: null,
        payment_method: null,
      }),
    );
  });

  afterEach(() => {
    page.ngOnDestroy();
    http.verify();
  });

  it('clears card fields after payment submit mock', () => {
    page.dispatch({ type: 'GO_STEP', step: 'payment' });
    page.pan = '4242424242424242';
    page.cvv = '123';
    page.expMonth = 12;
    page.expYear = new Date().getFullYear() + 2;

    page.submitPayment();

    expect(page.pan).toBe('');
    expect(page.cvv).toBe('');

    const attach = http.expectOne(`${base}/personal/checkout-sessions/42/payment-method`);
    expect(attach.request.body.simulation_token).toBe('sim_tok_succeeded');
    expect(attach.request.body).not.toHaveProperty('pan');
    expect(attach.request.body).not.toHaveProperty('cvv');
    expect(JSON.stringify(attach.request.body)).not.toContain('4242424242424242');
    attach.flush(readySession());

    const confirm = http.expectOne(`${base}/personal/checkout-sessions/42/confirm`);
    confirm.flush(readySession({ status: 'succeeded', next_action: 'view_result' }));

    expect(page.pan).toBe('');
    expect(page.cvv).toBe('');
  });

  it('fills a safe demonstration card without real payment data', () => {
    page.selectBrand('visa');
    page.fillDemoCard();

    expect(page.pan).toBe('4242424242424242');
    expect(page.cvv).toBe('123');
    expect(page.expMonth).toBe(12);
    expect(page.expYear).toBeGreaterThan(new Date().getFullYear());
    expect(page.planLabel('premium_individual')).toBe('Premium Individual');
    expect(page.periodLabel('monthly')).toBe('Mensual');
  });
});
