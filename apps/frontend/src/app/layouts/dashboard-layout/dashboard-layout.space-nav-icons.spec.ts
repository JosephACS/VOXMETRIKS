import { SPACE_NAV_ICON_IDS, SPACE_NAV_ICON_PATHS, spaceNavIconMarkup } from '../../core/spaces/space-nav.icons';
import { spaceNavSectionsFor } from '../../core/spaces/space-nav.config';

/**
 * Layout maps SpaceNavItem.iconId → SVG via spaceNavIconMarkup.
 * Guards against regressing to a single defaultIcon for every item.
 */
describe('dashboard space nav icons', () => {
  it('resolves a unique glyph for every registered icon id', () => {
    const rendered = SPACE_NAV_ICON_IDS.map((id) => spaceNavIconMarkup(id));
    expect(rendered.every((svg) => typeof svg === 'string' && svg.length > 0)).toBe(true);
    expect(new Set(rendered).size).toBe(SPACE_NAV_ICON_IDS.length);
    expect(Object.keys(SPACE_NAV_ICON_PATHS).sort()).toEqual([...SPACE_NAV_ICON_IDS].sort());
  });

  it('maps contextual nav items to distinct icons (personal + platform samples)', () => {
    const personal = spaceNavSectionsFor('personal').flatMap((s) => s.items);
    const personalIcons = personal.map((i) => spaceNavIconMarkup(i.iconId));
    expect(personalIcons).toContain(spaceNavIconMarkup('home'));
    expect(personalIcons).toContain(spaceNavIconMarkup('search'));
    expect(personalIcons).toContain(spaceNavIconMarkup('settings'));
    expect(new Set(personalIcons).size).toBeGreaterThan(1);

    const platform = spaceNavSectionsFor('platform_admin').flatMap((s) => s.items);
    const platformIcons = platform.map((i) => spaceNavIconMarkup(i.iconId));
    expect(platformIcons).toContain(spaceNavIconMarkup('artist_requests'));
    expect(platformIcons).toContain(spaceNavIconMarkup('unresolved_audio'));
    expect(platformIcons).toContain(spaceNavIconMarkup('workpanel'));
    expect(platformIcons).toContain(spaceNavIconMarkup('reports'));
    expect(new Set(platformIcons).size).toBe(platformIcons.length);
  });
});
