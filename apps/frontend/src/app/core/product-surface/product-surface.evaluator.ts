/**
 * Spec 054 — pure product-surface access evaluator.
 * No DI, no username / presentation flags.
 */

import { isPersonalSurfacePath } from '../navigation/nav-access.policy';
import type { SpaceKind } from '../spaces/space.models';
import type {
  ProductOrganizationTier,
  ProductPathAccessResult,
  ProductSurfaceContext,
  ProductSurfaceDefinition,
  ProductSurfaceVerdict,
} from './product-surface.models';
import { PRODUCT_SURFACE_REGISTRY, productSurfacesForSpace } from './product-surface.registry';

const TIER_RANK: Record<ProductOrganizationTier, number> = {
  onboarding: 1,
  recovery: 2,
  operational: 3,
};

export function resolveSurfacePath(
  surface: ProductSurfaceDefinition,
  organizationId?: number,
): string {
  if (!surface.path.includes(':id')) return surface.path;
  if (organizationId == null) {
    return surface.path.replace('/organizations/:id', '/organizations/none');
  }
  return surface.path.replace(/:id/g, String(organizationId));
}

export function tierMeetsMinimum(
  actual: ProductOrganizationTier | undefined,
  required: ProductOrganizationTier | undefined,
): boolean {
  if (!required) return true;
  if (!actual) return false;
  return TIER_RANK[actual] >= TIER_RANK[required];
}

function codePresent(code: string, ctx: ProductSurfaceContext, surface: ProductSurfaceDefinition): boolean {
  const trimmed = code.trim();
  if (!trimmed) return true;

  if (ctx.activeSpace === 'artist') {
    return ctx.artistCapabilities.has(trimmed);
  }
  if (
    ctx.activeSpace === 'organization' ||
    surface.organizationTier != null ||
    surface.path.includes('/organizations/')
  ) {
    return ctx.permissions.has(trimmed);
  }
  if (trimmed === 'report.view' && ctx.staffCapabilities.size > 0) {
    return true;
  }
  return ctx.permissions.has(trimmed) || ctx.artistCapabilities.has(trimmed);
}

function capabilitySatisfied(
  surface: ProductSurfaceDefinition,
  ctx: ProductSurfaceContext,
): boolean {
  if (surface.capability && !codePresent(surface.capability, ctx, surface)) {
    return false;
  }
  if (surface.capabilitiesAll?.length) {
    if (!surface.capabilitiesAll.every((c) => codePresent(c, ctx, surface))) {
      return false;
    }
  }
  if (surface.capabilitiesAny?.length) {
    if (!surface.capabilitiesAny.some((c) => codePresent(c, ctx, surface))) {
      return false;
    }
  }
  return true;
}

function isPrivileged(surface: ProductSurfaceDefinition): boolean {
  return (
    !!surface.organizationTier ||
    !!surface.capability ||
    !!(surface.capabilitiesAny?.length) ||
    !!(surface.capabilitiesAll?.length) ||
    !!surface.staffCapability ||
    !!surface.platformRole ||
    surface.path.includes(':id')
  );
}

type SurfaceDenyReason = 'space' | 'bootstrap' | 'tier' | 'permission';

/**
 * Detailed surface evaluation for path-level routing.
 * Returns allow or the primary deny reason.
 */
export function evaluateProductSurfaceReason(
  surface: ProductSurfaceDefinition,
  ctx: ProductSurfaceContext,
): 'allow' | SurfaceDenyReason {
  if (!surface.spaces.includes(ctx.activeSpace)) return 'space';

  if (!ctx.ready && isPrivileged(surface)) return 'bootstrap';

  if (surface.organizationTier) {
    if (ctx.organizationId == null) return 'tier';
    if (!tierMeetsMinimum(ctx.organizationTier, surface.organizationTier)) return 'tier';
  }

  if (surface.path.includes(':id') && ctx.organizationId == null) {
    return 'tier';
  }

  if (surface.staffCapability) {
    if (!ctx.staffCapabilities.has(surface.staffCapability)) return 'permission';
  }

  if (surface.platformRole) {
    if (!ctx.platformRoles.has(surface.platformRole)) return 'permission';
  }

  if (!capabilitySatisfied(surface, ctx)) return 'permission';

  return 'allow';
}

/**
 * Conjunctive evaluation of a single surface against hydrated facts.
 * ready=false never returns privileged surfaces (any constrained row).
 */
export function evaluateProductSurface(
  surface: ProductSurfaceDefinition,
  ctx: ProductSurfaceContext,
): ProductSurfaceVerdict {
  return evaluateProductSurfaceReason(surface, ctx) === 'allow' ? 'allow' : 'deny';
}

export function isProductSurfaceAllowed(
  surface: ProductSurfaceDefinition,
  ctx: ProductSurfaceContext,
): boolean {
  return evaluateProductSurface(surface, ctx) === 'allow';
}

export function listVisibleSurfaces(ctx: ProductSurfaceContext): ProductSurfaceDefinition[] {
  return productSurfacesForSpace(ctx.activeSpace).filter((s) => isProductSurfaceAllowed(s, ctx));
}

/** Sidebar-eligible surfaces (exclude tab-only admin/catalog extras). */
export function listVisibleSidebarSurfaces(ctx: ProductSurfaceContext): ProductSurfaceDefinition[] {
  return listVisibleSurfaces(ctx)
    .filter((s) => {
      if (!s.contextGroup) return true;
      return (
        s.id === 'org.catalog' ||
        s.id === 'org.hub' ||
        s.id === 'org.reports' ||
        s.id === 'org.subscriptions.overview' ||
        s.id === 'data_ops.reports' ||
        s.id === 'data_ops.elt' ||
        s.id === 'data_ops.explorer' ||
        s.id.startsWith('platform.ops.')
      );
    })
    .filter((s) => {
      if (s.sectionId === 'space-org-admin-tabs' || s.sectionId === 'space-catalog-tabs') {
        return false;
      }
      if (s.sectionId === 'space-report-tabs') return false;
      return true;
    });
}

export interface ProductNavSection {
  id: string;
  titleKey: string;
  items: Array<{
    id: string;
    path: string;
    labelKey: string;
    iconId: ProductSurfaceDefinition['iconId'];
    exact?: boolean;
  }>;
}

export function buildProductNavSections(ctx: ProductSurfaceContext): ProductNavSection[] {
  const visible = listVisibleSidebarSurfaces(ctx);
  const bySection = new Map<string, ProductNavSection>();

  for (const surface of visible) {
    let section = bySection.get(surface.sectionId);
    if (!section) {
      section = {
        id: surface.sectionId,
        titleKey: surface.sectionTitleKey,
        items: [],
      };
      bySection.set(surface.sectionId, section);
    }
    section.items.push({
      id: surface.id,
      path: resolveSurfacePath(surface, ctx.organizationId),
      labelKey: surface.labelKey,
      iconId: surface.iconId,
      exact: surface.exact,
    });
  }

  const sectionOrder = new Map<string, number>();
  for (const surface of visible) {
    if (!sectionOrder.has(surface.sectionId)) {
      sectionOrder.set(surface.sectionId, surface.order);
    }
  }

  return [...bySection.values()].sort(
    (a, b) => (sectionOrder.get(a.id) ?? 0) - (sectionOrder.get(b.id) ?? 0),
  );
}

export function listVisibleContextTabs(
  contextGroup: string,
  ctx: ProductSurfaceContext,
): ProductSurfaceDefinition[] {
  return PRODUCT_SURFACE_REGISTRY.filter(
    (s) => s.contextGroup === contextGroup && isProductSurfaceAllowed(s, ctx),
  ).sort((a, b) => a.order - b.order || a.id.localeCompare(b.id));
}

export function findSurfacesByPath(
  path: string,
  space?: SpaceKind,
): ProductSurfaceDefinition[] {
  const normalized = (path || '').split('?')[0];
  return PRODUCT_SURFACE_REGISTRY.filter((s) => {
    if (space && !s.spaces.includes(space)) return false;
    const staticPath = s.path.includes(':id') ? null : s.path;
    if (staticPath && (normalized === staticPath || normalized.startsWith(staticPath + '/'))) {
      return true;
    }
    if (s.path.includes(':id')) {
      const pattern = s.path.replace(/:id/g, '\\d+');
      return new RegExp(`^${pattern}(?:/|$)`).test(normalized);
    }
    if (s.matchPrefixes?.length) {
      return s.matchPrefixes.some((prefix) => {
        const resolved = prefix.includes(':id')
          ? prefix.replace(/:id/g, '\\d+')
          : prefix.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        if (prefix.includes(':id')) {
          return new RegExp(`^${resolved}(?:/|$)`).test(normalized);
        }
        return normalized === prefix || normalized.startsWith(prefix + '/');
      });
    }
    return false;
  });
}

/**
 * Path-level access for the product-surface guard.
 * - allow: at least one registry row permits the path in the active space
 * - permission-denied: row matches space/tier but capability/staff/platform missing
 * - unavailable: wrong space or tier / org context
 * - unregistered: no registry row (personal paths stay allow-by-route-guards)
 */
export function evaluateProductPathAccess(
  path: string,
  ctx: ProductSurfaceContext,
): ProductPathAccessResult {
  const normalized = (path || '').split('?')[0];
  const allMatches = findSurfacesByPath(normalized);
  if (allMatches.length === 0) {
    return 'unregistered';
  }

  const spaceMatches = allMatches.filter((s) => s.spaces.includes(ctx.activeSpace));
  if (spaceMatches.length === 0) {
    return 'unavailable';
  }

  let sawPermission = false;
  let sawUnavailable = false;
  for (const surface of spaceMatches) {
    const reason = evaluateProductSurfaceReason(surface, ctx);
    if (reason === 'allow') return 'allow';
    if (reason === 'permission') sawPermission = true;
    else sawUnavailable = true;
  }

  if (sawPermission) return 'permission-denied';
  if (sawUnavailable) return 'unavailable';
  // Personal unregistered is handled above; keep personal helper for clarity.
  if (isPersonalSurfacePath(normalized)) return 'unregistered';
  return 'unavailable';
}

/**
 * Whether a hydrated session may announce this path in the active space.
 * Fail-closed when no registry row matches a constrained commercial/staff path.
 */
export function pathAllowedByRegistry(path: string, ctx: ProductSurfaceContext): boolean {
  const result = evaluateProductPathAccess(path, ctx);
  return result === 'allow' || result === 'unregistered';
}

export function emptyProductSurfaceContext(space: SpaceKind = 'personal'): ProductSurfaceContext {
  return {
    ready: false,
    activeSpace: space,
    permissions: new Set(),
    artistCapabilities: new Set(),
    staffCapabilities: new Set(),
    platformRoles: new Set(),
  };
}
