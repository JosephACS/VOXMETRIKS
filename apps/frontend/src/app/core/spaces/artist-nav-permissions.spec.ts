import { filterSpaceNavSections, spaceNavSectionsFor } from './space-nav.config';
import type { ProductSurfaceContext } from '../product-surface';

/**
 * 051 / 054 — Artist Space nav mirrors the server permission manifest.
 */
describe('artist space nav permissions (051/054)', () => {
  function paths(permissions: string[] | null): string[] {
    const raw = spaceNavSectionsFor('artist');
    const access: ProductSurfaceContext = {
      ready: true,
      activeSpace: 'artist',
      permissions: new Set(),
      artistCapabilities: new Set(permissions ?? []),
      staffCapabilities: new Set(),
      platformRoles: new Set(),
    };
    return filterSpaceNavSections(raw, {
      productSurfaceContext: access,
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
