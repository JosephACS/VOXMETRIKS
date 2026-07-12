import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { CrmContextService } from '../services/crm-context.service';

/**
 * UX-only guard: redirects to /crm/access-denied if the user has no CRM
 * permissions after bootstrapping. Backend remains the authorization authority.
 */
export const crmAccessGuard: CanActivateFn = async () => {
  const ctx = inject(CrmContextService);
  const router = inject(Router);

  if (ctx.status() === 'idle') {
    await ctx.bootstrap();
  }

  if (ctx.hasCrmAccess()) return true;
  return router.createUrlTree(['/crm/access-denied']);
};
