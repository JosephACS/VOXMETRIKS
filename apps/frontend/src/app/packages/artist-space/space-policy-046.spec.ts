import { buildAvailableSpaces } from '../../core/spaces/space-access.policy';
import { evaluateProductPathAccess, emptyProductSurfaceContext } from '../../core/product-surface';

describe('space policy artist memberships (046)', () => {
  it('never invents artist spaces without memberships', () => {
    const spaces = buildAvailableSpaces({
      authenticated: true,
      identityRole: 'user',
      hasEngineerAccess: false,
      hasPlatformAdminSpace: false,
      organizations: [],
      artistMemberships: [],
    });
    expect(spaces.every((s) => s.kind !== 'artist')).toBe(true);
  });

  it('lists artist spaces only from real memberships', () => {
    const spaces = buildAvailableSpaces({
      authenticated: true,
      identityRole: 'user',
      hasEngineerAccess: false,
      hasPlatformAdminSpace: false,
      organizations: [],
      artistMemberships: [{ id: 12, name: 'Real Act' }],
    });
    const artist = spaces.find((s) => s.kind === 'artist');
    expect(artist?.id).toBe('artist:12');
    expect(artist?.artistProfileId).toBe(12);
  });

  it('allows artist-space paths in artist product surface via registry', () => {
    const ctx = {
      ...emptyProductSurfaceContext('artist'),
      ready: true,
      artistCapabilities: new Set(['artist_space.view']),
    };
    expect(evaluateProductPathAccess('/artist-space', ctx)).toBe('allow');
    expect(evaluateProductPathAccess('/artist-space/team', ctx)).toBe('allow');
    expect(evaluateProductPathAccess('/royalties', ctx)).toBe('unavailable');
  });
});
