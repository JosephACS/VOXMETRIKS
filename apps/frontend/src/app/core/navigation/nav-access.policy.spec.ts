import {
  canActivateStaffPath,
  classifyProductDeepLink,
  filterMainNavItems,
  filterMusicNavItems,
  filterReportingNavItems,
  filterListenerLibraryItems,
  filterListenerAccountItems,
  hasEngineeringNavAccess,
  hasStaffReportsNavAccess,
  isOutOfProductPath,
  isProductFinalSection,
  resolveCanonicalRedirect,
  showAnalyticsSection,
  showPlatformOpsInPrimaryNav,
  showReportingSection,
} from './nav-access.policy';

describe('nav-access.policy', () => {
  const listener = { identityRole: 'user' as const };
  const admin = { identityRole: 'admin' as const };
  const engineer = { identityRole: 'engineer' as const };
  const platformAdmin = { identityRole: 'user' as const, platformAdmin: true };

  it('grants staff reports to admin/engineer/platform_admin only', () => {
    expect(hasStaffReportsNavAccess(listener)).toBe(false);
    expect(hasStaffReportsNavAccess(admin)).toBe(true);
    expect(hasStaffReportsNavAccess(engineer)).toBe(true);
    expect(hasStaffReportsNavAccess(platformAdmin)).toBe(true);
  });

  it('grants engineering nav to staff or platform_admin', () => {
    expect(hasEngineeringNavAccess(listener)).toBe(false);
    expect(hasEngineeringNavAccess(engineer)).toBe(true);
    expect(hasEngineeringNavAccess(platformAdmin)).toBe(true);
  });

  it('blocks listener deep links to workpanel and reports', () => {
    expect(canActivateStaffPath('/workpanel', listener)).toBe(false);
    expect(canActivateStaffPath('/simple-reports?report=x', listener)).toBe(false);
    expect(canActivateStaffPath('/complex-reports', listener)).toBe(false);
    expect(canActivateStaffPath('/dashboard', listener)).toBe(false);
    expect(canActivateStaffPath('/elt-pipeline', listener)).toBe(false);
  });

  it('allows listener music paths', () => {
    expect(canActivateStaffPath('/discover', listener)).toBe(true);
    expect(canActivateStaffPath('/search', listener)).toBe(true);
    expect(canActivateStaffPath('/playlists/7', listener)).toBe(true);
  });

  it('allows admin staff paths', () => {
    expect(canActivateStaffPath('/workpanel', admin)).toBe(true);
    expect(canActivateStaffPath('/simple-reports', admin)).toBe(true);
    expect(canActivateStaffPath('/explorer', admin)).toBe(true);
  });

  it('filters main nav by role (043)', () => {
    const items = [
      { path: '/discover' },
      { path: '/search' },
      { path: '/workpanel' },
      { path: '/elt-pipeline' },
      { path: '/dashboard' },
    ];
    expect(filterMainNavItems(items, listener).map((i) => i.path)).toEqual([
      '/discover',
      '/search',
    ]);
    expect(filterMainNavItems(items, admin).map((i) => i.path)).toEqual(['/workpanel']);
    expect(filterMainNavItems(items, engineer).map((i) => i.path)).toEqual([
      '/workpanel',
      '/elt-pipeline',
    ]);
  });

  it('hides audio-features for listeners', () => {
    const items = [
      { path: '/search' },
      { path: '/liked' },
      { path: '/audio-features' },
    ];
    expect(filterMusicNavItems(items, listener).map((i) => i.path)).toEqual([
      '/search',
      '/liked',
    ]);
    expect(filterMusicNavItems(items, engineer).map((i) => i.path)).toContain('/audio-features');
  });

  it('filters listener library and account (043)', () => {
    expect(
      filterListenerLibraryItems([
        { path: '/tracks' },
        { path: '/artists' },
        { path: '/liked' },
        { path: '/activity' },
      ]).map((i) => i.path),
    ).toEqual(['/tracks', '/liked', '/activity']);
    expect(
      filterListenerAccountItems([
        { path: '/settings' },
        { path: '/account/plans' },
        { path: '/account/billing' },
      ]).map((i) => i.path),
    ).toEqual(['/settings']);
  });

  it('hides analytics section and shows reporting for staff (038)', () => {
    expect(showAnalyticsSection(listener)).toBe(false);
    expect(showAnalyticsSection(admin)).toBe(false);
    expect(showReportingSection(listener)).toBe(false);
    expect(showReportingSection(engineer)).toBe(true);
  });

  it('hides platform ops from primary product nav (043)', () => {
    expect(showPlatformOpsInPrimaryNav(admin)).toBe(false);
    expect(showPlatformOpsInPrimaryNav({ ...admin, presentationMode: true })).toBe(true);
  });

  it('keeps activity visible for listeners', () => {
    const items = [
      { path: '/search' },
      { path: '/activity' },
      { path: '/audio-features' },
    ];
    expect(filterMusicNavItems(items, listener).map((i) => i.path)).toEqual([
      '/search',
      '/activity',
    ]);
  });

  it('marks demo enterprise paths as out of product', () => {
    expect(isOutOfProductPath('/crm/prospects')).toBe(true);
    expect(isOutOfProductPath('/billing/invoices')).toBe(true);
    expect(isOutOfProductPath('/simple-reports')).toBe(false);
    expect(isOutOfProductPath('/reports')).toBe(false);
    expect(isOutOfProductPath('/workpanel')).toBe(false);
  });

  it('classifies demo deep links as unavailable for product users', () => {
    expect(classifyProductDeepLink('/crm/dashboard', admin)).toBe('unavailable');
    expect(classifyProductDeepLink('/workpanel', listener)).toBe('staff-block');
    expect(classifyProductDeepLink('/workpanel', admin)).toBe('allow');
    expect(
      classifyProductDeepLink('/crm/dashboard', { ...admin, presentationMode: true }),
    ).toBe('allow');
  });

  it('resolves canonical redirects for legacy hubs', () => {
    expect(resolveCanonicalRedirect('/dashboard')).toBe('/workpanel');
    expect(resolveCanonicalRedirect('/analytics')).toBe('/workpanel');
    expect(resolveCanonicalRedirect('/trending')).toBe('/reports?type=complex');
    expect(resolveCanonicalRedirect('/discover')).toBeNull();
  });

  it('filters reporting nav to hub (043)', () => {
    const items = [
      { path: '/reports' },
      { path: '/simple-reports' },
      { path: '/complex-reports' },
      { path: '/business-decisions' },
    ];
    expect(filterReportingNavItems(items, admin).map((i) => i.path)).toEqual(['/reports']);
  });

  it('keeps product-final sections only', () => {
    expect(isProductFinalSection('crm', admin)).toBe(false);
    expect(isProductFinalSection('reporting', admin)).toBe(true);
    expect(isProductFinalSection('catalogHub', admin)).toBe(true);
    expect(isProductFinalSection('music', listener)).toBe(true);
  });
});
