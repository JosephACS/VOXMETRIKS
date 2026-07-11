import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../../../../environments/environment';
import {
  OrganizationsApiError,
  OrganizationsApiService,
} from './organizations-api.service';
import { OrganizationContextService } from './organization-context.service';
import { ORGANIZATIONS_ROUTES } from '../organizations.routes';
import { APP_ROUTES } from '../../../app.routes';

describe('OrganizationsApiService (I4)', () => {
  let api: OrganizationsApiService;
  let http: HttpTestingController;
  const base = environment.apiUrl;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), OrganizationsApiService],
    });
    api = TestBed.inject(OrganizationsApiService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('lists organizations', () => {
    let got: unknown;
    api.listMine().subscribe((v) => (got = v));
    const req = http.expectOne(`${base}/organizations`);
    expect(req.request.method).toBe('GET');
    req.flush([{ id: 1, display_name: 'Acme', slug: 'acme', organization_type: 'label', timezone: 'UTC', default_currency: 'USD', status: 'active', created_by: 1, created_at: '', updated_at: '' }]);
    expect((got as { id: number }[])[0].id).toBe(1);
  });

  it('creates organization and surfaces slug conflict as typed error', () => {
    let err: OrganizationsApiError | undefined;
    api.create({ display_name: 'X', slug: 'taken' }).subscribe({
      error: (e) => (err = e),
    });
    const req = http.expectOne(`${base}/organizations`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.activate).toBeUndefined();
    req.flush(
      { status: 'error', message: 'Slug taken', details: { code: 'conflict' } },
      { status: 409, statusText: 'Conflict' },
    );
    expect(err).toBeInstanceOf(OrganizationsApiError);
    expect(err!.status).toBe(409);
    expect(err!.code).toBe('conflict');
  });

  it('posts create with activate flag when provided', () => {
    api.create({ display_name: 'Y', slug: 'y', activate: true }).subscribe();
    const req = http.expectOne(`${base}/organizations`);
    expect(req.request.body.activate).toBe(true);
    req.flush({
      organization: { id: 2, display_name: 'Y', slug: 'y', organization_type: 'label', timezone: 'UTC', default_currency: 'USD', status: 'active', created_by: 1, created_at: '', updated_at: '' },
      membership: { id: 1, organization_id: 2, user_id: 1, status: 'active', created_at: '', updated_at: '' },
      roles: ['owner'],
    });
  });

  it('activates organization context', () => {
    api.activate(9).subscribe();
    const req = http.expectOne(`${base}/organizations/9/activate`);
    expect(req.request.method).toBe('POST');
    req.flush({ context: 'active', organization: { id: 9 }, roles: [], permissions: [] });
  });

  it('creates invitation and returns returned-once token once', () => {
    let token: string | null | undefined;
    api.createInvitation(3, 'a@b.com', ['viewer'], 7).subscribe((r) => {
      token = r.invite_token ?? null;
      expect(r.returned_once).toBe(true);
      expect(r.delivery_status).toBe('not_sent');
    });
    const req = http.expectOne(`${base}/organizations/3/invitations`);
    req.flush({
      invitation_id: 1,
      expires_at: '2099-01-01T00:00:00Z',
      invite_token: 'plain-token-once',
      returned_once: true,
      delivery_status: 'not_sent',
      invitation: {
        id: 1,
        organization_id: 3,
        email_normalized: 'a@b.com',
        status: 'pending',
        expires_at: '2099-01-01T00:00:00Z',
        invited_by: 1,
        initial_role_code: 'viewer',
        created_at: '',
        updated_at: '',
      },
    });
    expect(token).toBe('plain-token-once');
  });

  it('accepts invitation by token path', () => {
    api.acceptInvitation('tok').subscribe();
    const req = http.expectOne(`${base}/invitations/tok/accept`);
    expect(req.request.method).toBe('POST');
    req.flush({
      organization: { id: 5, display_name: 'Z', slug: 'z', organization_type: 'label', timezone: 'UTC', default_currency: 'USD', status: 'active', created_by: 1, created_at: '', updated_at: '' },
      membership: { id: 2, organization_id: 5, user_id: 2, status: 'active', created_at: '', updated_at: '' },
    });
  });

  it('lists audit and members with pagination params', () => {
    api.listMembers(1, 2, 10).subscribe();
    const m = http.expectOne((r) => r.url === `${base}/organizations/1/members`);
    expect(m.request.params.get('page')).toBe('2');
    expect(m.request.params.get('limit')).toBe('10');
    m.flush({ items: [], page: 2, limit: 10, total: 0 });

    api.listAudit(1, 1, 25).subscribe();
    const a = http.expectOne((r) => r.url === `${base}/organizations/1/audit-log`);
    expect(a.request.params.get('limit')).toBe('25');
    a.flush({ items: [], page: 1, limit: 25, total: 0 });
  });
});

describe('OrganizationContextService (I4)', () => {
  let ctx: OrganizationContextService;
  let http: HttpTestingController;
  const base = environment.apiUrl;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        OrganizationsApiService,
        OrganizationContextService,
      ],
    });
    ctx = TestBed.inject(OrganizationContextService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  function flushBootstrap(list: object[], current: object): void {
    const listReq = http.expectOne(`${base}/organizations`);
    const curReq = http.expectOne(`${base}/organizations/current`);
    listReq.flush(list);
    curReq.flush(current);
  }

  it('bootstraps none state without organization', async () => {
    const p = ctx.bootstrap();
    flushBootstrap([], { context: 'none' });
    await p;
    expect(ctx.contextKind()).toBe('none');
    expect(ctx.hasOrganization()).toBe(false);
    expect(ctx.permissions()).toEqual([]);
  });

  it('bootstraps active context with permissions', async () => {
    const p = ctx.bootstrap();
    flushBootstrap(
      [{ id: 1, display_name: 'A', slug: 'a', organization_type: 'label', timezone: 'UTC', default_currency: 'USD', status: 'active', created_by: 1, created_at: '', updated_at: '' }],
      {
        context: 'active',
        organization: { id: 1, display_name: 'A', slug: 'a', organization_type: 'label', timezone: 'UTC', default_currency: 'USD', status: 'active', created_by: 1, created_at: '', updated_at: '' },
        membership: { id: 9, organization_id: 1, user_id: 1, status: 'active', created_at: '', updated_at: '' },
        roles: ['owner'],
        permissions: ['organization.view', 'member.view'],
      },
    );
    await p;
    expect(ctx.hasOrganization()).toBe(true);
    expect(ctx.hasPermission('member.view')).toBe(true);
    expect(ctx.hasPermission('audit.view')).toBe(false);
  });

  it('clears previous permissions when switching organization', async () => {
    const boot = ctx.bootstrap();
    flushBootstrap(
      [
        { id: 1, display_name: 'A', slug: 'a', organization_type: 'label', timezone: 'UTC', default_currency: 'USD', status: 'active', created_by: 1, created_at: '', updated_at: '' },
        { id: 2, display_name: 'B', slug: 'b', organization_type: 'label', timezone: 'UTC', default_currency: 'USD', status: 'active', created_by: 1, created_at: '', updated_at: '' },
      ],
      {
        context: 'active',
        organization: { id: 1, display_name: 'A', slug: 'a', organization_type: 'label', timezone: 'UTC', default_currency: 'USD', status: 'active', created_by: 1, created_at: '', updated_at: '' },
        roles: ['owner'],
        permissions: ['audit.view'],
      },
    );
    await boot;
    expect(ctx.hasPermission('audit.view')).toBe(true);

    const act = ctx.activate(2);
    const actReq = http.expectOne(`${base}/organizations/2/activate`);
    actReq.flush({
      context: 'active',
      organization: { id: 2, display_name: 'B', slug: 'b', organization_type: 'label', timezone: 'UTC', default_currency: 'USD', status: 'active', created_by: 1, created_at: '', updated_at: '' },
      roles: ['viewer'],
      permissions: ['organization.view'],
    });
    await Promise.resolve();
    const listReq = http.expectOne(`${base}/organizations`);
    listReq.flush([
      { id: 1, display_name: 'A', slug: 'a', organization_type: 'label', timezone: 'UTC', default_currency: 'USD', status: 'active', created_by: 1, created_at: '', updated_at: '' },
      { id: 2, display_name: 'B', slug: 'b', organization_type: 'label', timezone: 'UTC', default_currency: 'USD', status: 'active', created_by: 1, created_at: '', updated_at: '' },
    ]);
    await act;
    expect(ctx.activeOrganization()?.id).toBe(2);
    expect(ctx.hasPermission('audit.view')).toBe(false);
    expect(ctx.hasPermission('organization.view')).toBe(true);
  });
});

describe('Organizations routes (I4)', () => {
  it('registers key organization paths under dashboard layout', () => {
    const layout = APP_ROUTES.find((r) => r.path === '' && r.children);
    const children = layout?.children ?? [];
    const paths = new Set(children.map((c) => c.path));
    for (const required of [
      'organizations/new',
      'organizations/onboarding',
      'organizations/none',
      'organizations/suspended',
      'organizations/closed',
      'organizations/:id/settings',
      'organizations/:id/members',
      'organizations/:id/invitations',
      'organizations/:id/roles',
      'organizations/:id/audit',
      'access-denied',
      'invitations/accept',
    ]) {
      expect(paths.has(required)).toBe(true);
    }
    // I5: path-token accept route removed (Referer leakage).
    expect(paths.has('invitations/:token/accept')).toBe(false);
    // Personal routes remain available without org context.
    expect(paths.has('discover')).toBe(true);
    expect(paths.has('users')).toBe(true);
    expect(paths.has('settings')).toBe(true);
  });

  it('exports ORGANIZATIONS_ROUTES with loaders', () => {
    expect(ORGANIZATIONS_ROUTES.length).toBeGreaterThan(5);
    expect(ORGANIZATIONS_ROUTES.every((r) => typeof r.loadComponent === 'function')).toBe(true);
  });
});

describe('Org UI permission helpers (I4)', () => {
  it('does not treat localStorage as authorization source in context service', () => {
    localStorage.setItem('fake_org_perms', JSON.stringify(['audit.view']));
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        OrganizationsApiService,
        OrganizationContextService,
      ],
    });
    const ctx = TestBed.inject(OrganizationContextService);
    expect(ctx.hasPermission('audit.view')).toBe(false);
    localStorage.removeItem('fake_org_perms');
  });
});
