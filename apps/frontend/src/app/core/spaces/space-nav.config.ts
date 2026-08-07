/**
 * Navigation items per product space (045).
 * Only maps to routes that already exist in the app.
 * Organization items declare the SAME moduleKind + permission used by route guards.
 */

import { OrgModuleKind } from '../../packages/organizations/organization-access';
import { SpaceKind } from './space.models';

export interface SpaceNavItem {
  path: string;
  labelKey: string;
  exact?: boolean;
  /**
   * Org RBAC gate mirroring route guards (organizationModuleGuard).
   * When set, the item is hidden unless canAccessOrganizationModule passes.
   */
  orgModule?: OrgModuleKind;
  /** Optional permission code — must exist in backend/FE catalogs; never invent. */
  orgPermission?: string;
  /** When true, hide unless identity staff (admin|engineer) or platform_admin. */
  requireStaff?: boolean;
}

export interface SpaceNavSection {
  id: string;
  titleKey: string;
  items: SpaceNavItem[];
}

export interface SpaceNavFilterContext {
  canAccessOrgModule: (
    moduleKind: OrgModuleKind,
    requiredPermission?: string | null,
  ) => boolean;
  hasStaffAccess: boolean;
}

/** Filter nav items using real org/staff gates (UX only; backend remains authority). */
export function filterSpaceNavSections(
  sections: SpaceNavSection[],
  ctx: SpaceNavFilterContext,
): SpaceNavSection[] {
  return sections
    .map((section) => ({
      ...section,
      items: section.items.filter((item) => {
        if (item.requireStaff && !ctx.hasStaffAccess) return false;
        if (item.orgModule) {
          return ctx.canAccessOrgModule(item.orgModule, item.orgPermission ?? null);
        }
        return true;
      }),
    }))
    .filter((s) => s.items.length > 0);
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
            {
              path: '/artist-space/claim',
              labelKey: 'artistSpace.claim.title',
              exact: true,
            },
            { path: '/settings', labelKey: 'nav.settings', exact: true },
          ],
        },
      ];
    case 'organization': {
      const orgId = opts?.organizationId;
      const hub = orgId != null ? `/organizations/${orgId}` : '/organizations/none';
      // Permission codes taken from *.routes.ts organizationModuleGuard(...) only.
      return [
        {
          id: 'space-org-main',
          titleKey: 'spaces.nav.group.main',
          items: [
            {
              path: hub,
              labelKey: 'spaces.nav.org.summary',
              exact: true,
              orgModule: 'org_admin_basic',
              orgPermission: 'organization.view',
            },
            {
              path: '/artist-profiles',
              labelKey: 'nav.artistProfiles.list',
              exact: false,
              orgModule: 'operational',
              // Route: organizationModuleGuard('operational') — no permission code on route.
            },
            {
              path: '/catalog',
              labelKey: 'nav.catalogHub',
              exact: true,
              orgModule: 'operational',
            },
            {
              path: '/artist/releases',
              labelKey: 'nav.catalogRights.releases',
              exact: false,
              orgModule: 'operational',
            },
            {
              path: '/campaigns',
              labelKey: 'nav.campaigns.list',
              exact: false,
              orgModule: 'operational',
              // Route has no campaign.* permission — tier-only, same as campaigns.routes.ts.
            },
            {
              path: '/catalog-rights/contracts',
              labelKey: 'nav.catalogRights.contracts',
              exact: false,
              orgModule: 'operational',
            },
            {
              path: '/royalties',
              labelKey: 'nav.royalties.dashboard',
              exact: false,
              orgModule: 'operational',
              orgPermission: 'royalty.view',
            },
            {
              path: `${hub}/members`,
              labelKey: 'spaces.nav.org.team',
              exact: true,
              orgModule: 'org_admin_advanced',
              orgPermission: 'member.view',
            },
            {
              path: '/reports',
              labelKey: 'spaces.nav.reports',
              exact: true,
              requireStaff: true,
              // /reports uses staffCapabilityGuard — not org RBAC.
            },
            {
              path: '/subscriptions/overview',
              labelKey: 'nav.subscriptions.overview',
              exact: true,
              orgModule: 'onboarding',
              orgPermission: 'subscription.view',
            },
            {
              path: '/billing/invoices',
              labelKey: 'nav.billing.invoices',
              exact: false,
              orgModule: 'recovery',
              orgPermission: 'invoice.view',
            },
          ],
        },
      ];
    }
    case 'data_ops':
      // hasEngineerAccess() today = identity admin OR engineer (see AuthService).
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
      // Only surfaces that exist and match the label. No /users (profile) or /business (marketing).
      return [
        {
          id: 'space-platform',
          titleKey: 'spaces.nav.group.platform',
          items: [
            { path: '/platform-ops', labelKey: 'nav.platformOps.dashboard', exact: false },
            {
              path: '/platform-ops/artist-requests',
              labelKey: 'nav.platformOps.artistRequests',
              exact: true,
            },
            {
              path: '/platform-ops/audio-unresolved',
              labelKey: 'nav.platformOps.audioUnresolved',
              exact: true,
            },
            { path: '/workpanel', labelKey: 'nav.workpanel', exact: true },
            { path: '/reports', labelKey: 'spaces.nav.reports', exact: true },
            { path: '/settings', labelKey: 'nav.settings', exact: true },
          ],
        },
      ];
    case 'artist':
      // Spec 046 — membership-backed Artist Space only (no royalties/billing/plan/ads).
      return [
        {
          id: 'space-artist',
          titleKey: 'spaces.nav.group.artist',
          items: [
            { path: '/artist-space', labelKey: 'spaces.nav.artist.summary', exact: true },
            { path: '/artist-space/profile', labelKey: 'spaces.nav.artist.profile', exact: true },
            { path: '/artist-space/tracks', labelKey: 'spaces.nav.artist.tracks', exact: false },
            {
              path: '/artist-space/releases',
              labelKey: 'spaces.nav.artist.releases',
              exact: false,
            },
            { path: '/artist-space/team', labelKey: 'spaces.nav.artist.team', exact: true },
          ],
        },
      ];
    default:
      return [];
  }
}
