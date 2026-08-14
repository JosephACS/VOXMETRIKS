import {
  filterSpaceNavSections,
  spaceNavSectionsFor,
} from './space-nav.config';
import { SPACE_NAV_ICON_PATHS, spaceNavIconMarkup } from './space-nav.icons';
import {
  homePathForSpace,
  personalSpace,
  organizationSpace,
  dataOpsSpace,
  artistSpace,
  platformAdminSpace,
} from './space.models';

describe('space models & nav (043 product)', () => {
  it('maps home paths per space kind', () => {
    expect(homePathForSpace(personalSpace())).toBe('/discover');
    expect(homePathForSpace(organizationSpace(3, 'Org'))).toBe('/workpanel');
    expect(homePathForSpace(dataOpsSpace())).toBe('/workpanel');
    expect(homePathForSpace(artistSpace(7, 'Act'))).toBe('/artist-space');
    expect(homePathForSpace(platformAdminSpace())).toBe('/workpanel');
  });

  it('personal nav is Discover/Search + library + personal account', () => {
    const paths = spaceNavSectionsFor('personal').flatMap((s) => s.items.map((i) => i.path));
    expect(paths).toEqual([
      '/discover',
      '/search',
      '/tracks',
      '/playlists',
      '/liked',
      '/history',
      '/activity',
      '/account/plans',
      '/account/subscription',
      '/account/household',
      '/account/billing',
      '/settings',
      '/artist-space/claim',
      '/organizations/new',
    ]);
  });

  it('organization nav keeps principal hubs plus admin commercial modules', () => {
    const items = spaceNavSectionsFor('organization', { organizationId: 5 }).flatMap(
      (s) => s.items,
    );
    const paths = items.map((i) => i.path);
    expect(paths.slice(0, 4)).toEqual(['/workpanel', '/catalog', '/organizations/5', '/reports']);
    expect(paths).toContain('/subscriptions/plans');
    expect(paths).toContain('/subscriptions/overview');
    expect(paths).toContain('/billing/invoices');
    expect(paths).toContain('/crm/dashboard');
    expect(paths).toContain('/campaigns');
    expect(paths).toContain('/business-analytics');
    expect(paths).toContain('/royalties');
    expect(paths).toContain('/payouts');
    expect(paths).toContain('/customer-success');
    expect(paths).toContain('/support');
    expect(paths).toContain('/account/plans');
    expect(paths).toContain('/account/subscription');
  });

  it('hides org items when canAccessOrgModule returns false', () => {
    const raw = spaceNavSectionsFor('organization', { organizationId: 1 });
    const filtered = filterSpaceNavSections(raw, {
      hasStaffAccess: false,
      canAccessOrgModule: (module, perm) =>
        module === 'org_admin_basic' && perm === 'organization.view',
    });
    const paths = filtered.flatMap((s) => s.items.map((i) => i.path));
    expect(paths).toContain('/organizations/1');
    expect(paths).toContain('/account/plans');
    expect(paths).not.toContain('/catalog');
    expect(paths).not.toContain('/campaigns');
  });

  it('hides operational catalog during onboarding-tier org access', () => {
    const raw = spaceNavSectionsFor('organization', { organizationId: 1 });
    const filtered = filterSpaceNavSections(raw, {
      hasStaffAccess: true,
      canAccessOrgModule: (module) => module === 'onboarding' || module === 'org_admin_basic',
      productSurface: {
        activeSpaceKind: 'organization',
        navCtx: { identityRole: 'admin', presentationMode: false },
      },
    });
    const paths = filtered.flatMap((s) => s.items.map((i) => i.path));
    expect(paths).toContain('/organizations/1');
    expect(paths).toContain('/workpanel');
    expect(paths).toContain('/reports');
    expect(paths).not.toContain('/catalog');
  });

  it('shows reports only for staff in organization space', () => {
    const raw = spaceNavSectionsFor('organization', { organizationId: 1 });
    const asMember = filterSpaceNavSections(raw, {
      hasStaffAccess: false,
      canAccessOrgModule: () => true,
    });
    expect(asMember.flatMap((s) => s.items.map((i) => i.path))).not.toContain('/reports');

    const asStaff = filterSpaceNavSections(raw, {
      hasStaffAccess: true,
      canAccessOrgModule: () => true,
    });
    expect(asStaff.flatMap((s) => s.items.map((i) => i.path))).toContain('/reports');
  });

  it('engineer nav keeps Estado técnico and Ingeniería de datos on distinct paths', () => {
    const items = spaceNavSectionsFor('data_ops').flatMap((s) => s.items);
    const labels = items.map((i) => i.labelKey);
    const paths = items.map((i) => i.path);
    expect(labels).toContain('nav.technicalStatus');
    expect(labels).toContain('nav.eltPipeline');
    expect(labels).toContain('nav.explorer');
    expect(labels).toContain('spaces.nav.reports');
    expect(labels).not.toContain('nav.workpanel');
    expect(paths.filter((p) => p === '/elt-pipeline').length).toBe(1);
    expect(paths.filter((p) => p === '/workpanel').length).toBe(1);
    const technical = items.find((i) => i.labelKey === 'nav.technicalStatus');
    const engineering = items.find((i) => i.labelKey === 'nav.eltPipeline');
    expect(technical?.path).toBe('/workpanel');
    expect(engineering?.path).toBe('/elt-pipeline');
    expect(paths).toContain('/explorer');
    expect(paths).toContain('/reports');
  });

  it('platform admin nav includes commercial modules and Platform Ops entries', () => {
    const paths = spaceNavSectionsFor('platform_admin').flatMap((s) =>
      s.items.map((i) => i.path),
    );
    expect(paths.slice(0, 4)).toEqual(['/workpanel', '/catalog', '/reports', '/settings']);
    expect(paths).toContain('/platform-ops/artist-requests');
    expect(paths).toContain('/platform-ops/audio-unresolved');
    expect(paths).toContain('/subscriptions/plans');
    expect(paths).toContain('/billing/invoices');
    expect(paths).toContain('/crm/dashboard');
    expect(paths).toContain('/campaigns');
    expect(paths).toContain('/account/plans');
  });

  it('hides Platform Ops entries from non-staff nav contexts', () => {
    const raw = spaceNavSectionsFor('platform_admin');
    const paths = filterSpaceNavSections(raw, {
      hasStaffAccess: false,
      canAccessOrgModule: () => true,
    }).flatMap((s) => s.items.map((i) => i.path));
    expect(paths.some((p) => p.startsWith('/platform-ops'))).toBe(false);
  });

  it('every nav item has a registered icon', () => {
    const kinds = ['personal', 'organization', 'data_ops', 'platform_admin', 'artist'] as const;
    for (const kind of kinds) {
      const items = spaceNavSectionsFor(kind, { organizationId: 1 }).flatMap((s) => s.items);
      for (const item of items) {
        expect(SPACE_NAV_ICON_PATHS[item.iconId]).toBeTruthy();
        expect(spaceNavIconMarkup(item.iconId).length).toBeGreaterThan(10);
      }
    }
  });
});
