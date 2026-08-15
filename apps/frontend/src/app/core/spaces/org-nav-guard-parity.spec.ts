import {
  canAnnounceSpaceNavItem,
  filterSpaceNavSections,
  spaceNavSectionsFor,
} from './space-nav.config';
import { evaluateProductPathAccess } from '../product-surface/product-surface.evaluator';
import {
  STAFF_CAPABILITY,
  type ProductSurfaceContext,
} from '../product-surface';

/**
 * Menu announce must match Spec 054 product-surface evaluator.
 */
describe('organization nav announce ↔ guard parity (054)', () => {
  function ctx(partial: Partial<ProductSurfaceContext>): ProductSurfaceContext {
    return {
      ready: true,
      activeSpace: 'organization',
      organizationId: 9,
      organizationTier: 'operational',
      permissions: new Set(),
      artistCapabilities: new Set(),
      staffCapabilities: new Set(),
      platformRoles: new Set(),
      ...partial,
    };
  }

  function announcePaths(access: ProductSurfaceContext): string[] {
    const raw = spaceNavSectionsFor('organization', { organizationId: 9 });
    return filterSpaceNavSections(raw, {
      productSurfaceContext: access,
    }).flatMap((s) => s.items.map((i) => i.path));
  }

  it('never announces product-surface-blocked commercial paths in personal space', () => {
    const access = ctx({
      activeSpace: 'personal',
      permissions: new Set(['organization.view', 'subscription.view', 'invoice.view', 'campaign.view']),
    });
    const paths = announcePaths(access);
    for (const path of [
      '/campaigns',
      '/business-analytics',
      '/billing/invoices',
      '/subscriptions/overview',
    ]) {
      expect(evaluateProductPathAccess(path, access)).toBe('unavailable');
      expect(paths).not.toContain(path);
    }
  });

  it('announces catalog/org commercial when organization space + permissions allow', () => {
    const paths = announcePaths(
      ctx({
        permissions: new Set([
          'organization.view',
          'subscription.view',
          'invoice.view',
          'report.view',
          'artist.view',
          'campaign.view',
          'biz_analytics.view',
        ]),
      }),
    );
    expect(paths).toContain('/catalog');
    expect(paths).toContain('/organizations/9');
    expect(paths).toContain('/subscriptions/overview');
    expect(paths).toContain('/campaigns');
    expect(paths).toContain('/business-analytics');
    expect(paths).toContain('/billing/invoices');
  });

  it('keeps operational catalog hidden for onboarding tier', () => {
    expect(
      canAnnounceSpaceNavItem(
        { path: '/catalog', labelKey: 'nav.catalogHub', iconId: 'catalog' },
        {
          productSurfaceContext: ctx({
            organizationTier: 'onboarding',
            permissions: new Set(['organization.view', 'artist.view']),
          }),
        },
      ),
    ).toBe(false);

    const paths = announcePaths(
      ctx({
        organizationTier: 'onboarding',
        permissions: new Set(['organization.view', 'subscription.view', 'campaign.view']),
      }),
    );
    expect(paths).not.toContain('/catalog');
    expect(paths).not.toContain('/business-analytics');
  });

  it('report.view (not staff) announces Reports; Workpanel stays staff-only', () => {
    const paths = announcePaths(
      ctx({
        permissions: new Set(['organization.view', 'report.view']),
        staffCapabilities: new Set(),
      }),
    );
    expect(paths).toContain('/reports');
    expect(paths).not.toContain('/workpanel');

    const staff = announcePaths(
      ctx({
        permissions: new Set(['organization.view']),
        staffCapabilities: new Set([STAFF_CAPABILITY.shell]),
      }),
    );
    expect(staff).toContain('/workpanel');
    expect(staff).not.toContain('/reports');
  });
});
