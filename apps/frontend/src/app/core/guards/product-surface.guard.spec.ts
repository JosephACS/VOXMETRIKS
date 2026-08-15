import { CanActivateFn } from '@angular/router';
import { convertToParamMap, Router } from '@angular/router';
import { TestBed } from '@angular/core/testing';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { vi } from 'vitest';
import { productSurfaceGuard } from './product-surface.guard';
import { evaluateProductPathAccess } from '../product-surface/product-surface.evaluator';
import { AuthService } from '../services/auth.service';
import { CrmContextService } from '../../packages/crm/services/crm-context.service';
import { SpaceContextService } from '../spaces/space-context.service';
import { OrganizationContextService } from '../../packages/organizations/services/organization-context.service';
import {
  PRODUCT_SURFACE_WRAPPED_PACKAGES,
  prependRouteGuard,
} from './product-surface.routes';

const here = dirname(fileURLToPath(import.meta.url));
const noopGuard: CanActivateFn = () => true;

describe('prependRouteGuard (038 wiring helper)', () => {
  it('prepends guard and skips redirectTo routes', () => {
    const routes = prependRouteGuard(
      [
        { path: 'crm', redirectTo: 'crm/dashboard', pathMatch: 'full' },
        {
          path: 'crm/dashboard',
          canActivate: [noopGuard],
          loadComponent: () => Promise.resolve(class {}),
        },
        {
          path: 'campaigns',
          loadComponent: () => Promise.resolve(class {}),
        },
      ],
      noopGuard,
    );

    expect(routes[0].canActivate).toBeUndefined();
    expect(routes[0].redirectTo).toBe('crm/dashboard');
    expect(routes[1].canActivate?.[0]).toBe(noopGuard);
    expect(routes[1].canActivate?.[1]).toBe(noopGuard);
    expect(routes[2].canActivate?.[0]).toBe(noopGuard);
    expect(routes[2].canActivate?.length).toBe(1);
  });

  it('documents which packages app.routes must wrap', () => {
    expect(PRODUCT_SURFACE_WRAPPED_PACKAGES).toContain('CRM_ROUTES');
    expect(PRODUCT_SURFACE_WRAPPED_PACKAGES).toContain('BILLING_ROUTES');
    expect(PRODUCT_SURFACE_WRAPPED_PACKAGES).toContain('CAMPAIGNS_ROUTES');
    expect(PRODUCT_SURFACE_WRAPPED_PACKAGES as readonly string[]).not.toContain(
      'PLATFORM_OPS_ROUTES',
    );
  });
});

describe('app.routes.ts product-surface attachment (source contract)', () => {
  it('wraps 038 demo packages and leaves platform-ops unwrapped', () => {
    const src = readFileSync(join(here, '../../app.routes.ts'), 'utf8');
    for (const pkg of PRODUCT_SURFACE_WRAPPED_PACKAGES) {
      expect(src).toContain(`withProductSurfaceGuard(${pkg})`);
    }
    expect(src).toContain('...PLATFORM_OPS_ROUTES');
    expect(src).not.toContain('withProductSurfaceGuard(PLATFORM_OPS_ROUTES)');
    expect(src).not.toContain('withProductSurfaceGuard(ARTIST_PROFILES_ROUTES)');
    expect(src).not.toContain('withProductSurfaceGuard(CATALOG_PUBLISHING_ROUTES)');
  });
});

describe('evaluateProductPathAccess (054)', () => {
  function ctx(partial: Record<string, unknown> = {}) {
    return {
      ready: true,
      activeSpace: 'organization' as const,
      organizationId: 1,
      organizationTier: 'operational' as const,
      permissions: new Set<string>(),
      artistCapabilities: new Set<string>(),
      staffCapabilities: new Set<string>(),
      platformRoles: new Set<string>(),
      ...partial,
    };
  }

  it('blocks personal deep link to CRM with unavailable', () => {
    expect(
      evaluateProductPathAccess('/crm/dashboard', ctx({ activeSpace: 'personal' })),
    ).toBe('unavailable');
  });

  it('permission-denied when org space lacks capability', () => {
    expect(evaluateProductPathAccess('/campaigns', ctx())).toBe('permission-denied');
    expect(
      evaluateProductPathAccess(
        '/campaigns',
        ctx({ permissions: new Set(['campaign.view']) }),
      ),
    ).toBe('allow');
  });

  it('unavailable for wrong tier even with permission', () => {
    expect(
      evaluateProductPathAccess(
        '/campaigns',
        ctx({
          organizationTier: 'onboarding',
          permissions: new Set(['campaign.view']),
        }),
      ),
    ).toBe('unavailable');
  });

  it('allows staff workpanel in data_ops; denies listener', () => {
    expect(
      evaluateProductPathAccess('/workpanel', ctx({ activeSpace: 'data_ops' })),
    ).toBe('permission-denied');
    expect(
      evaluateProductPathAccess(
        '/workpanel',
        ctx({
          activeSpace: 'data_ops',
          staffCapabilities: new Set(['identity.staff']),
        }),
      ),
    ).toBe('allow');
  });

  it('blocks compliance for personal space', () => {
    expect(
      evaluateProductPathAccess('/compliance', ctx({ activeSpace: 'personal' })),
    ).toBe('unavailable');
  });
});

describe('productSurfaceGuard organization deep links', () => {
  it('selects the requested authorized organization before evaluating checkout access', async () => {
    const selectSpace = vi.fn().mockResolvedValue(true);
    const activeSpace = vi
      .fn()
      .mockReturnValueOnce({ id: 'personal', kind: 'personal' })
      .mockReturnValue({ id: 'org:9', kind: 'organization', organizationId: 9 });

    TestBed.configureTestingModule({
      providers: [
        {
          provide: AuthService,
          useValue: { role: () => 'user', getUser: () => ({ username: 'owner' }) },
        },
        { provide: CrmContextService, useValue: { roles: () => [] } },
        {
          provide: SpaceContextService,
          useValue: {
            ensureReady: vi.fn().mockResolvedValue(undefined),
            activeSpace,
            activeSpaceKind: () => activeSpace()?.kind ?? null,
            selectSpace,
            bootstrapFromSession: vi.fn().mockResolvedValue({}),
            productSurfaceContext: () => ({
              ready: true,
              activeSpace: 'organization',
              organizationId: 9,
              organizationTier: 'operational',
              permissions: new Set(['subscription.view', 'organization.view']),
              artistCapabilities: new Set(),
              staffCapabilities: new Set(),
              platformRoles: new Set(),
            }),
          },
        },
        {
          provide: OrganizationContextService,
          useValue: {
            activate: vi.fn().mockResolvedValue(undefined),
          },
        },
        {
          provide: Router,
          useValue: { createUrlTree: vi.fn((commands: string[]) => commands) },
        },
      ],
    });

    const result = await TestBed.runInInjectionContext(() =>
      productSurfaceGuard(
        {
          queryParamMap: convertToParamMap({ organization_id: '9' }),
        } as never,
        { url: '/subscriptions/checkout?organization_id=9' } as never,
      ),
    );

    expect(selectSpace).toHaveBeenCalledWith('org:9', { navigate: false });
    expect(result).toBe(true);
  });
});
