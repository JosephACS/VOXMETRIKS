import { CanActivateFn } from '@angular/router';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  decideProductSurfaceAccess,
  presentationModeFromUser,
} from './product-surface.policy';
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

describe('decideProductSurfaceAccess (045)', () => {
  const listener = { identityRole: 'user' as const, presentationMode: false };
  const admin = { identityRole: 'admin' as const, presentationMode: false };
  const presentation = {
    identityRole: 'user' as const,
    presentationMode: true,
  };

  it('blocks personal deep link to CRM with unavailable', () => {
    expect(decideProductSurfaceAccess('/crm/dashboard', listener, 'personal')).toBe(
      'unavailable',
    );
  });

  it('allows organization space commercial campaigns/billing/royalties', () => {
    expect(decideProductSurfaceAccess('/campaigns', listener, 'organization')).toBe('allow');
    expect(decideProductSurfaceAccess('/business-analytics', listener, 'organization')).toBe(
      'allow',
    );
    expect(decideProductSurfaceAccess('/billing/invoices', listener, 'organization')).toBe(
      'allow',
    );
    expect(decideProductSurfaceAccess('/royalties', listener, 'organization')).toBe('allow');
    expect(decideProductSurfaceAccess('/subscriptions/overview', listener, 'organization')).toBe(
      'allow',
    );
    expect(decideProductSurfaceAccess('/reports', listener, 'organization')).toBe('allow');
    expect(decideProductSurfaceAccess('/business-decisions', listener, 'organization')).toBe(
      'allow',
    );
  });

  it('allows CRM in organization and platform_admin spaces', () => {
    expect(decideProductSurfaceAccess('/crm/prospects', listener, 'organization')).toBe('allow');
    expect(decideProductSurfaceAccess('/crm/dashboard', admin, 'platform_admin')).toBe('allow');
  });

  it('blocks listener workpanel even in data_ops space exception', () => {
    expect(decideProductSurfaceAccess('/workpanel', listener, 'data_ops')).toBe('staff-block');
    expect(decideProductSurfaceAccess('/workpanel', admin, 'data_ops')).toBe('allow');
  });

  it('allows presentation demos to out-of-product paths', () => {
    expect(decideProductSurfaceAccess('/crm/dashboard', presentation, 'personal')).toBe(
      'allow',
    );
  });

  it('allows engineer data ops tool paths', () => {
    const engineer = { identityRole: 'engineer' as const, presentationMode: false };
    expect(decideProductSurfaceAccess('/elt-pipeline', engineer, 'data_ops')).toBe('allow');
  });

  it('blocks compliance and business-decisions for personal', () => {
    expect(decideProductSurfaceAccess('/compliance', listener, 'personal')).toBe('unavailable');
    expect(decideProductSurfaceAccess('/business-decisions', listener, 'personal')).toBe(
      'unavailable',
    );
  });
});

describe('presentationModeFromUser', () => {
  it('detects demo.business username', () => {
    expect(presentationModeFromUser({ username: 'demo.business' })).toBe(true);
    expect(presentationModeFromUser({ username: 'alice' })).toBe(false);
  });
});
