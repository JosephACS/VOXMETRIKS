import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { homePathForRole } from '../navigation/nav-access.policy';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  if (auth.isAuthenticated()) return true;
  return router.createUrlTree(['/login']);
};

export const guestGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  if (!auth.isAuthenticated()) return true;
  return router.parseUrl(homePathForRole(auth.role()));
};

/** Authenticated `/` → role home (never force Discover for staff). */
export const roleHomeRedirectGuard: CanActivateFn = () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  if (!auth.isAuthenticated()) return router.createUrlTree(['/login']);
  return router.parseUrl(homePathForRole(auth.role()));
};
