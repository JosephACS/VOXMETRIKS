import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { Router } from '@angular/router';
import { provideRouter } from '@angular/router';
import { environment } from '../../../../environments/environment';
import { CrmApiError, CrmApiService } from './crm-api.service';
import { CrmContextService } from './crm-context.service';
import { crmAccessGuard } from '../guards/crm.guards';
import { CRM_ROUTES } from '../crm.routes';
import { APP_ROUTES } from '../../../app.routes';
import { CrmDashboardPageComponent } from '../pages/crm-dashboard.page';
import { CrmProspectsListPageComponent } from '../pages/crm-prospects-list.page';
import { CrmAuditPageComponent } from '../pages/crm-audit.page';
import { CrmAccessDeniedPageComponent } from '../pages/crm-access-denied.page';

const base = environment.apiUrl;

// ── CrmApiService ──────────────────────────────────────────────────────────────

describe('CrmApiService (J4)', () => {
  let api: CrmApiService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), CrmApiService],
    });
    api = TestBed.inject(CrmApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('getPermissions hits /crm/permissions', () => {
    api.getPermissions().subscribe();
    const req = http.expectOne(`${base}/crm/permissions`);
    expect(req.request.method).toBe('GET');
    req.flush({ permissions: ['crm.prospect.view'], roles: ['sales_agent'] });
  });

  it('listProspects builds correct URL with pagination', () => {
    let got: unknown;
    api.listProspects(2, 10).subscribe((v) => (got = v));
    const req = http.expectOne((r) => r.url === `${base}/crm/prospects`);
    expect(req.request.params.get('page')).toBe('2');
    expect(req.request.params.get('limit')).toBe('10');
    req.flush({ items: [], page: 2, limit: 10, total: 0 });
    expect((got as { total: number }).total).toBe(0);
  });

  it('listProspects appends status filter when provided', () => {
    api.listProspects(1, 25, 'qualified').subscribe();
    const req = http.expectOne((r) => r.url === `${base}/crm/prospects`);
    expect(req.request.params.get('status')).toBe('qualified');
    req.flush({ items: [], page: 1, limit: 25, total: 0 });
  });

  it('createProspect posts to /crm/prospects', () => {
    api.createProspect({ display_name: 'Acme Corp', email: 'acme@example.com' }).subscribe();
    const req = http.expectOne(`${base}/crm/prospects`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.display_name).toBe('Acme Corp');
    req.flush({
      id: 1, display_name: 'Acme Corp', status: 'new',
      created_at: '', updated_at: '',
    });
  });

  it('updateProspect patches /crm/prospects/:id', () => {
    api.updateProspect(5, { display_name: 'Updated Name' }).subscribe();
    const req = http.expectOne(`${base}/crm/prospects/5`);
    expect(req.request.method).toBe('PATCH');
    req.flush({ id: 5, display_name: 'Updated Name', status: 'new', created_at: '', updated_at: '' });
  });

  it('transitionProspectStatus posts to /crm/prospects/:id/status', () => {
    api.transitionProspectStatus(3, 'qualified').subscribe();
    const req = http.expectOne(`${base}/crm/prospects/3/status`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.status).toBe('qualified');
    req.flush({ id: 3, display_name: 'X', status: 'qualified', created_at: '', updated_at: '' });
  });

  it('listOpportunities builds URL with optional stage', () => {
    api.listOpportunities(1, 50, 'proposal').subscribe();
    const req = http.expectOne((r) => r.url === `${base}/crm/opportunities`);
    expect(req.request.params.get('stage')).toBe('proposal');
    req.flush({ items: [], page: 1, limit: 50, total: 0 });
  });

  it('advanceOpportunityStage posts to /crm/opportunities/:id/stage', () => {
    api.advanceOpportunityStage(7, 'negotiation', 'budget approved').subscribe();
    const req = http.expectOne(`${base}/crm/opportunities/7/stage`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.stage).toBe('negotiation');
    expect(req.request.body.reason).toBe('budget approved');
    req.flush({ id: 7, prospect_id: 1, name: 'Test', stage: 'negotiation', created_at: '', updated_at: '' });
  });

  it('closeOpportunity posts to /crm/opportunities/:id/close', () => {
    api.closeOpportunity(9, 'lost', 'lost', 'price too high').subscribe();
    const req = http.expectOne(`${base}/crm/opportunities/9/close`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.outcome).toBe('lost');
    req.flush({ id: 9, prospect_id: 1, name: 'Test', stage: 'lost', created_at: '', updated_at: '' });
  });

  it('listQuotationVersions hits /crm/quotations/:id/versions', () => {
    api.listQuotationVersions(4).subscribe();
    const req = http.expectOne(`${base}/crm/quotations/4/versions`);
    expect(req.request.method).toBe('GET');
    req.flush([]);
  });

  it('sendQuotationVersion posts to /crm/quotation-versions/:id/send', () => {
    api.sendQuotationVersion(12).subscribe();
    const req = http.expectOne(`${base}/crm/quotation-versions/12/send`);
    expect(req.request.method).toBe('POST');
    req.flush({ id: 12, quotation_id: 1, version_no: 1, status: 'sent', created_at: '' });
  });

  it('approveRequest posts to /crm/approvals/:id/approve', () => {
    api.approveRequest(2, 'looks good').subscribe();
    const req = http.expectOne(`${base}/crm/approvals/2/approve`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.review_note).toBe('looks good');
    req.flush({ id: 2, object_type: 'quotation_version', object_id: 1, status: 'approved', created_at: '', updated_at: '' });
  });

  it('rejectRequest posts to /crm/approvals/:id/reject', () => {
    api.rejectRequest(3, 'too high').subscribe();
    const req = http.expectOne(`${base}/crm/approvals/3/reject`);
    expect(req.request.body.review_note).toBe('too high');
    req.flush({ id: 3, object_type: 'quotation_version', object_id: 2, status: 'rejected', created_at: '', updated_at: '' });
  });

  it('listCrmAudit hits /crm/audit with pagination', () => {
    api.listCrmAudit(1, 50).subscribe();
    const req = http.expectOne((r) => r.url === `${base}/crm/audit`);
    expect(req.request.params.get('limit')).toBe('50');
    req.flush({ items: [], page: 1, limit: 50, total: 0 });
  });

  it('surfaces 403 as typed CrmApiError', () => {
    let err: CrmApiError | undefined;
    api.getPermissions().subscribe({ error: (e) => (err = e) });
    const req = http.expectOne(`${base}/crm/permissions`);
    req.flush(
      { status: 'error', message: 'Forbidden', details: { code: 'forbidden' } },
      { status: 403, statusText: 'Forbidden' },
    );
    expect(err).toBeInstanceOf(CrmApiError);
    expect(err!.status).toBe(403);
    expect(err!.code).toBe('forbidden');
  });

  it('getContract hits /crm/contracts/:id', () => {
    api.getContract(99).subscribe();
    const req = http.expectOne(`${base}/crm/contracts/99`);
    expect(req.request.method).toBe('GET');
    req.flush({
      id: 99, quotation_version_id: 1, opportunity_id: 2, status: 'draft',
      created_at: '', updated_at: '',
    });
  });

  it('expireContract posts to /crm/contracts/:id/expire', () => {
    api.expireContract(11).subscribe();
    const req = http.expectOne(`${base}/crm/contracts/11/expire`);
    expect(req.request.method).toBe('POST');
    req.flush({ id: 11, quotation_version_id: 1, opportunity_id: 2, status: 'expired', created_at: '', updated_at: '' });
  });
});

// ── CrmContextService ──────────────────────────────────────────────────────────

describe('CrmContextService (J4)', () => {
  let ctx: CrmContextService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        CrmApiService,
        CrmContextService,
      ],
    });
    ctx = TestBed.inject(CrmContextService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('starts in idle state with no permissions', () => {
    expect(ctx.status()).toBe('idle');
    expect(ctx.permissions()).toEqual([]);
    expect(ctx.hasCrmAccess()).toBe(false);
  });

  it('bootstraps and sets CRM permissions correctly', async () => {
    const p = ctx.bootstrap();
    const req = http.expectOne(`${base}/crm/permissions`);
    req.flush({ permissions: ['crm.prospect.view', 'crm.prospect.create'], roles: ['sales_agent'] });
    await p;
    expect(ctx.status()).toBe('ready');
    expect(ctx.hasCrmAccess()).toBe(true);
    expect(ctx.hasPermission('crm.prospect.view')).toBe(true);
    expect(ctx.hasPermission('quotation.approve')).toBe(false);
  });

  it('sets ready state with empty permissions when user has no CRM roles', async () => {
    const p = ctx.bootstrap();
    const req = http.expectOne(`${base}/crm/permissions`);
    req.flush({ permissions: [], roles: [] });
    await p;
    expect(ctx.status()).toBe('ready');
    expect(ctx.hasCrmAccess()).toBe(false);
    expect(ctx.hasPermission('crm.prospect.view')).toBe(false);
  });

  it('treats 403 response as no-access (not error)', async () => {
    const p = ctx.bootstrap();
    const req = http.expectOne(`${base}/crm/permissions`);
    req.flush({ message: 'Forbidden' }, { status: 403, statusText: 'Forbidden' });
    await p;
    expect(ctx.status()).toBe('ready');
    expect(ctx.hasCrmAccess()).toBe(false);
  });

  it('sets error state on non-403 server error', async () => {
    const p = ctx.bootstrap();
    const req = http.expectOne(`${base}/crm/permissions`);
    req.flush({ message: 'Server Error' }, { status: 500, statusText: 'Internal Server Error' });
    await p;
    expect(ctx.status()).toBe('error');
    expect(ctx.error()).toBeTruthy();
  });

  it('clearState resets to idle', async () => {
    const p = ctx.bootstrap();
    http.expectOne(`${base}/crm/permissions`).flush({
      permissions: ['crm.prospect.view'],
      roles: ['sales_agent'],
    });
    await p;
    expect(ctx.hasCrmAccess()).toBe(true);
    ctx.clearState();
    expect(ctx.status()).toBe('idle');
    expect(ctx.hasCrmAccess()).toBe(false);
  });

  it('does not use localStorage for permissions', () => {
    localStorage.setItem('fake_crm_perms', JSON.stringify(['crm.audit.view']));
    expect(ctx.hasPermission('crm.audit.view')).toBe(false);
    localStorage.removeItem('fake_crm_perms');
  });
});

// ── Guard ──────────────────────────────────────────────────────────────────────

describe('crmAccessGuard (J4)', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([
          { path: 'crm/dashboard', component: CrmDashboardPageComponent, canActivate: [crmAccessGuard] },
          { path: 'crm/access-denied', component: CrmAccessDeniedPageComponent },
        ]),
        CrmApiService,
        CrmContextService,
      ],
    });
    http = TestBed.inject(HttpTestingController);
    TestBed.inject(CrmContextService).clearState();
  });

  afterEach(() => http.verify());

  it('guard is a function (canActivateFn)', () => {
    expect(typeof crmAccessGuard).toBe('function');
  });

  it('allows navigation when user has CRM access', async () => {
    const ctx = TestBed.inject(CrmContextService);
    const boot = ctx.bootstrap();
    const req = http.expectOne(`${base}/crm/permissions`);
    req.flush({ permissions: ['crm.prospect.view'], roles: ['sales_agent'] });
    await boot;
    expect(ctx.hasCrmAccess()).toBe(true);

    const result = await TestBed.runInInjectionContext(() => crmAccessGuard({} as never, {} as never));
    expect(result).toBe(true);
  });

  it('redirects to /crm/access-denied when user has no CRM access', async () => {
    const ctx = TestBed.inject(CrmContextService);
    const boot = ctx.bootstrap();
    const req = http.expectOne(`${base}/crm/permissions`);
    req.flush({ permissions: [], roles: [] });
    await boot;
    expect(ctx.hasCrmAccess()).toBe(false);

    const result = await TestBed.runInInjectionContext(() => crmAccessGuard({} as never, {} as never));
    expect(String(result)).toContain('access-denied');
  });
});

// ── CRM Routes registration ────────────────────────────────────────────────────

describe('CRM Routes registration (J4)', () => {
  it('CRM_ROUTES exports required paths', () => {
    const paths = new Set(CRM_ROUTES.map((r) => r.path));
    const required = [
      'crm/dashboard',
      'crm/prospects',
      'crm/prospects/:id',
      'crm/opportunities',
      'crm/opportunities/:id',
      'crm/approvals',
      'crm/audit',
      'crm/access-denied',
      'crm/contracts/:id',
      'crm/conversions/:id',
      'crm/quotations/:id',
    ];
    for (const path of required) {
      expect(paths.has(path), `Expected CRM_ROUTES to include '${path}'`).toBe(true);
    }
  });

  it('CRM_ROUTES all have loadComponent', () => {
    const withLoader = CRM_ROUTES.filter(
      (r) => r.path !== 'crm' && r.path !== 'crm/access-denied',
    );
    expect(withLoader.every((r) => typeof r.loadComponent === 'function')).toBe(true);
  });

  it('APP_ROUTES includes CRM paths', () => {
    const layout = APP_ROUTES.find((r) => r.path === '' && r.children);
    const children = layout?.children ?? [];
    const paths = new Set(children.map((c) => c.path));
    expect(paths.has('crm/dashboard')).toBe(true);
    expect(paths.has('crm/prospects')).toBe(true);
    expect(paths.has('crm/access-denied')).toBe(true);
  });
});

// ── Page component creation ────────────────────────────────────────────────────

describe('CRM page components (J4)', () => {
  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        CrmApiService,
        CrmContextService,
      ],
    });
  });

  afterEach(() => TestBed.inject(HttpTestingController).verify());

  it('CrmDashboardPageComponent can be created', () => {
    const fixture = TestBed.createComponent(CrmDashboardPageComponent);
    const component = fixture.componentInstance;
    expect(component).toBeTruthy();
    expect(component.loading()).toBe(true);
    // Flush pending requests from ngOnInit
    const http = TestBed.inject(HttpTestingController);
    http.match(`${base}/crm/prospects`).forEach((r) => r.flush({ items: [], page: 1, limit: 1, total: 0 }));
    http.match(`${base}/crm/opportunities`).forEach((r) => r.flush({ items: [], page: 1, limit: 1, total: 0 }));
    http.match(`${base}/crm/activities`).forEach((r) => r.flush({ items: [], page: 1, limit: 1, total: 0 }));
    http.match(`${base}/crm/approvals`).forEach((r) => r.flush({ items: [], page: 1, limit: 1, total: 0 }));
  });

  it('CrmProspectsListPageComponent can be created', () => {
    const fixture = TestBed.createComponent(CrmProspectsListPageComponent);
    expect(fixture.componentInstance).toBeTruthy();
    const http = TestBed.inject(HttpTestingController);
    http.match(`${base}/crm/prospects`).forEach((r) => r.flush({ items: [], page: 1, limit: 25, total: 0 }));
  });

  it('CrmAuditPageComponent can be created', () => {
    const fixture = TestBed.createComponent(CrmAuditPageComponent);
    expect(fixture.componentInstance).toBeTruthy();
    const http = TestBed.inject(HttpTestingController);
    http.match(`${base}/crm/audit`).forEach((r) => r.flush({ items: [], page: 1, limit: 50, total: 0 }));
  });

  it('CrmAccessDeniedPageComponent can be created', () => {
    const fixture = TestBed.createComponent(CrmAccessDeniedPageComponent);
    expect(fixture.componentInstance).toBeTruthy();
  });
});
