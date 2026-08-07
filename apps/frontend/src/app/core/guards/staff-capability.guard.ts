import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import {
  canActivateStaffPath,
  normalizeIdentityRole,
} from '../navigation/nav-access.policy';
import { CrmContextService } from '../../packages/crm/services/crm-context.service';

/**
 * Blocks pure listeners from staff Workpanel / reports / analytics hubs.
 * Authenticated users without permission go to /error/403 (not login).
 */
export const staffCapabilityGuard: CanActivateFn = (_route, state) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const crm = inject(CrmContextService);

  const user = auth.getUser();
  const username = (user?.username || '').toLowerCase();
  const prefs = user?.preferences as
    | { presentation_nav?: boolean; presentation_role?: string }
    | undefined;
  const presentationMode = !!(
    prefs?.presentation_nav ||
    prefs?.presentation_role ||
    username === 'demo.business' ||
    username === 'demo.artist' ||
    username === 'finance.manager'
  );

  const ctx = {
    identityRole: normalizeIdentityRole(auth.role()),
    platformAdmin: crm.roles().includes('platform_admin'),
    presentationMode,
  };

  if (canActivateStaffPath(state.url, ctx)) return true;

  if (typeof console !== 'undefined' && console.debug) {
    console.debug('[nav-access] blocked staff path', state.url, ctx.identityRole);
  }
  return router.createUrlTree(['/error/403']);
};
