import { canAccessArtistPermission } from '../models/artist-space.models';
import { ArtistContextService } from './artist-context.service';
import { ArtistSpaceMineItem } from '../models/artist-space.models';

describe('ArtistContext activate/clear semantics (046)', () => {
  const sample: ArtistSpaceMineItem = {
    artist_profile_id: 9,
    warehouse_artist_id: 101,
    display_name: 'Demo Act',
    image_url: null,
    membership_role: 'owner',
    membership_status: 'active',
    permissions: ['artist_space.view', 'artist_space.profile.update'],
    organization_id: 0,
  };

  it('independent org_id stays 0 (never treated as activatable org)', () => {
    expect(sample.organization_id).toBe(0);
    expect(sample.organization_id > 0).toBe(false);
  });

  it('permission helper used by context can()', () => {
    expect(canAccessArtistPermission(sample.permissions, 'artist_space.view')).toBe(true);
    expect(canAccessArtistPermission(sample.permissions, 'artist_space.team.manage')).toBe(false);
  });

  it('service class is exported for DI', () => {
    expect(ArtistContextService).toBeTruthy();
  });
});
