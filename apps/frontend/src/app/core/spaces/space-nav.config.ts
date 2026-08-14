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

function personalAccountNavSection(opts: { includeSettings: boolean }): SpaceNavSection {
  const items: SpaceNavItem[] = [
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
      path: '/account/household',
      labelKey: 'nav.personal.household',
      iconId: 'team',
      exact: true,
    },
    {
      path: '/account/billing',
      labelKey: 'nav.personal.billing',
      iconId: 'billing',
      exact: true,
    },
  ];
  if (opts.includeSettings) {
    items.push({
      path: '/settings',
      labelKey: 'nav.settings',
      iconId: 'settings',
      exact: true,
    });
  }
  return {
    id: 'space-account',
    titleKey: 'spaces.nav.group.account',
    items,
  };
}

/** Admin-visible enterprise modules (planes, facturación, CRM, campañas, regalías). */
function adminCommercialNavSections(opts: { gateOrgModules: boolean }): SpaceNavSection[] {
  const orgGate = (
    module: OrgModuleKind,
    permission?: string,
  ): Pick<SpaceNavItem, 'orgModule' | 'orgPermission'> =>
    opts.gateOrgModules
      ? { orgModule: module, orgPermission: permission }
      : {};

  return [
    {
      id: 'space-org-plan',
      titleKey: 'spaces.nav.org.planBilling',
      items: [
        {
          path: '/subscriptions/plans',
          labelKey: 'nav.subscriptions.plans',
          iconId: 'plans',
          ...orgGate('onboarding'),
        },
        {
          path: '/subscriptions/overview',
          labelKey: 'nav.subscriptions.overview',
          iconId: 'account',
          ...orgGate('onboarding', 'subscription.view'),
        },
        {
          path: '/billing/invoices',
          labelKey: 'nav.billing.invoices',
          iconId: 'billing',
          ...orgGate('recovery', 'invoice.view'),
        },
        {
          path: '/billing/profile',
          labelKey: 'nav.billing.profile',
          iconId: 'settings',
          ...orgGate('recovery', 'billing.view'),
        },
      ],
    },
    {
      id: 'space-org-crm',
      titleKey: 'nav.section.crm',
      items: [
        {
          path: '/crm/dashboard',
          labelKey: 'nav.crm.dashboard',
          iconId: 'team',
          requireStaff: true,
        },
        {
          path: '/crm/prospects',
          labelKey: 'nav.crm.prospects',
          iconId: 'artist',
          requireStaff: true,
        },
        {
          path: '/crm/opportunities',
          labelKey: 'nav.crm.opportunities',
          iconId: 'strategic',
          requireStaff: true,
        },
      ],
    },
    {
      id: 'space-org-growth',
      titleKey: 'nav.section.campaigns',
      items: [
        {
          path: '/campaigns',
          labelKey: 'nav.campaigns.list',
          iconId: 'campaigns',
          ...orgGate('operational'),
        },
        {
          path: '/business-analytics',
          labelKey: 'nav.businessAnalytics.dashboard',
          iconId: 'activity',
          ...orgGate('operational'),
        },
      ],
    },
    {
      id: 'space-org-rights',
      titleKey: 'nav.section.royalties',
      items: [
        {
          path: '/royalties',
          labelKey: 'nav.royalties.dashboard',
          iconId: 'contracts',
          ...orgGate('operational', 'royalty.view'),
        },
        {
          path: '/payouts',
          labelKey: 'nav.royalties.payouts',
          iconId: 'billing',
          ...orgGate('operational', 'royalty.view'),
        },
      ],
    },
    {
      id: 'space-org-cs',
      titleKey: 'nav.section.customerSuccess',
      items: [
        {
          path: '/customer-success',
          labelKey: 'nav.customerSuccess.dashboard',
          iconId: 'team',
          requireStaff: true,
        },
        {
          path: '/support',
          labelKey: 'nav.customerSuccess.support',
          iconId: 'unresolved_audio',
          requireStaff: true,
        },
      ],
    },
  ];
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
            { path: '/tracks', labelKey: 'nav.tracks', iconId: 'catalog', exact: true },
            { path: '/playlists', labelKey: 'nav.playlists', iconId: 'playlists', exact: false },
            { path: '/liked', labelKey: 'nav.liked', iconId: 'liked', exact: true },
            { path: '/history', labelKey: 'nav.history', iconId: 'activity', exact: true },
            { path: '/activity', labelKey: 'nav.activity', iconId: 'activity', exact: true },
          ],
        },
        personalAccountNavSection({ includeSettings: true }),
        {
          id: 'space-entry',
          titleKey: 'firstAccess.group',
          items: [
            {
              path: '/artist-space/claim',
              labelKey: 'firstAccess.artist',
              iconId: 'artist',
              exact: true,
            },
            {
              path: '/organizations/new',
              labelKey: 'firstAccess.organization',
              iconId: 'organization',
              exact: true,
            },
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
            {
              path: '/workpanel',
              labelKey: 'nav.workpanel',
              iconId: 'workpanel',
              exact: true,
              requireStaff: true,
            },
            {
              path: '/catalog',
              labelKey: 'nav.catalogHub',
              iconId: 'catalog',
              exact: true,
              orgModule: 'operational',
            },
            {
              path: hub,
              labelKey: 'spaces.nav.org.summary',
              iconId: 'organization',
              exact: true,
              orgModule: 'org_admin_basic',
              orgPermission: 'organization.view',
            },
            {
              path: '/reports',
              labelKey: 'spaces.nav.reports',
              iconId: 'reports',
              exact: true,
              requireStaff: true,
            },
          ],
        },
        ...adminCommercialNavSections({ gateOrgModules: true }),
        personalAccountNavSection({ includeSettings: true }),
      ];
    }
    case 'data_ops':
      // Estado técnico → /workpanel (canónico). Ingeniería de datos → /elt-pipeline.
      // One URL → one active item (never share paths across labels).
      return [
        {
          id: 'space-data',
          titleKey: 'spaces.nav.group.dataOps',
          items: [
            {
              path: '/workpanel',
              labelKey: 'nav.technicalStatus',
              iconId: 'workpanel',
              exact: true,
            },
            {
              path: '/elt-pipeline',
              labelKey: 'nav.eltPipeline',
              iconId: 'elt',
              exact: true,
            },
            { path: '/explorer', labelKey: 'nav.explorer', iconId: 'explorer', exact: true },
            {
              path: '/reports',
              labelKey: 'spaces.nav.reports',
              iconId: 'reports',
              exact: true,
            },
          ],
        },
      ];
    case 'platform_admin':
      return [
        {
          id: 'space-platform',
          titleKey: 'spaces.nav.group.platform',
          items: [
            { path: '/workpanel', labelKey: 'nav.workpanel', iconId: 'workpanel', exact: true },
            { path: '/catalog', labelKey: 'nav.catalogHub', iconId: 'catalog', exact: true },
            { path: '/reports', labelKey: 'spaces.nav.reports', iconId: 'reports', exact: true },
            { path: '/settings', labelKey: 'nav.settings', iconId: 'settings', exact: true },
          ],
        },
        {
          id: 'space-platform-ops',
          titleKey: 'nav.section.platformOps',
          items: [
            {
              path: '/platform-ops/artist-requests',
              labelKey: 'nav.platformOps.artistRequests',
              iconId: 'artist_requests',
              exact: true,
              requireStaff: true,
            },
            {
              path: '/platform-ops/audio-unresolved',
              labelKey: 'nav.platformOps.audioUnresolved',
              iconId: 'unresolved_audio',
              exact: true,
              requireStaff: true,
            },
          ],
        },
        ...adminCommercialNavSections({ gateOrgModules: false }),
        personalAccountNavSection({ includeSettings: false }),
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
