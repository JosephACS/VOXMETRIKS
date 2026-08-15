import { filterSpaceNavSections, spaceNavSectionsFor } from './space-nav.config';

/**
 * 051 · T004 — Artist Space nav mirrors the server permission manifest
 * (GET /artist-space/mine) instead of showing every surface to every role.
 */
describe('artist space nav permissions (051)', () => {
  function paths(permissions: string[] | null): string[] {
    const raw = spaceNavSectionsFor('artist');
    return filterSpaceNavSections(raw, {
      hasStaffAccess: false,
      canAccessOrgModule: () => true,
      canAccessArtistPermission: permissions
        ? (permission) => permissions.includes(permission)
        : undefined,
    }).flatMap((section) => section.items.map((item) => item.path));
  }

  it('shows the consolidated Music surface to members with catalog access', () => {
    const visible = paths(['artist_space.view', 'artist_space.catalog.view']);
    expect(visible).toContain('/artist-space');
    expect(visible).toContain('/artist-space/profile');
    expect(visible).toContain('/artist-space/music');
    expect(visible).toContain('/artist-space/team');
  });

  it('hides Music when the manifest does not grant catalog.view', () => {
    const visible = paths(['artist_space.view']);
    expect(visible).toContain('/artist-space/profile');
    expect(visible).not.toContain('/artist-space/music');
  });

  it('keeps artist-gated items hidden when no manifest is loaded', () => {
    const visible = paths(null);
    expect(visible).toEqual(['/artist-space']);
  });

  it('drops the legacy split tracks/releases entries', () => {
    const declared = spaceNavSectionsFor('artist').flatMap((s) => s.items.map((i) => i.path));
    expect(declared).not.toContain('/artist-space/tracks');
    expect(declared).not.toContain('/artist-space/releases');
  });
});
