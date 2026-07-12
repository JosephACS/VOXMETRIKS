import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { BillingApiService } from './billing-api.service';
import { environment } from '../../../../environments/environment';

const base = environment.apiUrl;
const orgId = 1;

describe('BillingApiService (L4)', () => {
  let api: BillingApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.resetTestingModule();
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        BillingApiService,
      ],
    });
    api = TestBed.inject(BillingApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('getProfile hits GET /billing/profile with org header', () => {
    let result: unknown;
    api.getProfile(orgId).subscribe((r) => (result = r));
    const req = http.expectOne(`${base}/billing/profile`);
    expect(req.request.method).toBe('GET');
    expect(req.request.headers.get('X-Organization-Id')).toBe('1');
    req.flush({ id: 1, default_currency: 'USD', status: 'active' });
    expect((result as { default_currency: string }).default_currency).toBe('USD');
  });

  it('createProfile hits POST /billing/profile', () => {
    let result: unknown;
    api.createProfile(orgId, { default_currency: 'EUR' }).subscribe((r) => (result = r));
    const req = http.expectOne(`${base}/billing/profile`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.default_currency).toBe('EUR');
    req.flush({ id: 2, default_currency: 'EUR', status: 'active' });
    expect((result as { id: number }).id).toBe(2);
  });

  it('listInvoices hits GET /billing/invoices with status param', () => {
    let result: unknown;
    api.listInvoices(orgId, { status: 'issued' }).subscribe((r) => (result = r));
    const req = http.expectOne((r) => r.url === `${base}/billing/invoices`);
    expect(req.request.method).toBe('GET');
    expect(req.request.params.get('status')).toBe('issued');
    req.flush({ items: [], total: 0, page: 1, page_size: 25 });
    expect((result as { total: number }).total).toBe(0);
  });

  it('createInvoice hits POST /billing/invoices', () => {
    let result: unknown;
    api.createInvoice(orgId, { billing_profile_id: 1 }).subscribe((r) => (result = r));
    const req = http.expectOne(`${base}/billing/invoices`);
    expect(req.request.method).toBe('POST');
    req.flush({ id: 10, status: 'draft', invoice_number: 'INV-000010' });
    expect((result as { status: string }).status).toBe('draft');
  });

  it('issueInvoice hits POST /billing/invoices/10/issue', () => {
    api.issueInvoice(orgId, 10).subscribe();
    const req = http.expectOne(`${base}/billing/invoices/10/issue`);
    expect(req.request.method).toBe('POST');
    req.flush({ id: 10, status: 'issued' });
  });

  it('createPaymentAttempt hits POST /billing/payment-attempts', () => {
    let result: unknown;
    const body = { invoice_id: 10, provider_code: 'academic_mock', idempotency_key: 'k1', amount: 100, currency: 'USD' };
    api.createPaymentAttempt(orgId, body).subscribe((r) => (result = r));
    const req = http.expectOne(`${base}/billing/payment-attempts`);
    expect(req.request.method).toBe('POST');
    req.flush({ id: 1, is_mock: true, status: 'created', ...body });
    expect((result as { is_mock: boolean }).is_mock).toBe(true);
  });

  it('confirmMockAttempt hits POST /billing/payment-attempts/1/confirm', () => {
    api.confirmMockAttempt(orgId, 1).subscribe();
    const req = http.expectOne(`${base}/billing/payment-attempts/1/confirm`);
    expect(req.request.method).toBe('POST');
    req.flush({ id: 1, status: 'succeeded', is_mock: true });
  });

  it('createManualTransfer hits POST /billing/manual-transfer', () => {
    let result: unknown;
    const body = { invoice_id: 10, amount: 500, currency: 'USD', notes: 'Wire ref #001' };
    api.createManualTransfer(orgId, body).subscribe((r) => (result = r));
    const req = http.expectOne(`${base}/billing/manual-transfer`);
    expect(req.request.method).toBe('POST');
    req.flush({ id: 5, status: 'recorded', amount: 500 });
    expect((result as { status: string }).status).toBe('recorded');
  });

  it('getLedger hits GET /billing/ledger with org header', () => {
    api.getLedger(orgId, { entry_type: 'payment_received' }).subscribe();
    const req = http.expectOne((r) => r.url === `${base}/billing/ledger`);
    expect(req.request.headers.get('X-Organization-Id')).toBe('1');
    expect(req.request.params.get('entry_type')).toBe('payment_received');
    req.flush({ items: [], total: 0, page: 1, page_size: 50 });
  });

  it('createRefund hits POST /billing/refunds', () => {
    const body = { payment_id: 5, amount: 50, reason: 'Customer request' };
    api.createRefund(orgId, body).subscribe();
    const req = http.expectOne(`${base}/billing/refunds`);
    expect(req.request.method).toBe('POST');
    req.flush({ id: 1, status: 'processed' });
  });

  it('createCreditNote and applyCreditNote', () => {
    api.createCreditNote(orgId, { invoice_id: 10, amount: 30 }).subscribe();
    const req1 = http.expectOne(`${base}/billing/credit-notes`);
    req1.flush({ id: 1, status: 'issued' });

    api.applyCreditNote(orgId, 1).subscribe();
    const req2 = http.expectOne(`${base}/billing/credit-notes/1/apply`);
    expect(req2.request.method).toBe('POST');
    req2.flush({ id: 1, status: 'applied' });
  });
});
