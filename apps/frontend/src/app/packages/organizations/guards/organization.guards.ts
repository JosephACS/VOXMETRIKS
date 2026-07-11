import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { OrganizationContextService } from '../services/organization-context.service';

/** UX-only: requires an active validated organization context. Backend remains authority. */
export const organizationRequiredGuard: CanActivateFn = async () => {
  const ctx = inject(OrganizationContextService);
  const router = inject(Router);
  if (ctx.status() === 'idle') {
    await ctx.bootstrap();
  }
  if (ctx.hasOrganization()) return true;
  const kind = ctx.contextKind();
  if (kind === 'access_revoked') {
    return router.createUrlTree(['/organizations/suspended']);
  }
  if (kind === 'invalid') {
    return router.createUrlTree(['/organizations/closed']);
  }
  return router.createUrlTree(['/organizations/none']);
};

/**
 * Syncs active org to route :id via activate API (clears previous permissions).
 * UX-only; backend still authorizes each request.
 */
export const organizationPathContextGuard: CanActivateFn = async (route) => {
  const ctx = inject(OrganizationContextService);
  const router = inject(Router);
  if (ctx.status() === 'idle') {
    await ctx.bootstrap();
  }
  const id = Number(route.paramMap.get('id'));
  if (!Number.isFinite(id) || id <= 0) {
    return router.createUrlTree(['/organizations/none']);
  }
  const listed = ctx.organizations().find((o) => o.id === id);
  if (!listed) {
    if (!ctx.organizations().length) {
      return router.createUrlTree(['/organizations/none']);
    }
    return router.createUrlTree(['/access-denied']);
  }
  if (listed.status === 'closed') {
    return router.createUrlTree(['/organizations/closed']);
  }
  if (listed.status === 'suspended_by_platform') {
    return router.createUrlTree(['/organizations/suspended']);
  }
  if (ctx.activeOrganization()?.id !== id) {
    try {
      await ctx.activate(id);
    } catch {
      return router.createUrlTree(['/access-denied']);
    }
  }
  if (!ctx.hasOrganization()) {
    return router.createUrlTree(['/organizations/none']);
  }
  return true;
};

/** UX-only permission check; never replaces backend authorization. */
export function organizationPermissionGuard(permission: string): CanActivateFn {
  return async () => {
    const ctx = inject(OrganizationContextService);
    const router = inject(Router);
    if (ctx.status() === 'idle') {
      await ctx.bootstrap();
    }
    if (!ctx.hasOrganization()) {
      return router.createUrlTree(['/organizations/none']);
    }
    if (!ctx.hasPermission(permission)) {
      return router.createUrlTree(['/access-denied']);
    }
    return true;
  };
}
