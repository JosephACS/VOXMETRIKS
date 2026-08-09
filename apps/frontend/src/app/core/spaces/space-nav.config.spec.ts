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

describe('space models & nav (045/046)', () => {
  it('maps home paths per space kind', () => {
    expect(homePathForSpace(personalSpace())).toBe('/discover');
    expect(homePathForSpace(organizationSpace(3, 'Org'))).toBe('/organizations/3');
    expect(homePathForSpace(dataOpsSpace())).toBe('/elt-pipeline');
    expect(homePathForSpace(artistSpace(7, 'Act'))).toBe('/artist-space');
    expect(homePathForSpace(platformAdminSpace())).toBe('/platform-ops/artist-requests');
  });

  it('personal nav includes library activity without audio-features', () => {
    const paths = spaceNavSectionsFor('personal').flatMap((s) => s.items.map((i) => i.path));
    expect(paths).toContain('/discover');
    expect(paths).toContain('/activity');
    expect(paths).not.toContain('/audio-features');
    expect(paths).not.toContain('/recommendations');
  });

  it('personal claim nav uses short label key and keeps page title key separate', () => {
    const claim = spaceNavSectionsFor('personal')
      .flatMap((s) => s.items)
      .find((i) => i.path === '/artist-space/claim');
    expect(claim?.labelKey).toBe('spaces.nav.artist.claimShort');
    expect(claim?.labelKey).not.toBe('artistSpace.claim.title');
  });

  it('organization nav includes hub and catalog routes with permission metadata', () => {
    const items = spaceNavSectionsFor('organization', { organizationId: 5 }).flatMap(
      (s) => s.items,
    );
    const paths = items.map((i) => i.path);
    expect(paths).toContain('/organizations/5');
    expect(paths).toContain('/catalog');
    expect(paths).toContain('/artist-profiles');
    const royalties = items.find((i) => i.path === '/royalties');
    expect(royalties?.orgPermission).toBe('royalty.view');
    expect(royalties?.orgModule).toBe('operational');
    const invoices = items.find((i) => i.path === '/billing/invoices');
    expect(invoices?.orgPermission).toBe('invoice.view');
  });

  it('hides org items when canAccessOrgModule returns false', () => {
    const raw = spaceNavSectionsFor('organization', { organizationId: 1 });
    const filtered = filterSpaceNavSections(raw, {
      hasStaffAccess: false,
      canAccessOrgModule: (module, perm) =>
        module === 'org_admin_basic' && perm === 'organization.view',
    });
    const paths = filtered.flatMap((s) => s.items.map((i) => i.path));
    expect(paths).toEqual(['/organizations/1']);
    expect(paths).not.toContain('/royalties');
    expect(paths).not.toContain('/reports');
  });

  it('hides OUT_OF_PRODUCT org commercial paths when product surface rejects personal space', () => {
    const raw = spaceNavSectionsFor('organization', { organizationId: 1 });
    const filtered = filterSpaceNavSections(raw, {
      hasStaffAccess: false,
      canAccessOrgModule: () => true,
      productSurface: {
        activeSpaceKind: 'personal',
        navCtx: { identityRole: 'user', presentationMode: false },
      },
    });
    const paths = filtered.flatMap((s) => s.items.map((i) => i.path));
    expect(paths).toContain('/organizations/1');
    expect(paths).toContain('/catalog');
    expect(paths).toContain('/artist-profiles');
    expect(paths).not.toContain('/campaigns');
    expect(paths).not.toContain('/billing/invoices');
    expect(paths).not.toContain('/subscriptions/overview');
  });

  it('keeps org commercial paths when organization space + product surface allow', () => {
    const raw = spaceNavSectionsFor('organization', { organizationId: 1 });
    const filtered = filterSpaceNavSections(raw, {
      hasStaffAccess: false,
      canAccessOrgModule: () => true,
      productSurface: {
        activeSpaceKind: 'organization',
        navCtx: { identityRole: 'user', presentationMode: false },
      },
    });
    const paths = filtered.flatMap((s) => s.items.map((i) => i.path));
    expect(paths).toContain('/campaigns');
    expect(paths).toContain('/billing/invoices');
    expect(paths).toContain('/subscriptions/overview');
  });

  it('hides operational catalog during onboarding-tier org access', () => {
    const raw = spaceNavSectionsFor('organization', { organizationId: 1 });
    const filtered = filterSpaceNavSections(raw, {
      hasStaffAccess: false,
      canAccessOrgModule: (module) => module === 'onboarding' || module === 'org_admin_basic',
      productSurface: {
        activeSpaceKind: 'organization',
        navCtx: { identityRole: 'user', presentationMode: false },
      },
    });
    const paths = filtered.flatMap((s) => s.items.map((i) => i.path));
    expect(paths).toContain('/organizations/1');
    expect(paths).toContain('/subscriptions/overview');
    expect(paths).not.toContain('/catalog');
    expect(paths).not.toContain('/artist-profiles');
    expect(paths).not.toContain('/campaigns');
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

  it('data ops nav includes ELT and explorer', () => {
    const paths = spaceNavSectionsFor('data_ops').flatMap((s) => s.items.map((i) => i.path));
    expect(paths).toContain('/elt-pipeline');
    expect(paths).toContain('/explorer');
  });

  it('platform admin lands on artist-requests and hides empty Ops dashboard from nav', () => {
    const paths = spaceNavSectionsFor('platform_admin').flatMap((s) =>
      s.items.map((i) => i.path),
    );
    expect(paths).toContain('/platform-ops/artist-requests');
    expect(paths).toContain('/platform-ops/audio-unresolved');
    expect(paths).toContain('/workpanel');
    expect(paths).toContain('/reports');
    expect(paths).toContain('/settings');
    expect(paths).not.toContain('/platform-ops');
    expect(paths).not.toContain('/users');
    expect(paths).not.toContain('/business');
    expect(paths).not.toContain('/subscriptions/plans');
  });

  it('assigns distinct typed icons per space (never a single shared default)', () => {
    const kinds = ['personal', 'organization', 'data_ops', 'platform_admin', 'artist'] as const;
    for (const kind of kinds) {
      const items = spaceNavSectionsFor(kind, { organizationId: 1 }).flatMap((s) => s.items);
      expect(items.length).toBeGreaterThan(1);
      expect(items.every((i) => !!i.iconId)).toBe(true);
      const markups = items.map((i) => spaceNavIconMarkup(i.iconId));
      expect(new Set(markups).size).toBeGreaterThan(1);
      expect(markups.every((m) => m === markups[0])).toBe(false);
    }
    // Catalog of glyph bodies must itself stay non-uniform.
    const allGlyphs = Object.values(SPACE_NAV_ICON_PATHS);
    expect(new Set(allGlyphs).size).toBe(allGlyphs.length);
  });

  it('artist nav is membership surface only (no royalties/billing)', () => {
    const paths = spaceNavSectionsFor('artist').flatMap((s) => s.items.map((i) => i.path));
    expect(paths).toEqual([
      '/artist-space',
      '/artist-space/profile',
      '/artist-space/tracks',
      '/artist-space/releases',
      '/artist-space/team',
    ]);
    expect(paths).not.toContain('/royalties');
    expect(paths).not.toContain('/billing/invoices');
    expect(paths).not.toContain('/settings');
  });
});
