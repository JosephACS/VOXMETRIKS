import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { environment } from '../../../../environments/environment';
import { OrganizationsApiService } from './organizations-api.service';
import { OrganizationContextService } from './organization-context.service';
import { SUBSCRIPTIONS_ROUTES } from '../../subscriptions/subscriptions.routes';

const base = environment.apiUrl;

const orgRow = {
  id: 1,
  display_name: 'VOXMETRIKS Demo',
  slug: 'voxmetriks-demo',
  organization_type: 'label',
  timezone: 'UTC',
  default_currency: 'USD',
  status: 'active',
  created_by: 1,
  created_at: '',
  updated_at: '',
};

describe('OrganizationContextService subscription bootstrap (deep-link parity)', () => {
  let ctx: OrganizationContextService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.resetTestingModule();
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

  afterEach(() => {
    for (const req of http.match(() => true)) {
      req.flush({});
    }
    http.verify();
    TestBed.resetTestingModule();
  });

  async function flushOrgBootstrap(current: object): Promise<void> {
    http.expectOne(`${base}/organizations`).flush([orgRow]);
    http.expectOne(`${base}/organizations/current`).flush(current);
    await Promise.resolve();
  }

  function drainSoftSubscriptions(): void {
    for (const req of http.match(
      (r) => r.method === 'GET' && /\/subscriptions(\?|$)/.test(r.url),
    )) {
      req.flush({ items: [], page: 1, limit: 20, total: 0 });
    }
  }

  async function flushActiveSubscriptionEnrichment(opts?: {
    status?: string;
    access_state?: string;
    empty?: boolean;
  }): Promise<void> {
    await Promise.resolve();
    const listReq = http.expectOne(
      (r) => r.url === `${base}/subscriptions` && r.headers.get('X-Organization-Id') === '1',
    );
    if (opts?.empty) {
      listReq.flush({ items: [], page: 1, limit: 20, total: 0 });
      await Promise.resolve();
      return;
    }
    listReq.flush({
      items: [
        {
          id: 77,
          status: opts?.status ?? 'active',
          access_state: opts?.access_state ?? 'full',
          organization_id: 1,
          plan_id: 1,
        },
      ],
      page: 1,
      limit: 20,
      total: 1,
    });
    await Promise.resolve();
    await Promise.resolve();
    http
      .expectOne(`${base}/subscriptions/77/entitlements`)
      .flush([{ feature_code: 'catalog.publish', enabled: true }]);
    await Promise.resolve();
  }

  it('054: /current tier makes operational ready without blocking on soft enrichment', async () => {
    const boot = ctx.bootstrap();
    const readyProbe = ctx.ensureReady();

    await flushOrgBootstrap({
      context: 'active',
      organization: orgRow,
      membership: {
        id: 9,
        organization_id: 1,
        user_id: 1,
        status: 'active',
        created_at: '',
        updated_at: '',
      },
      roles: ['owner'],
      permissions: ['organization.view', 'subscription.view', 'member.view', 'royalty.view'],
      subscription_access: {
        has_subscription: true,
        status: null,
        access_state: null,
        tier: 'operational',
      },
    });

    await Promise.all([boot, readyProbe]);
    expect(ctx.status()).toBe('ready');
    expect(ctx.accessTier()).toBe('operational');
    expect(ctx.canAccessModule('operational', 'royalty.view')).toBe(true);

    await flushActiveSubscriptionEnrichment();
    expect(ctx.accessTier()).toBe('operational');
  });

  it('6: soft enrichment failure keeps /current gate (no network downgrade)', async () => {
    const boot = ctx.bootstrap();
    await flushOrgBootstrap({
      context: 'active',
      organization: orgRow,
      membership: {
        id: 9,
        organization_id: 1,
        user_id: 1,
        status: 'active',
        created_at: '',
        updated_at: '',
      },
      roles: ['owner'],
      permissions: ['organization.view', 'subscription.view'],
      subscription_access: {
        has_subscription: true,
        status: 'active',
        access_state: 'full',
      },
    });

    await boot;
    expect(ctx.status()).toBe('ready');
    expect(ctx.accessTier()).toBe('operational');

    http
      .expectOne(
        (r) => r.url === `${base}/subscriptions` && r.headers.get('X-Organization-Id') === '1',
      )
      .flush({ detail: 'boom' }, { status: 500, statusText: 'Server Error' });

    await Promise.resolve();
    expect(ctx.accessTier()).toBe('operational');
    expect(ctx.canAccessModule('operational')).toBe(true);
  });

  it('7: concurrent ensureReady callers share one bootstrap', async () => {
    const p1 = ctx.ensureReady();
    const p2 = ctx.ensureReady();
    await flushOrgBootstrap({
      context: 'active',
      organization: orgRow,
      membership: {
        id: 9,
        organization_id: 1,
        user_id: 1,
        status: 'active',
        created_at: '',
        updated_at: '',
      },
      roles: ['owner'],
      permissions: ['organization.view', 'subscription.view'],
      subscription_access: {
        has_subscription: true,
        status: 'active',
        access_state: 'full',
        tier: 'operational',
      },
    });
    await Promise.all([p1, p2]);
    expect(ctx.accessTier()).toBe('operational');
    drainSoftSubscriptions();
  });

  it('8: real onboarding (no subscription) still blocks operational modules', async () => {
    const boot = ctx.bootstrap();
    await flushOrgBootstrap({
      context: 'active',
      organization: orgRow,
      membership: {
        id: 9,
        organization_id: 1,
        user_id: 1,
        status: 'active',
        created_at: '',
        updated_at: '',
      },
      roles: ['owner'],
      permissions: ['organization.view', 'subscription.view'],
      subscription_access: { has_subscription: false, status: null, access_state: null },
    });
    await boot;
    expect(ctx.accessTier()).toBe('onboarding');
    expect(ctx.canAccessModule('operational')).toBe(false);
    expect(ctx.canAccessModule('onboarding', 'subscription.view')).toBe(true);
    await flushActiveSubscriptionEnrichment({ empty: true });
  });

  it('activate becomes ready from /activate subscription_access; soft enrichment is non-blocking', async () => {
    const boot = ctx.bootstrap();
    http.expectOne(`${base}/organizations`).flush([]);
    http.expectOne(`${base}/organizations/current`).flush({ context: 'none' });
    await boot;
    expect(ctx.hasOrganization()).toBe(false);

    const act = ctx.activate(1);
    http.expectOne(`${base}/organizations/1/activate`).flush({
      context: 'active',
      organization: orgRow,
      membership: {
        id: 9,
        organization_id: 1,
        user_id: 1,
        status: 'active',
        created_at: '',
        updated_at: '',
      },
      roles: ['owner'],
      permissions: ['organization.view', 'subscription.view'],
      subscription_access: {
        has_subscription: true,
        status: null,
        access_state: null,
        tier: 'operational',
      },
    });
    await Promise.resolve();
    http.expectOne(`${base}/organizations`).flush([orgRow]);
    await act;
    expect(ctx.status()).toBe('ready');
    expect(ctx.accessTier()).toBe('operational');
    drainSoftSubscriptions();
  });
});

describe('SUBSCRIPTIONS_ROUTES titles (no embedded brand)', () => {
  it('uses clean human titles without Voxmetrik/VOXMETRIKS', () => {
    const titles = SUBSCRIPTIONS_ROUTES.map((r) => r.title).filter(Boolean) as string[];
    expect(titles).toEqual([
      'Planes',
      'Plan',
      'Mi suscripción',
      'Iniciar prueba',
      'Seleccionar plan',
      'checkout.title',
      'Cancelar suscripción',
      'Complementos',
      'Uso',
    ]);
    for (const title of titles) {
      expect(title.toLowerCase()).not.toContain('voxmetrik');
    }
  });
});
