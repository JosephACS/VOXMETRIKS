/**
 * Spec 054 — space navigation adapter over the product-surface registry.
 */

import type { SpaceKind } from './space.models';
import type { SpaceNavIconId } from './space-nav.icons';
import {
  buildProductNavSections,
  isProductSurfaceAllowed,
  listVisibleSidebarSurfaces,
  resolveSurfacePath,
  type ProductSurfaceContext,
} from '../product-surface';
import { productSurfacesForSpace } from '../product-surface/product-surface.registry';
import type { ProductSurfaceDefinition } from '../product-surface/product-surface.models';

export interface SpaceNavItem {
  path: string;
  labelKey: string;
  iconId: SpaceNavIconId;
  exact?: boolean;
}

export interface SpaceNavSection {
  id: string;
  titleKey: string;
  items: SpaceNavItem[];
}

export interface SpaceNavFilterContext {
  productSurfaceContext: ProductSurfaceContext;
}

function isSidebarSurface(s: ProductSurfaceDefinition): boolean {
  if (s.sectionId === 'space-org-admin-tabs' || s.sectionId === 'space-catalog-tabs') {
    return false;
  }
  if (s.sectionId === 'space-report-tabs') return false;
  return true;
}

function sectionsFromSurfaces(
  surfaces: ProductSurfaceDefinition[],
  organizationId?: number | null,
): SpaceNavSection[] {
  const bySection = new Map<string, SpaceNavSection>();
  const sectionOrder = new Map<string, number>();
  for (const surface of surfaces) {
    if (!isSidebarSurface(surface)) continue;
    if (!sectionOrder.has(surface.sectionId)) {
      sectionOrder.set(surface.sectionId, surface.order);
    }
    let section = bySection.get(surface.sectionId);
    if (!section) {
      section = { id: surface.sectionId, titleKey: surface.sectionTitleKey, items: [] };
      bySection.set(surface.sectionId, section);
    }
    section.items.push({
      path: resolveSurfacePath(surface, organizationId ?? undefined),
      labelKey: surface.labelKey,
      iconId: surface.iconId,
      exact: surface.exact,
    });
  }
  return [...bySection.values()].sort(
    (a, b) => (sectionOrder.get(a.id) ?? 0) - (sectionOrder.get(b.id) ?? 0),
  );
}

export function canAnnounceSpaceNavItem(
  item: SpaceNavItem,
  ctx: SpaceNavFilterContext,
): boolean {
  const orgId = ctx.productSurfaceContext.organizationId;
  const surfaces = productSurfacesForSpace(ctx.productSurfaceContext.activeSpace).filter(
    isSidebarSurface,
  );
  const surface = surfaces.find((s) => resolveSurfacePath(s, orgId) === item.path.split('?')[0]);
  if (!surface) return false;
  return isProductSurfaceAllowed(surface, ctx.productSurfaceContext);
}

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

/**
 * Build nav sections for a space from the registry.
 * Pass `access` for permission-filtered production nav (incl. ready=false bootstrap).
 * Without `access`, returns the structural sidebar catalog for the space (unit inventory).
 */
export function spaceNavSectionsFor(
  kind: SpaceKind,
  opts?: { organizationId?: number | null; access?: ProductSurfaceContext },
): SpaceNavSection[] {
  if (opts?.access) {
    const access: ProductSurfaceContext = {
      ...opts.access,
      activeSpace: kind,
      organizationId: opts.organizationId ?? opts.access.organizationId,
    };
    return buildProductNavSections(access).map((section) => ({
      id: section.id,
      titleKey: section.titleKey,
      items: section.items.map((item) => ({
        path: item.path,
        labelKey: item.labelKey,
        iconId: item.iconId,
        exact: item.exact,
      })),
    }));
  }

  return sectionsFromSurfaces(productSurfacesForSpace(kind), opts?.organizationId);
}

export function registeredSurfacesForSpace(kind: SpaceKind): ProductSurfaceDefinition[] {
  return productSurfacesForSpace(kind);
}

export function visibleSidebarPaths(ctx: ProductSurfaceContext): string[] {
  return listVisibleSidebarSurfaces(ctx).map((s) =>
    resolveSurfacePath(s, ctx.organizationId),
  );
}
