import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { RefundsPage } from './refunds.page';
import { BillingApiService } from '../services/billing-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { environment } from '../../../../environments/environment';

describe('RefundsPage idempotency', () => {
  let page: RefundsPage;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      imports: [RefundsPage],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        BillingApiService,
        {
          provide: OrganizationContextService,
          useValue: { organizationId: () => 7 },
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
    const fixture = TestBed.createComponent(RefundsPage);
    page = fixture.componentInstance;
    // Flush the initial list load from ngOnInit.
    fixture.detectChanges();
    const refundsReq = http.expectOne(`${environment.apiUrl}/billing/refunds`);
    refundsReq.flush({ items: [], total: 0, page: 1, page_size: 25 });
    const paymentsReq = http.expectOne(
      (r) => r.url.startsWith(`${environment.apiUrl}/billing/payments`),
    );
    paymentsReq.flush({ items: [], total: 0, page: 1, page_size: 100 });
  });

  afterEach(() => http.verify());

  it('reuses the same idempotency key while retrying a failed submit', () => {
    page.showForm = true;
    page.form.setValue({ payment_id: 9, amount: 10, reason: 'test' });

    page.submit();
    const first = http.expectOne(`${environment.apiUrl}/billing/refunds`);
    const key1 = first.request.body.idempotency_key as string;
    expect(key1).toBeTruthy();
    expect(first.request.headers.get('Idempotency-Key')).toBe(key1);
    first.flush({ message: 'fail' }, { status: 500, statusText: 'err' });
    expect(page.submitting).toBe(false);

    page.submit();
    const second = http.expectOne(`${environment.apiUrl}/billing/refunds`);
    expect(second.request.body.idempotency_key).toBe(key1);
    second.flush({
      id: 1,
      payment_id: 9,
      amount: 10,
      currency: 'USD',
      status: 'processed',
      idempotency_key: key1,
    });
    const reload = http.expectOne(`${environment.apiUrl}/billing/refunds`);
    reload.flush({ items: [], total: 0, page: 1, page_size: 25 });
  });

  it('generates a new key after a successful refund', () => {
    page.showForm = true;
    page.form.setValue({ payment_id: 9, amount: 5, reason: 'a' });
    const k1 = page.ensureIdempotencyKey();
    page.submit();
    const req = http.expectOne(`${environment.apiUrl}/billing/refunds`);
    expect(req.request.body.idempotency_key).toBe(k1);
    req.flush({
      id: 2,
      payment_id: 9,
      amount: 5,
      currency: 'USD',
      status: 'processed',
      idempotency_key: k1,
    });
    http.expectOne(`${environment.apiUrl}/billing/refunds`).flush({ items: [], total: 0, page: 1, page_size: 25 });

    page.toggleForm(true);
    http
      .expectOne((r) => r.url.startsWith(`${environment.apiUrl}/billing/payments`))
      .flush({ items: [], total: 0, page: 1, page_size: 100 });
    const k2 = page.ensureIdempotencyKey();
    expect(k2).not.toBe(k1);
  });

  it('blocks double submit while a request is in flight', () => {
    page.showForm = true;
    page.form.setValue({ payment_id: 9, amount: 8, reason: '' });
    page.submit();
    expect(page.submitting).toBe(true);
    page.submit(); // ignored
    const reqs = http.match(`${environment.apiUrl}/billing/refunds`);
    expect(reqs.length).toBe(1);
    reqs[0].flush({
      id: 3,
      payment_id: 9,
      amount: 8,
      currency: 'USD',
      status: 'processed',
      idempotency_key: reqs[0].request.body.idempotency_key,
    });
    http.expectOne(`${environment.apiUrl}/billing/refunds`).flush({ items: [], total: 0, page: 1, page_size: 25 });
  });
});
