import { describe, expect, it } from 'vitest';
import {
  STAFF_CAPABILITY,
  evaluateProductPathAccess,
  listVisibleContextTabs,
  listVisibleSidebarSurfaces,
  resolveSurfacePath,
  type ProductSurfaceContext,
} from '../../core/product-surface';
import { resolveModuleContext } from '../../shared/navigation/module-context';
import { ENTERPRISE_ES } from '../../core/i18n/locales/enterprise.es';
import { LOCALE_ES } from '../../core/i18n/locales/es';

function persona(
  partial: Partial<ProductSurfaceContext> & Pick<ProductSurfaceContext, 'activeSpace'>,
): ProductSurfaceContext {
  return {
    ready: true,
    permissions: new Set(),
    artistCapabilities: new Set(),
    staffCapabilities: new Set(),
    platformRoles: new Set(),
    ...partial,
  };
}

function sidebarPaths(ctx: ProductSurfaceContext): string[] {
  return listVisibleSidebarSurfaces(ctx).map((s) => resolveSurfacePath(s, ctx.organizationId));
}

describe('Spec 056 final professional product closure', () => {
  const owner = persona({
    activeSpace: 'organization',
    organizationId: 9,
    organizationTier: 'operational',
    permissions: new Set([
      'organization.view',
      'campaign.view',
      'customer_success.view',
      'support.view',
      'compliance.view',
      'compliance.manage',
    ]),
    platformRoles: new Set(['sales_manager']),
  });

  it('exposes one sidebar entry per commercial domain', () => {
    const paths = sidebarPaths(owner);
    expect(paths.filter((p) => p.startsWith('/crm'))).toEqual(['/crm/dashboard']);
    expect(paths.filter((p) => p.startsWith('/campaigns'))).toEqual(['/campaigns']);
    expect(paths.filter((p) => p === '/customer-success' || p === '/support')).toEqual([
      '/customer-success',
    ]);
    expect(paths.filter((p) => p.startsWith('/compliance'))).toEqual(['/compliance']);
  });

  it('keeps deep links authorized for the same hydrated session', () => {
    expect(evaluateProductPathAccess('/crm/prospects', owner)).toBe('allow');
    expect(evaluateProductPathAccess('/crm/contacts', owner)).toBe('allow');
    expect(evaluateProductPathAccess('/crm/opportunities', owner)).toBe('allow');
    expect(evaluateProductPathAccess('/crm/approvals', owner)).toBe('allow');
    expect(evaluateProductPathAccess('/support', owner)).toBe('allow');
    expect(evaluateProductPathAccess('/compliance/admin', owner)).toBe('allow');
  });

  it('hides compliance admin tab without manage', () => {
    const viewer = persona({
      activeSpace: 'organization',
      organizationId: 9,
      organizationTier: 'operational',
      permissions: new Set(['compliance.view']),
    });
    expect(sidebarPaths(viewer)).toContain('/compliance');
    expect(listVisibleContextTabs('compliance', viewer).map((s) => s.path)).not.toContain(
      '/compliance/admin',
    );
    expect(evaluateProductPathAccess('/compliance/admin', viewer)).toBe('permission-denied');
  });

  it('module chrome exposes CRM/CS/compliance tabs without sidebar clutter', () => {
    const crm = resolveModuleContext('/crm/prospects', owner);
    expect(crm?.moduleId).toBe('crm');
    expect(crm?.tabs.map((t) => t.path)).toEqual(
      expect.arrayContaining(['/crm/dashboard', '/crm/prospects', '/crm/opportunities']),
    );

    const cs = resolveModuleContext('/support', owner);
    expect(cs?.moduleId).toBe('customerSuccess');
    expect(cs?.tabs.some((t) => t.path === '/support')).toBe(true);

    const compliance = resolveModuleContext('/compliance', owner);
    expect(compliance?.moduleId).toBe('compliance');
  });

  it('restricted persona does not see commercial hubs', () => {
    const restricted = persona({
      activeSpace: 'organization',
      organizationId: 9,
      organizationTier: 'operational',
      permissions: new Set(['organization.view']),
    });
    const paths = sidebarPaths(restricted);
    expect(paths).not.toContain('/crm/dashboard');
    expect(paths).not.toContain('/campaigns');
    expect(paths).not.toContain('/customer-success');
    expect(paths).not.toContain('/compliance');
  });

  it('normal UI copy avoids demo/academic/development wording on closed surfaces', () => {
    const keys = [
      'nav.crm.dashboard',
      'nav.customerSuccess.dashboard',
      'nav.compliance.privacy',
      'settings.api.status',
      'settings.profile.desc',
    ] as const;
    for (const key of keys) {
      const value = LOCALE_ES[key as keyof typeof LOCALE_ES] ?? ENTERPRISE_ES[key];
      expect(value, key).toBeTruthy();
      expect(String(value).toLowerCase()).not.toMatch(/demo|académic|academic|desarrollo|development/);
    }
    expect(ENTERPRISE_ES['campaigns.detail.roiDisclosure'].toLowerCase()).toContain('simulad');
    expect(ENTERPRISE_ES['campaigns.detail.roiDisclosure'].toLowerCase()).not.toContain('académic');
    expect(ENTERPRISE_ES['customerSuccess.dashboard.subtitle'].toLowerCase()).not.toContain(
      'académic',
    );
    expect(ENTERPRISE_ES['crm.contract.registerAcceptance'].toLowerCase()).not.toContain(
      'académic',
    );
  });

  it('CRM staff identity still unlocks CRM hub', () => {
    const staff = persona({
      activeSpace: 'organization',
      organizationId: 2,
      organizationTier: 'operational',
      staffCapabilities: new Set([STAFF_CAPABILITY.shell]),
    });
    expect(sidebarPaths(staff)).toContain('/crm/dashboard');
  });
});
