/**
 * Navigation items per product space (045).
 * Only maps to routes that already exist in the app.
 * Organization items declare the SAME moduleKind + permission used by route guards.
 */

import { OrgModuleKind } from '../../packages/organizations/organization-access';
import { decideProductSurfaceAccess } from '../guards/product-surface.policy';
import type { NavAccessContext } from '../navigation/nav-access.policy';
import { SpaceKind } from './space.models';
import { SpaceNavIconId } from './space-nav.icons';

export interface SpaceNavItem {
  path: string;
  labelKey: string;
  /** Deterministic shell icon — never share one default across all items. */
  iconId: SpaceNavIconId;
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
  /**
   * Same product-surface decision used by productSurfaceGuard.
   * Required for org commercial paths that are OUT_OF_PRODUCT outside organization space.
   */
  productSurface?: {
    navCtx: NavAccessContext;
    activeSpaceKind: SpaceKind | null | undefined;
  };
}

/**
 * Single announce gate aligned with route guards:
 * org RBAC (organizationModuleGuard) + product surface (productSurfaceGuard).
 */
export function canAnnounceSpaceNavItem(
  item: SpaceNavItem,
  ctx: SpaceNavFilterContext,
): boolean {
  if (item.requireStaff && !ctx.hasStaffAccess) return false;
  if (item.orgModule) {
    if (!ctx.canAccessOrgModule(item.orgModule, item.orgPermission ?? null)) {
      return false;
    }
  }
  if (ctx.productSurface) {
    const verdict = decideProductSurfaceAccess(
      item.path,
      ctx.productSurface.navCtx,
      ctx.productSurface.activeSpaceKind,
    );
    if (verdict !== 'allow') return false;
  }
  return true;
}

/** Filter nav items using real org/staff/product-surface gates (UX only; backend remains authority). */
export function filterSpaceNavSections(
  sections: SpaceNavSection[],
  ctx: SpaceNavFilterContext,
): SpaceNavSection[] {
  return sections
    .map((section) => ({
      ...section,
      items: section.items.filter((item) => canAnnounceSpaceNavItem(item, ctx)),
    }))
    .filter((s) => s.items.length > 0);
}

/** Icons reused as inline SVG paths from layout — layout resolves icons by iconId. */
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
            { path: '/discover', labelKey: 'nav.home', iconId: 'home', exact: true },
            { path: '/search', labelKey: 'nav.search', iconId: 'search', exact: true },
          ],
        },
        {
          id: 'space-library',
          titleKey: 'spaces.nav.group.library',
          items: [
            { path: '/liked', labelKey: 'nav.liked', iconId: 'liked', exact: true },
            { path: '/playlists', labelKey: 'nav.playlists', iconId: 'playlists', exact: false },
            { path: '/activity', labelKey: 'nav.activity', iconId: 'activity', exact: true },
          ],
        },
        {
          id: 'space-account',
          titleKey: 'spaces.nav.group.account',
          items: [
            {
              path: '/account/plans',
              labelKey: 'nav.personal.plans',
              iconId: 'plans',
              exact: true,
            },
            {
              path: '/account/subscription',
              labelKey: 'nav.personal.subscription',
              iconId: 'account',
              exact: true,
            },
            {
              path: '/artist-space/claim',
              labelKey: 'spaces.nav.artist.claimShort',
              iconId: 'artist',
              exact: true,
            },
            { path: '/settings', labelKey: 'nav.settings', iconId: 'settings', exact: true },
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
              iconId: 'organization',
              exact: true,
              orgModule: 'org_admin_basic',
              orgPermission: 'organization.view',
            },
            {
              path: '/artist-profiles',
              labelKey: 'nav.artistProfiles.list',
              iconId: 'artist',
              exact: false,
              orgModule: 'operational',
              // Route: organizationModuleGuard('operational') — no permission code on route.
            },
            {
              path: '/catalog',
              labelKey: 'nav.catalogHub',
              iconId: 'catalog',
              exact: true,
              orgModule: 'operational',
            },
            {
              path: '/artist/releases',
              labelKey: 'nav.catalogRights.releases',
              iconId: 'playlists',
              exact: false,
              orgModule: 'operational',
            },
            {
              path: '/campaigns',
              labelKey: 'nav.campaigns.list',
              iconId: 'campaigns',
              exact: false,
              orgModule: 'operational',
              // Route has no campaign.* permission — tier-only, same as campaigns.routes.ts.
            },
            {
              path: '/catalog-rights/contracts',
              labelKey: 'nav.catalogRights.contracts',
              iconId: 'contracts',
              exact: false,
              orgModule: 'operational',
            },
            {
              path: '/royalties',
              labelKey: 'nav.royalties.dashboard',
              iconId: 'billing',
              exact: false,
              orgModule: 'operational',
              orgPermission: 'royalty.view',
            },
            {
              path: `${hub}/members`,
              labelKey: 'spaces.nav.org.team',
              iconId: 'team',
              exact: true,
              orgModule: 'org_admin_advanced',
              orgPermission: 'member.view',
            },
            {
              path: '/reports',
              labelKey: 'spaces.nav.reports',
              iconId: 'reports',
              exact: true,
              requireStaff: true,
              // /reports uses staffCapabilityGuard — not org RBAC.
            },
            {
              path: '/subscriptions/overview',
              labelKey: 'nav.subscriptions.overview',
              iconId: 'plans',
              exact: true,
              orgModule: 'onboarding',
              orgPermission: 'subscription.view',
            },
            {
              path: '/billing/invoices',
              labelKey: 'nav.billing.invoices',
              iconId: 'billing',
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
            {
              path: '/elt-pipeline',
              labelKey: 'spaces.nav.data.summary',
              iconId: 'elt',
              exact: true,
            },
            { path: '/explorer', labelKey: 'nav.explorer', iconId: 'explorer', exact: true },
            { path: '/workpanel', labelKey: 'nav.workpanel', iconId: 'workpanel', exact: true },
            {
              path: '/complex-reports',
              labelKey: 'spaces.nav.reports',
              iconId: 'reports',
              exact: true,
            },
            { path: '/settings', labelKey: 'nav.settings', iconId: 'settings', exact: true },
          ],
        },
      ];
    case 'platform_admin':
      // Ops dashboard route stays reachable by deep link; omit from nav while empty.
      return [
        {
          id: 'space-platform',
          titleKey: 'spaces.nav.group.platform',
          items: [
            {
              path: '/platform-ops/artist-requests',
              labelKey: 'nav.platformOps.artistRequests',
              iconId: 'artist_requests',
              exact: true,
            },
            {
              path: '/platform-ops/audio-unresolved',
              labelKey: 'nav.platformOps.audioUnresolved',
              iconId: 'unresolved_audio',
              exact: true,
            },
            { path: '/workpanel', labelKey: 'nav.workpanel', iconId: 'workpanel', exact: true },
            { path: '/reports', labelKey: 'spaces.nav.reports', iconId: 'reports', exact: true },
            { path: '/settings', labelKey: 'nav.settings', iconId: 'settings', exact: true },
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
            {
              path: '/artist-space',
              labelKey: 'spaces.nav.artist.summary',
              iconId: 'home',
              exact: true,
            },
            {
              path: '/artist-space/profile',
              labelKey: 'spaces.nav.artist.profile',
              iconId: 'artist',
              exact: true,
            },
            {
              path: '/artist-space/tracks',
              labelKey: 'spaces.nav.artist.tracks',
              iconId: 'catalog',
              exact: false,
            },
            {
              path: '/artist-space/releases',
              labelKey: 'spaces.nav.artist.releases',
              iconId: 'playlists',
              exact: false,
            },
            {
              path: '/artist-space/team',
              labelKey: 'spaces.nav.artist.team',
              iconId: 'team',
              exact: true,
            },
          ],
        },
      ];
    default:
      return [];
  }
}
