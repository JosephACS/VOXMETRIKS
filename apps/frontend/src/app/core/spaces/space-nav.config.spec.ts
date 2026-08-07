import {
  filterSpaceNavSections,
  spaceNavSectionsFor,
} from './space-nav.config';
import {
  homePathForSpace,
  personalSpace,
  organizationSpace,
  dataOpsSpace,
  artistSpace,
} from './space.models';

describe('space models & nav (045/046)', () => {
  it('maps home paths per space kind', () => {
    expect(homePathForSpace(personalSpace())).toBe('/discover');
    expect(homePathForSpace(organizationSpace(3, 'Org'))).toBe('/organizations/3');
    expect(homePathForSpace(dataOpsSpace())).toBe('/elt-pipeline');
    expect(homePathForSpace(artistSpace(7, 'Act'))).toBe('/artist-space');
  });

  it('personal nav includes library activity without audio-features', () => {
    const paths = spaceNavSectionsFor('personal').flatMap((s) => s.items.map((i) => i.path));
    expect(paths).toContain('/discover');
    expect(paths).toContain('/activity');
    expect(paths).not.toContain('/audio-features');
    expect(paths).not.toContain('/recommendations');
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

  it('platform admin nav excludes /users profile and /business marketing', () => {
    const paths = spaceNavSectionsFor('platform_admin').flatMap((s) =>
      s.items.map((i) => i.path),
    );
    expect(paths).toContain('/platform-ops');
    expect(paths).toContain('/platform-ops/artist-requests');
    expect(paths).toContain('/workpanel');
    expect(paths).not.toContain('/users');
    expect(paths).not.toContain('/business');
    expect(paths).not.toContain('/subscriptions/plans');
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
