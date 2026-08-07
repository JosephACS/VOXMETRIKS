import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { CrmContextService } from '../../packages/crm/services/crm-context.service';

/** Technical platform tools: engineer identity or CRM platform_admin. */
export const platformAdminGuard: CanActivateFn = async () => {
  const auth = inject(AuthService);
  const crm = inject(CrmContextService);
  const router = inject(Router);
  if (auth.hasEngineerAccess()) return true;
  if (crm.status() === 'idle') {
    await crm.bootstrap().catch(() => undefined);
  }
  if (crm.roles().includes('platform_admin')) return true;
  return router.createUrlTree(['/access-denied']);
};
