/**
 * Navigation items per product space (045).
 * Only maps to routes that already exist in the app.
 */

import { SpaceKind } from './space.models';

export interface SpaceNavItem {
  path: string;
  labelKey: string;
  exact?: boolean;
}

export interface SpaceNavSection {
  id: string;
  titleKey: string;
  items: SpaceNavItem[];
}

/** Icons reused as inline SVG paths from layout — layout resolves icons by path. */
export function spaceNavSectionsFor(
  kind: SpaceKind,
  opts?: { organizationId?: number | null },
): SpaceNavSection[] {
  switch (kind) {
    case 'personal':
      return [
        {
          id: 'space-main',
          titleKey: 'spaces.nav.group.main',
          items: [
            { path: '/discover', labelKey: 'nav.home', exact: true },
            { path: '/search', labelKey: 'nav.search', exact: true },
          ],
        },
        {
          id: 'space-library',
          titleKey: 'spaces.nav.group.library',
          items: [
            { path: '/liked', labelKey: 'nav.liked', exact: true },
            { path: '/playlists', labelKey: 'nav.playlists', exact: false },
            { path: '/activity', labelKey: 'nav.activity', exact: true },
          ],
        },
        {
          id: 'space-account',
          titleKey: 'spaces.nav.group.account',
          items: [
            { path: '/account/plans', labelKey: 'nav.personal.plans', exact: true },
            { path: '/account/subscription', labelKey: 'nav.personal.subscription', exact: true },
            { path: '/settings', labelKey: 'nav.settings', exact: true },
          ],
        },
      ];
    case 'organization': {
      const orgId = opts?.organizationId;
      const hub = orgId != null ? `/organizations/${orgId}` : '/organizations/none';
      return [
        {
          id: 'space-org-main',
          titleKey: 'spaces.nav.group.main',
          items: [
            { path: hub, labelKey: 'spaces.nav.org.summary', exact: true },
            { path: '/artist-profiles', labelKey: 'nav.artistProfiles.list', exact: false },
            { path: '/catalog', labelKey: 'nav.catalogHub', exact: true },
            { path: '/artist/releases', labelKey: 'nav.catalogRights.releases', exact: false },
            { path: '/campaigns', labelKey: 'nav.campaigns.list', exact: false },
            { path: '/catalog-rights/contracts', labelKey: 'nav.catalogRights.contracts', exact: false },
            { path: '/royalties', labelKey: 'nav.royalties.dashboard', exact: false },
            { path: `${hub}/members`, labelKey: 'spaces.nav.org.team', exact: true },
            { path: '/reports', labelKey: 'spaces.nav.reports', exact: true },
            { path: '/subscriptions/overview', labelKey: 'nav.subscriptions.overview', exact: true },
            { path: '/billing/invoices', labelKey: 'nav.billing.invoices', exact: false },
          ],
        },
      ];
    }
    case 'data_ops':
      return [
        {
          id: 'space-data',
          titleKey: 'spaces.nav.group.dataOps',
          items: [
            { path: '/elt-pipeline', labelKey: 'spaces.nav.data.summary', exact: true },
            { path: '/explorer', labelKey: 'nav.explorer', exact: true },
            { path: '/workpanel', labelKey: 'nav.workpanel', exact: true },
            { path: '/complex-reports', labelKey: 'spaces.nav.reports', exact: true },
            { path: '/settings', labelKey: 'nav.settings', exact: true },
          ],
        },
      ];
    case 'platform_admin':
      return [
        {
          id: 'space-platform',
          titleKey: 'spaces.nav.group.platform',
          items: [
            { path: '/platform-ops', labelKey: 'nav.platformOps.dashboard', exact: false },
            { path: '/users', labelKey: 'nav.userInsights', exact: true },
            { path: '/business', labelKey: 'spaces.nav.platform.orgs', exact: true },
            { path: '/subscriptions/plans', labelKey: 'nav.subscriptions.plans', exact: false },
            { path: '/workpanel', labelKey: 'nav.workpanel', exact: true },
            { path: '/reports', labelKey: 'spaces.nav.reports', exact: true },
            { path: '/settings', labelKey: 'nav.settings', exact: true },
          ],
        },
      ];
    case 'artist':
      // Prepared structure — space not listed until artist membership API exists.
      return [
        {
          id: 'space-artist',
          titleKey: 'spaces.nav.group.artist',
          items: [
            { path: '/artist/profile', labelKey: 'nav.artist.profile', exact: true },
            { path: '/artist/tracks', labelKey: 'nav.artist.tracks', exact: false },
            { path: '/artist/releases', labelKey: 'nav.artist.releases', exact: false },
            { path: '/royalties', labelKey: 'nav.royalties.dashboard', exact: false },
            { path: '/settings', labelKey: 'nav.settings', exact: true },
          ],
        },
      ];
    default:
      return [];
  }
}
