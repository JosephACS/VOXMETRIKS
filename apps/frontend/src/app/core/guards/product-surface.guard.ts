import { inject } from '@angular/core';
import { CanActivateFn, Router, UrlTree } from '@angular/router';
import { OrganizationContextService } from '../../packages/organizations/services/organization-context.service';
import { SpaceContextService } from '../spaces/space-context.service';
import { evaluateProductPathAccess } from '../product-surface/product-surface.evaluator';

/**
 * Spec 054 — product surface gate.
 * Uses SpaceContextService.productSurfaceContext() + evaluateProductPathAccess exclusively.
 * Wired via withProductSurfaceGuard for commercial packages.
 */
export const productSurfaceGuard: CanActivateFn = async (
  route,
  state,
): Promise<boolean | UrlTree> => {
  const router = inject(Router);
  const spaces = inject(SpaceContextService);
  const orgCtx = inject(OrganizationContextService);

  await spaces.ensureReady();

  const requestedOrganizationId = Number(route.queryParamMap.get('organization_id') || 0);
  const activeSpace = spaces.activeSpace();
  if (
    requestedOrganizationId > 0 &&
    (activeSpace?.kind !== 'organization' ||
      activeSpace.organizationId !== requestedOrganizationId)
  ) {
    let ok = await spaces.selectSpace(`org:${requestedOrganizationId}`, { navigate: false });
    if (!ok) {
      try {
        await spaces.bootstrapFromSession();
        ok = await spaces.selectSpace(`org:${requestedOrganizationId}`, { navigate: false });
      } catch {
        ok = false;
      }
    }
    if (!ok) {
      try {
        await orgCtx.activate(requestedOrganizationId);
        await spaces.bootstrapFromSession();
        ok = await spaces.selectSpace(`org:${requestedOrganizationId}`, { navigate: false });
      } catch {
        ok = false;
      }
    }
    if (!ok || spaces.activeSpace()?.organizationId !== requestedOrganizationId) {
      return router.createUrlTree(['/error/module-unavailable']);
    }
  }

  const verdict = evaluateProductPathAccess(state.url, spaces.productSurfaceContext());
  switch (verdict) {
    case 'allow':
    case 'unregistered':
      return true;
    case 'permission-denied':
      return router.createUrlTree(['/error/403']);
    case 'unavailable':
      return router.createUrlTree(['/error/module-unavailable']);
    default: {
      const _exhaustive: never = verdict;
      return _exhaustive;
    }
  }
};
