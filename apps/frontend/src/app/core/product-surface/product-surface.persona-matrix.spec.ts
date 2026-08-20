import { describe, expect, it } from 'vitest';
import {
  STAFF_CAPABILITY,
  evaluateProductPathAccess,
  listVisibleContextTabs,
  listVisibleSidebarSurfaces,
  resolveSurfacePath,
  emptyProductSurfaceContext,
  type ProductSurfaceContext,
} from './index';
import { resolveModuleContext } from '../../shared/navigation/module-context';

function persona(partial: Partial<ProductSurfaceContext> & Pick<ProductSurfaceContext, 'activeSpace'>): ProductSurfaceContext {
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

describe('Spec 054 persona matrix + visible-link parity', () => {
  it('owner (operational + broad permissions) sees org hubs, billing edit paths and reports', () => {
    const ctx = persona({
      activeSpace: 'organization',
      organizationId: 1,
      organizationTier: 'operational',
      permissions: new Set([
        'organization.view',
        'organization.update',
        'member.view',
        'member.invite',
        'role.view',
        'audit.view',
        'subscription.view',
        'invoice.view',
        'billing.view',
        'report.view',
        'royalty.view',
        'artist.view',
        'publishing.view',
        'publishing.create',
        'publishing.review',
        'rights.view',
        'campaign.view',
        'biz_analytics.view',
      ]),
    });
    const paths = sidebarPaths(ctx);
    expect(paths).toContain('/organizations/1');
    expect(paths).toContain('/catalog');
    expect(paths).toContain('/reports');
    expect(paths).toContain('/subscriptions/overview');
    expect(paths).toContain('/billing/invoices');
    expect(paths).toContain('/campaigns');
    expect(paths).not.toContain('/workpanel');

    const orgTabs = listVisibleContextTabs('organization', ctx).map((s) =>
      resolveSurfacePath(s, 1),
    );
    expect(orgTabs).toContain('/organizations/1/settings');
    expect(orgTabs).toContain('/organizations/1/members');
    expect(orgTabs).toContain('/organizations/1/invitations');
    expect(orgTabs).toContain('/subscriptions/overview');

    const catalogTabs = listVisibleContextTabs('catalog', ctx).map((s) => s.path);
    expect(catalogTabs).toContain('/catalog-review');
    expect(catalogTabs).toContain('/artist-profiles');
    expect(catalogTabs).toContain('/artist/tracks');
  });

  it('negatives without each commercial permission hide those surfaces', () => {
    const ctx = persona({
      activeSpace: 'organization',
      organizationId: 2,
      organizationTier: 'operational',
      permissions: new Set(['organization.view']),
    });
    const paths = sidebarPaths(ctx);
    expect(paths).not.toContain('/campaigns');
    expect(paths).not.toContain('/business-analytics');
    expect(paths).not.toContain('/customer-success');
    expect(paths).not.toContain('/support');
    expect(paths).not.toContain('/compliance');
    expect(paths).not.toContain('/catalog');
  });

  it('positives independent by permission', () => {
    const base = {
      activeSpace: 'organization' as const,
      organizationId: 3,
      organizationTier: 'operational' as const,
    };
    expect(
      sidebarPaths(persona({ ...base, permissions: new Set(['campaign.view']) })),
    ).toContain('/campaigns');
    expect(
      sidebarPaths(persona({ ...base, permissions: new Set(['biz_analytics.view']) })),
    ).toContain('/business-analytics');
    expect(
      sidebarPaths(persona({ ...base, permissions: new Set(['customer_success.view']) })),
    ).toContain('/customer-success');
    expect(
      sidebarPaths(persona({ ...base, permissions: new Set(['support.view']) })),
    ).not.toContain('/support');
    expect(
      listVisibleContextTabs(
        'customerSuccess',
        persona({ ...base, permissions: new Set(['support.view']) }),
      ).map((s) => s.path),
    ).toContain('/support');
    expect(
      sidebarPaths(persona({ ...base, permissions: new Set(['compliance.view']) })),
    ).toContain('/compliance');
    expect(
      sidebarPaths(persona({ ...base, permissions: new Set(['compliance.manage']) })),
    ).not.toContain('/compliance/admin');
    expect(
      listVisibleContextTabs(
        'compliance',
        persona({ ...base, permissions: new Set(['compliance.manage']) }),
      ).map((s) => s.path),
    ).toContain('/compliance/admin');
  });

  it('CRM hub is single sidebar entry; children are tabs', () => {
    const ctx = persona({
      activeSpace: 'organization',
      organizationId: 1,
      organizationTier: 'operational',
      staffCapabilities: new Set([STAFF_CAPABILITY.shell]),
    });
    const paths = sidebarPaths(ctx);
    expect(paths.filter((p) => p.startsWith('/crm')).length).toBe(1);
    expect(paths).toContain('/crm/dashboard');
    expect(paths).not.toContain('/crm/prospects');
    expect(paths).not.toContain('/crm/opportunities');
    const tabs = listVisibleContextTabs('crm', ctx).map((s) => s.path);
    expect(tabs).toEqual(
      expect.arrayContaining([
        '/crm/dashboard',
        '/crm/prospects',
        '/crm/contacts',
        '/crm/opportunities',
        '/crm/approvals',
        '/crm/audit',
      ]),
    );
  });

  it('CRM platform role unlocks CRM hub without identity staff', () => {
    const ctx = persona({
      activeSpace: 'organization',
      organizationId: 1,
      organizationTier: 'operational',
      platformRoles: new Set(['sales_manager']),
    });
    expect(sidebarPaths(ctx)).toContain('/crm/dashboard');
    expect(evaluateProductPathAccess('/crm/prospects', ctx)).toBe('allow');
  });

  it('billing persona sees recovery billing without operational catalog', () => {
    const ctx = persona({
      activeSpace: 'organization',
      organizationId: 2,
      organizationTier: 'recovery',
      permissions: new Set([
        'organization.view',
        'subscription.view',
        'invoice.view',
        'billing.view',
      ]),
    });
    const paths = sidebarPaths(ctx);
    expect(paths).toContain('/billing/invoices');
    expect(paths).toContain('/billing/profile');
    expect(paths).toContain('/subscriptions/overview');
    expect(paths).not.toContain('/catalog');
    expect(paths).not.toContain('/reports');
    expect(paths).not.toContain('/campaigns');
  });

  it('analyst with report.view sees Reports; not Workpanel', () => {
    const ctx = persona({
      activeSpace: 'organization',
      organizationId: 3,
      organizationTier: 'operational',
      permissions: new Set(['organization.view', 'report.view']),
    });
    const paths = sidebarPaths(ctx);
    expect(paths).toContain('/reports');
    expect(paths).not.toContain('/workpanel');
    expect(paths).not.toContain('/crm/dashboard');
    expect(paths).not.toContain('/campaigns');
  });

  it('viewer with organization.view only keeps hub + personal account', () => {
    const ctx = persona({
      activeSpace: 'organization',
      organizationId: 4,
      organizationTier: 'operational',
      permissions: new Set(['organization.view']),
    });
    const paths = sidebarPaths(ctx);
    expect(paths).toContain('/organizations/4');
    expect(paths).not.toContain('/catalog');
    expect(paths).not.toContain('/campaigns');
    expect(paths).not.toContain('/reports');
    expect(paths).not.toContain('/royalties');
    expect(paths).not.toContain('/billing/invoices');
  });

  it('catalog tabs are permission-gated independently', () => {
    const base = {
      activeSpace: 'organization' as const,
      organizationId: 8,
      organizationTier: 'operational' as const,
    };
    expect(
      listVisibleContextTabs(
        'catalog',
        persona({ ...base, permissions: new Set(['artist.view']) }),
      ).map((s) => s.path),
    ).toEqual(expect.arrayContaining(['/catalog', '/artist-profiles']));
    expect(
      listVisibleContextTabs(
        'catalog',
        persona({ ...base, permissions: new Set(['publishing.view']) }),
      ).map((s) => s.path),
    ).toEqual(expect.arrayContaining(['/catalog', '/artist/tracks', '/artist/releases']));
    expect(
      listVisibleContextTabs(
        'catalog',
        persona({ ...base, permissions: new Set(['publishing.create']) }),
      ).map((s) => s.path),
    ).toContain('/artist/releases/new');
    expect(
      listVisibleContextTabs(
        'catalog',
        persona({ ...base, permissions: new Set(['rights.view']) }),
      ).map((s) => s.path),
    ).toContain('/catalog-rights/conflicts');
  });

  it('artist persona is capability-gated', () => {
    const ctx = persona({
      activeSpace: 'artist',
      artistCapabilities: new Set(['artist_space.view', 'artist_space.catalog.view']),
    });
    expect(sidebarPaths(ctx)).toEqual([
      '/artist-space',
      '/artist-space/profile',
      '/artist-space/music',
      '/artist-space/team',
    ]);
  });

  it('engineer data_ops sees workpanel/elt/explorer/reports', () => {
    const ctx = persona({
      activeSpace: 'data_ops',
      staffCapabilities: new Set([STAFF_CAPABILITY.shell, STAFF_CAPABILITY.engineering]),
    });
    expect(sidebarPaths(ctx)).toEqual([
      '/workpanel',
      '/elt-pipeline',
      '/explorer',
      '/reports',
    ]);
  });

  it('platform admin sees platform ops and no org commercial without org context', () => {
    const ctx = persona({
      activeSpace: 'platform_admin',
      staffCapabilities: new Set([STAFF_CAPABILITY.shell, STAFF_CAPABILITY.engineering]),
      platformRoles: new Set(['platform_admin']),
    });
    const paths = sidebarPaths(ctx);
    expect(paths).toContain('/platform-ops/artist-requests');
    expect(paths).toContain('/platform-ops/audio-unresolved');
    expect(paths).not.toContain('/subscriptions/plans');
    expect(paths).not.toContain('/crm/dashboard');
    expect(paths).not.toContain('/catalog');
  });

  it('CRM platform_admin unlocks Platform Ops without identity.staff', () => {
    const ctx = persona({
      activeSpace: 'platform_admin',
      platformRoles: new Set(['platform_admin']),
    });
    const paths = sidebarPaths(ctx);
    expect(paths).toContain('/workpanel');
    expect(paths).toContain('/platform-ops');
    expect(paths).toContain('/platform-ops/artist-requests');
    expect(evaluateProductPathAccess('/platform-ops/system', ctx)).toBe('allow');
  });

  it('ready=false never flashes privileged organization surfaces', () => {
    const ctx = {
      ...emptyProductSurfaceContext('organization'),
      organizationId: 9,
      organizationTier: 'operational' as const,
      permissions: new Set(['organization.view', 'report.view', 'royalty.view']),
      staffCapabilities: new Set([STAFF_CAPABILITY.shell]),
    };
    const paths = sidebarPaths(ctx);
    expect(paths).not.toContain('/catalog');
    expect(paths).not.toContain('/reports');
    expect(paths).not.toContain('/workpanel');
    expect(paths).not.toContain('/organizations/9');
    expect(paths).not.toContain('/campaigns');
    expect(paths.every((p) => p.startsWith('/account') || p === '/settings')).toBe(true);
  });

  it('path access: missing permission → permission-denied; wrong space → unavailable', () => {
    const orgReady = persona({
      activeSpace: 'organization',
      organizationId: 1,
      organizationTier: 'operational',
      permissions: new Set(['organization.view']),
    });
    expect(evaluateProductPathAccess('/campaigns', orgReady)).toBe('permission-denied');
    expect(
      evaluateProductPathAccess(
        '/campaigns',
        persona({
          ...orgReady,
          permissions: new Set(['campaign.view']),
        }),
      ),
    ).toBe('allow');
    expect(
      evaluateProductPathAccess('/campaigns', persona({ activeSpace: 'personal' })),
    ).toBe('unavailable');
    expect(
      evaluateProductPathAccess(
        '/campaigns',
        persona({
          activeSpace: 'organization',
          organizationId: 1,
          organizationTier: 'onboarding',
          permissions: new Set(['campaign.view']),
        }),
      ),
    ).toBe('plan-required');
    expect(evaluateProductPathAccess('/discover', persona({ activeSpace: 'personal' }))).toBe(
      'allow',
    );
  });

  it('module-context tabs hide review without publishing.review', () => {
    const ctx = persona({
      activeSpace: 'organization',
      organizationId: 8,
      organizationTier: 'operational',
      permissions: new Set(['organization.view', 'artist.view']),
    });
    const view = resolveModuleContext('/catalog', ctx);
    expect(view?.tabs.map((t) => t.path)).not.toContain('/catalog-review');
    expect(view?.tabs.map((t) => t.path)).toContain('/catalog');
  });
});
