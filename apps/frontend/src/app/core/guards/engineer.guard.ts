import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

/** Restricts routes to engineer or admin identity. Denied → /error/403 (stay authenticated). */
export const engineerGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  if (auth.hasEngineerAccess()) return true;
  if (typeof console !== 'undefined' && console.debug) {
    console.debug('[nav-access] engineerGuard denied for role', auth.role());
  }
  return router.createUrlTree(['/error/403']);
};
