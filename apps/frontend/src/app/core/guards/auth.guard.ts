import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { PostAuthOrchestrator } from '../spaces/post-auth.orchestrator';
import { captureReturnUrl } from '../spaces/return-url';

export const authGuard: CanActivateFn = (_route, state) => {
  const auth = inject(AuthService);
  const router = inject(Router);
  if (auth.isAuthenticated()) return true;
  captureReturnUrl(state.url);
  return router.createUrlTree(['/login']);
};

export const guestGuard: CanActivateFn = async () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  if (!auth.isAuthenticated()) return true;
  const orchestrator = inject(PostAuthOrchestrator);
  try {
    return router.parseUrl(await orchestrator.afterAuthenticated());
  } catch {
    // Session bootstrap failed: stay on login so the user can retry instead of
    // being routed into a space we could not verify.
    return true;
  }
};

/** Authenticated `/` → bootstrap destination (role home remains a legacy adapter). */
export const roleHomeRedirectGuard: CanActivateFn = async () => {
  const auth = inject(AuthService);
  const router = inject(Router);
  if (!auth.isAuthenticated()) {
    return router.createUrlTree(['/login']);
  }
  const orchestrator = inject(PostAuthOrchestrator);
  try {
    return router.parseUrl(await orchestrator.afterAuthenticated());
  } catch {
    return router.createUrlTree(['/login']);
  }
};
