import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

/** Restricts routes to engineer role (admin username or admin@ email). */
export const engineerGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  if (auth.hasEngineerAccess()) return true;
  return router.createUrlTree(['/dashboard']);
};
