import { inject } from '@angular/core';
import { CanActivateFn, Router, UrlTree } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { normalizeIdentityRole, type NavAccessContext } from '../navigation/nav-access.policy';
import { CrmContextService } from '../../packages/crm/services/crm-context.service';
import { OrganizationContextService } from '../../packages/organizations/services/organization-context.service';
import { SpaceContextService } from '../spaces/space-context.service';
import {
  decideProductSurfaceAccess,
  presentationModeFromUser,
} from './product-surface.policy';

export { decideProductSurfaceAccess, presentationModeFromUser } from './product-surface.policy';
export { presentationModeFromUser as presentationModeFromAuth } from './product-surface.policy';

/**
 * Spec 038 — block deep links to out-of-product demo modules.
 * Spec 045 — allow org-commercial paths when active space is organization.
 *
 * Wired via withProductSurfaceGuard in app.routes.ts for CRM/Billing/etc.
 * NOT applied to Platform Ops (platformAdminGuard).
 *
 * Awaits space bootstrap so menu announce and guard see the same activeSpaceKind.
 */
export const productSurfaceGuard: CanActivateFn = async (
  route,
  state,
): Promise<boolean | UrlTree> => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const crm = inject(CrmContextService);
  const spaces = inject(SpaceContextService);
  const orgCtx = inject(OrganizationContextService);

  await spaces.ensureReady();

  // Organization deep links may be opened while the persisted space is Personal.
  // Resolve the requested tenant through the authoritative session-context API
  // before evaluating the product surface; downstream org guards still enforce
  // membership, lifecycle, subscription tier and the concrete permission.
  const requestedOrganizationId = Number(route.queryParamMap.get('organization_id') || 0);
  const activeSpace = spaces.activeSpace();
  if (
    requestedOrganizationId > 0 &&
    (activeSpace?.kind !== 'organization' ||
      activeSpace.organizationId !== requestedOrganizationId)
  ) {
    let ok = await spaces.selectSpace(`org:${requestedOrganizationId}`, { navigate: false });
    if (!ok) {
      // Newly created orgs may be missing from a stale space list — refresh once.
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

  const ctx: NavAccessContext = {
    identityRole: normalizeIdentityRole(auth.role()),
    platformAdmin: crm.roles().includes('platform_admin'),
    presentationMode: presentationModeFromUser(auth.getUser()),
  };

  const verdict = decideProductSurfaceAccess(
    state.url,
    ctx,
    spaces.activeSpaceKind(),
  );
  if (verdict === 'allow') return true;
  if (verdict === 'staff-block') {
    return router.createUrlTree(['/error/403']);
  }
  return router.createUrlTree(['/error/module-unavailable']);
};
