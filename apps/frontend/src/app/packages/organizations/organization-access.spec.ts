import {
  canAccessOrganizationModule,
  resolveOrgAccessTier,
} from './organization-access';

describe('organization-access', () => {
  const membership = {
    active: true,
    permissions: ['organization.view', 'royalty.view', 'invoice.view'],
  };

  it('denies unauthenticated users', () => {
    expect(
      canAccessOrganizationModule({
        authenticated: false,
        membership,
        organizationSubscription: { has_subscription: true, status: 'active', access_state: 'full' },
        moduleKind: 'operational',
        requiredPermission: 'royalty.view',
      }),
    ).toBe(false);
  });

  it('denies listeners without membership', () => {
    expect(
      canAccessOrganizationModule({
        authenticated: true,
        membership: null,
        organizationSubscription: null,
        moduleKind: 'operational',
      }),
    ).toBe(false);
  });

  it('allows onboarding modules without a subscription', () => {
    expect(resolveOrgAccessTier({ has_subscription: false, status: null, access_state: null })).toBe(
      'onboarding',
    );
    expect(
      canAccessOrganizationModule({
        authenticated: true,
        membership,
        organizationSubscription: { has_subscription: false, status: null, access_state: null },
        moduleKind: 'onboarding',
        requiredPermission: 'organization.view',
      }),
    ).toBe(true);
    expect(
      canAccessOrganizationModule({
        authenticated: true,
        membership,
        organizationSubscription: { has_subscription: false, status: null, access_state: null },
        moduleKind: 'operational',
        requiredPermission: 'royalty.view',
      }),
    ).toBe(false);
  });

  it('allows operational modules for active/trialing full access', () => {
    expect(
      canAccessOrganizationModule({
        authenticated: true,
        membership,
        organizationSubscription: {
          has_subscription: true,
          status: 'trialing',
          access_state: 'full',
        },
        moduleKind: 'operational',
        requiredPermission: 'royalty.view',
      }),
    ).toBe(true);
  });

  it('limits past_due to recovery modules', () => {
    const sub = { has_subscription: true, status: 'past_due', access_state: 'limited' };
    expect(resolveOrgAccessTier(sub)).toBe('recovery');
    expect(
      canAccessOrganizationModule({
        authenticated: true,
        membership,
        organizationSubscription: sub,
        moduleKind: 'recovery',
        requiredPermission: 'invoice.view',
      }),
    ).toBe(true);
    expect(
      canAccessOrganizationModule({
        authenticated: true,
        membership,
        organizationSubscription: sub,
        moduleKind: 'operational',
        requiredPermission: 'royalty.view',
      }),
    ).toBe(false);
  });

  it('requires permission when provided', () => {
    expect(
      canAccessOrganizationModule({
        authenticated: true,
        membership,
        organizationSubscription: {
          has_subscription: true,
          status: 'active',
          access_state: 'full',
        },
        moduleKind: 'operational',
        requiredPermission: 'campaign.manage',
      }),
    ).toBe(false);
  });
});
