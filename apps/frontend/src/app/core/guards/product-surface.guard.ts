import { inject } from '@angular/core';
import { CanActivateFn, Router, UrlTree } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { normalizeIdentityRole, type NavAccessContext } from '../navigation/nav-access.policy';
import { CrmContextService } from '../../packages/crm/services/crm-context.service';
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
 */
export const productSurfaceGuard: CanActivateFn = (_route, state): boolean | UrlTree => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const crm = inject(CrmContextService);
  const spaces = inject(SpaceContextService);

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
