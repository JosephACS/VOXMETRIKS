import {
  canAnnounceSpaceNavItem,
  filterSpaceNavSections,
  spaceNavSectionsFor,
  type SpaceNavItem,
} from './space-nav.config';
import { decideProductSurfaceAccess } from '../guards/product-surface.policy';
import type { OrgModuleKind } from '../../packages/organizations/organization-access';

/**
 * Menu announce must match the same policy stack as route guards:
 * decideProductSurfaceAccess + canAccessOrganizationModule (via canAccessOrgModule).
 */
describe('organization nav announce ↔ guard parity', () => {
  const listener = { identityRole: 'user' as const, presentationMode: false };

  function announcePaths(opts: {
    spaceKind: 'organization' | 'personal';
    canAccessOrgModule: (moduleKind: OrgModuleKind, requiredPermission?: string | null) => boolean;
  }): string[] {
    const raw = spaceNavSectionsFor('organization', { organizationId: 9 });
    return filterSpaceNavSections(raw, {
      hasStaffAccess: false,
      canAccessOrgModule: opts.canAccessOrgModule,
      productSurface: {
        activeSpaceKind: opts.spaceKind,
        navCtx: listener,
      },
    }).flatMap((s) => s.items.map((i) => i.path));
  }

  it('never announces product-surface-blocked commercial paths in personal space', () => {
    const paths = announcePaths({
      spaceKind: 'personal',
      canAccessOrgModule: () => true,
    });
    for (const path of [
      '/campaigns',
      '/business-analytics',
      '/billing/invoices',
      '/subscriptions/overview',
    ]) {
      expect(decideProductSurfaceAccess(path, listener, 'personal')).toBe('unavailable');
      expect(paths).not.toContain(path);
    }
  });

  it('announces commercial paths only when organization space allows product surface', () => {
    for (const path of [
      '/campaigns',
      '/business-analytics',
      '/billing/invoices',
      '/subscriptions/overview',
    ]) {
      expect(decideProductSurfaceAccess(path, listener, 'organization')).toBe('allow');
    }
    const paths = announcePaths({
      spaceKind: 'organization',
      canAccessOrgModule: () => true,
    });
    expect(paths).toEqual(
      expect.arrayContaining([
        '/campaigns',
        '/business-analytics',
        '/billing/invoices',
        '/subscriptions/overview',
      ]),
    );
  });

  it('keeps operational catalog/artist-profiles hidden for onboarding tier', () => {
    const onboardingOnly = (moduleKind: OrgModuleKind) =>
      moduleKind === 'onboarding' || moduleKind === 'org_admin_basic';

    const catalog: SpaceNavItem = {
      path: '/catalog',
      labelKey: 'nav.catalogHub',
      iconId: 'catalog',
      orgModule: 'operational',
    };
    expect(
      canAnnounceSpaceNavItem(catalog, {
        hasStaffAccess: false,
        canAccessOrgModule: onboardingOnly,
        productSurface: { activeSpaceKind: 'organization', navCtx: listener },
      }),
    ).toBe(false);

    const paths = announcePaths({
      spaceKind: 'organization',
      canAccessOrgModule: onboardingOnly,
    });
    expect(paths).not.toContain('/catalog');
    expect(paths).not.toContain('/artist-profiles');
    expect(paths).not.toContain('/business-analytics');
  });

  it('staff-only reports stay off for non-staff even when org modules pass', () => {
    const paths = announcePaths({
      spaceKind: 'organization',
      canAccessOrgModule: () => true,
    });
    expect(paths).not.toContain('/reports');
  });
});
