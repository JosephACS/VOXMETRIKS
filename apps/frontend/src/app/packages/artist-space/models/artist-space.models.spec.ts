import { canAccessArtistPermission } from './artist-space.models';

describe('artist space permissions (046)', () => {
  it('owner permissions include team manage and profile update', () => {
    const perms = [
      'artist_space.view',
      'artist_space.profile.update',
      'artist_space.team.manage',
      'artist_space.access.review',
      'artist_space.invite',
    ];
    expect(canAccessArtistPermission(perms, 'artist_space.view')).toBe(true);
    expect(canAccessArtistPermission(perms, 'artist_space.team.manage')).toBe(true);
  });

  it('reader cannot manage team', () => {
    expect(canAccessArtistPermission(['artist_space.view'], 'artist_space.team.manage')).toBe(
      false,
    );
  });

  it('empty permissions deny all', () => {
    expect(canAccessArtistPermission([], 'artist_space.view')).toBe(false);
    expect(canAccessArtistPermission(null, 'artist_space.view')).toBe(false);
  });
});
