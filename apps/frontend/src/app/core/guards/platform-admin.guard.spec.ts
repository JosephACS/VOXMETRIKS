import { canAccessPlatformAdmin } from './platform-admin.policy';

describe('canAccessPlatformAdmin (045)', () => {
  it('allows identity admin', () => {
    expect(canAccessPlatformAdmin({ isAdmin: true, crmRoles: [] })).toBe(true);
  });

  it('allows CRM platform_admin without identity admin', () => {
    expect(
      canAccessPlatformAdmin({ isAdmin: false, crmRoles: ['platform_admin'] }),
    ).toBe(true);
  });

  it('blocks pure engineer (Data Ops only)', () => {
    expect(canAccessPlatformAdmin({ isAdmin: false, crmRoles: [] })).toBe(false);
  });

  it('blocks normal user', () => {
    expect(canAccessPlatformAdmin({ isAdmin: false, crmRoles: ['sales_agent'] })).toBe(
      false,
    );
  });
});
