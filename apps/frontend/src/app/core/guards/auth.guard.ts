import { inject, Injector } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { captureReturnUrl } from '../spaces/return-url';

async function postAuthDestination(injector: Injector): Promise<string> {
  const { PostAuthOrchestrator } = await import('../spaces/post-auth.orchestrator');
  return injector.get(PostAuthOrchestrator).afterAuthenticated();
}

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
  const injector = inject(Injector);
  try {
    return router.parseUrl(await postAuthDestination(injector));
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
  const injector = inject(Injector);
  if (!auth.isAuthenticated()) {
    return router.createUrlTree(['/login']);
  }
  try {
    return router.parseUrl(await postAuthDestination(injector));
  } catch {
    return router.createUrlTree(['/login']);
  }
};
