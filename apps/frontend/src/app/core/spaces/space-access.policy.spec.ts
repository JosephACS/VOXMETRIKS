import {
  buildAvailableSpaces,
  findSpaceById,
  isOrganizationSpaceCommercialPath,
  isPersistedSpaceStillValid,
  spaceAllowsProductPath,
  toPersistedRef,
} from './space-access.policy';
import { organizationSpace, personalSpace, SPACE_STORAGE_KEY } from './space.models';

describe('space-access.policy (045)', () => {
  it('always includes Personal for authenticated users', () => {
    const spaces = buildAvailableSpaces({
      authenticated: true,
      identityRole: 'user',
      hasEngineerAccess: false,
      hasPlatformAdminSpace: false,
      organizations: [],
      artistMemberships: [],
    });
    expect(spaces.map((s) => s.id)).toEqual(['personal']);
  });

  it('adds one organization space per membership', () => {
    const spaces = buildAvailableSpaces({
      authenticated: true,
      identityRole: 'user',
      hasEngineerAccess: false,
      hasPlatformAdminSpace: false,
      organizations: [
        { id: 1, name: 'Sello A' },
        { id: 2, name: 'Sello B' },
      ],
      artistMemberships: [],
    });
    expect(spaces.map((s) => s.id)).toEqual(['personal', 'org:1', 'org:2']);
    expect(spaces[1].label).toBe('Sello A');
  });

  it('adds Data Ops only with engineer access', () => {
    const listener = buildAvailableSpaces({
      authenticated: true,
      identityRole: 'user',
      hasEngineerAccess: false,
      hasPlatformAdminSpace: false,
      organizations: [],
      artistMemberships: [],
    });
    const engineer = buildAvailableSpaces({
      authenticated: true,
      identityRole: 'engineer',
      hasEngineerAccess: true,
      hasPlatformAdminSpace: false,
      organizations: [],
      artistMemberships: [],
    });
    expect(listener.some((s) => s.kind === 'data_ops')).toBe(false);
    expect(engineer.some((s) => s.kind === 'data_ops')).toBe(true);
  });

  it('adds platform admin space for identity admin or CRM platform_admin, not pure engineer', () => {
    const admin = buildAvailableSpaces({
      authenticated: true,
      identityRole: 'admin',
      hasEngineerAccess: true,
      hasPlatformAdminSpace: true,
      organizations: [],
      artistMemberships: [],
    });
    expect(admin.some((s) => s.kind === 'platform_admin')).toBe(true);

    const engineerOnly = buildAvailableSpaces({
      authenticated: true,
      identityRole: 'engineer',
      hasEngineerAccess: true,
      hasPlatformAdminSpace: false,
      organizations: [],
      artistMemberships: [],
    });
    expect(engineerOnly.some((s) => s.kind === 'data_ops')).toBe(true);
    expect(engineerOnly.some((s) => s.kind === 'platform_admin')).toBe(false);
  });

  it('never invents artist spaces when memberships are empty', () => {
    const spaces = buildAvailableSpaces({
      authenticated: true,
      identityRole: 'admin',
      hasEngineerAccess: true,
      hasPlatformAdminSpace: true,
      organizations: [{ id: 9, name: 'Org' }],
      artistMemberships: [],
    });
    expect(spaces.some((s) => s.kind === 'artist')).toBe(false);
  });

  it('includes artist spaces only when real memberships are provided', () => {
    const spaces = buildAvailableSpaces({
      authenticated: true,
      identityRole: 'user',
      hasEngineerAccess: false,
      hasPlatformAdminSpace: false,
      organizations: [],
      artistMemberships: [{ id: 44, name: 'Artista X' }],
    });
    expect(spaces.some((s) => s.id === 'artist:44')).toBe(true);
  });

  it('invalidates persisted org space after membership revoked', () => {
    const available = [personalSpace(), organizationSpace(1, 'A')];
    const ok = isPersistedSpaceStillValid(
      { id: 'org:1', kind: 'organization', organizationId: 1 },
      available,
    );
    expect(ok?.id).toBe('org:1');

    const revoked = isPersistedSpaceStillValid(
      { id: 'org:99', kind: 'organization', organizationId: 99 },
      available,
    );
    expect(revoked).toBeNull();
  });

  it('findSpaceById returns null for unknown ids', () => {
    expect(findSpaceById([personalSpace()], 'org:1')).toBeNull();
  });

  it('toPersistedRef keeps org id', () => {
    expect(toPersistedRef(organizationSpace(7, 'X'))).toEqual({
      id: 'org:7',
      kind: 'organization',
      organizationId: 7,
      artistProfileId: undefined,
    });
  });

  it('allows org commercial paths only in organization space', () => {
    expect(isOrganizationSpaceCommercialPath('/campaigns/1')).toBe(true);
    expect(spaceAllowsProductPath('/business-analytics', 'organization')).toBe(true);
    expect(spaceAllowsProductPath('/reports', 'organization')).toBe(true);
    expect(spaceAllowsProductPath('/business-decisions/7', 'organization')).toBe(true);
    expect(spaceAllowsProductPath('/billing/invoices', 'organization')).toBe(true);
    expect(spaceAllowsProductPath('/billing/invoices', 'personal')).toBe(false);
    expect(spaceAllowsProductPath('/platform-ops', 'platform_admin')).toBe(true);
    expect(spaceAllowsProductPath('/elt-pipeline', 'data_ops')).toBe(true);
    expect(spaceAllowsProductPath('/elt-pipeline', 'personal')).toBe(false);
  });

  it('storage key is stable', () => {
    expect(SPACE_STORAGE_KEY).toBe('voxmetriks_active_space_v1');
  });
});
