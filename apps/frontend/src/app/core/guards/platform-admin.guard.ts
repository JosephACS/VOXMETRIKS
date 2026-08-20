import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { CrmContextService } from '../../packages/crm/services/crm-context.service';
import { canAccessPlatformAdmin } from './platform-admin.policy';

export { canAccessPlatformAdmin } from './platform-admin.policy';

/** Platform Ops routes: identity admin or CRM platform_admin only (not pure engineer). */
export const platformAdminGuard: CanActivateFn = async () => {
  const auth = inject(AuthService);
  const crm = inject(CrmContextService);
  const router = inject(Router);

  if (crm.status() === 'idle') {
    await crm.bootstrap().catch(() => undefined);
  }

  const allowed = canAccessPlatformAdmin({
    isAdmin: auth.isAdmin(),
    crmRoles: crm.roles(),
  });
  if (allowed) return true;
  return router.createUrlTree(['/access-denied'], {
    queryParams: { reason: 'platform' },
  });
};
