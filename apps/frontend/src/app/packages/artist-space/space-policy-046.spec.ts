import { buildAvailableSpaces, spaceAllowsProductPath } from '../../core/spaces/space-access.policy';

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

  it('allows artist-space paths in artist product surface', () => {
    expect(spaceAllowsProductPath('/artist-space', 'artist')).toBe(true);
    expect(spaceAllowsProductPath('/artist-space/team', 'artist')).toBe(true);
    expect(spaceAllowsProductPath('/royalties', 'artist')).toBe(false);
  });
});
