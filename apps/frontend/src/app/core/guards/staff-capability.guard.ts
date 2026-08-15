import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import {
  canActivateStaffPath,
  normalizeIdentityRole,
} from '../navigation/nav-access.policy';
import { CrmContextService } from '../../packages/crm/services/crm-context.service';
import { OrganizationContextService } from '../../packages/organizations/services/organization-context.service';

/**
 * Blocks pure listeners from staff Workpanel / reports / analytics hubs.
 * Organization members with report.view / decision.view may open reporting hubs.
 * Authenticated users without permission go to /error/403 (not login).
 * Spec 054: no username / presentation bypass.
 */
export const staffCapabilityGuard: CanActivateFn = async (_route, state) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  const crm = inject(CrmContextService);
  const organization = inject(OrganizationContextService);

  const path = (state.url || '').split('?')[0];
  const organizationPermission =
    path === '/reports' ||
    path.startsWith('/reports/') ||
    path === '/simple-reports' ||
    path.startsWith('/simple-reports/') ||
    path === '/complex-reports' ||
    path.startsWith('/complex-reports/')
      ? 'report.view'
      : path === '/business-decisions' || path.startsWith('/business-decisions/')
        ? 'decision.view'
        : null;
  if (organizationPermission) {
    await organization.ensureReady();
    if (organization.canAccessModule('operational', organizationPermission)) {
      return true;
    }
    // Spec 054: membership may already hold the permission while subscription
    // enrichment is still catching up after space activation.
    if (
      organization.hasPermission(organizationPermission) &&
      organization.accessTier() === 'operational'
    ) {
      return true;
    }
    await organization.refreshSubscriptionSnapshot(undefined, { soft: true });
    if (organization.canAccessModule('operational', organizationPermission)) {
      return true;
    }
  }

  const ctx = {
    identityRole: normalizeIdentityRole(auth.role()),
    platformAdmin: crm.roles().includes('platform_admin'),
  };

  if (canActivateStaffPath(state.url, ctx)) return true;

  if (typeof console !== 'undefined' && console.debug) {
    console.debug('[nav-access] blocked staff path', state.url, ctx.identityRole);
  }
  return router.createUrlTree(['/error/403']);
};
