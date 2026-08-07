import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import {
  classifyProductDeepLink,
  normalizeIdentityRole,
} from '../navigation/nav-access.policy';
import { CrmContextService } from '../../packages/crm/services/crm-context.service';
import { SpaceContextService } from '../spaces/space-context.service';
import { spaceAllowsProductPath } from '../spaces/space-access.policy';

function presentationModeFromAuth(auth: AuthService): boolean {
  const user = auth.getUser();
  const username = (user?.username || '').toLowerCase();
  const prefs = user?.preferences as
    | { presentation_nav?: boolean; presentation_role?: string }
    | undefined;
  return !!(
    prefs?.presentation_nav ||
    prefs?.presentation_role ||
    username === 'demo.business' ||
    username === 'demo.artist' ||
    username === 'finance.manager'
  );
}

/**
 * Spec 038 — block deep links to out-of-product demo modules.
 * Spec 045 — allow org-commercial / platform / data paths when the active
 * product space explicitly includes them (backend RBAC still authoritative).
 */
export const productSurfaceGuard: CanActivateFn = (_route, state) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const crm = inject(CrmContextService);
  const spaces = inject(SpaceContextService);

  const ctx = {
    identityRole: normalizeIdentityRole(auth.role()),
    platformAdmin: crm.roles().includes('platform_admin'),
    presentationMode: presentationModeFromAuth(auth),
  };

  if (spaceAllowsProductPath(state.url, spaces.activeSpaceKind())) {
    const staffVerdict = classifyProductDeepLink(state.url, ctx);
    if (staffVerdict === 'staff-block') {
      return router.createUrlTree(['/error/403']);
    }
    return true;
  }

  const verdict = classifyProductDeepLink(state.url, ctx);
  if (verdict === 'allow') return true;
  if (verdict === 'staff-block') {
    return router.createUrlTree(['/error/403']);
  }
  return router.createUrlTree(['/error/module-unavailable']);
};
