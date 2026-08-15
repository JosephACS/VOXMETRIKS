import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { OrganizationContextService } from '../services/organization-context.service';
import type { OrgModuleKind } from '../organization-access';

/** UX-only: requires an active validated organization context. Backend remains authority. */
export const organizationRequiredGuard: CanActivateFn = async (route) => {
  const ctx = inject(OrganizationContextService);
  const router = inject(Router);
  await ctx.ensureReady();
  const qOrg = Number(route.queryParamMap.get('organization_id') || 0);
  if (qOrg > 0 && ctx.organizationId() !== qOrg) {
    const listed = ctx.organizations().find((o) => o.id === qOrg);
    if (listed) {
      try {
        await ctx.activate(qOrg);
      } catch {
        /* fall through to standard redirects */
      }
    }
  }
  if (ctx.hasOrganization()) return true;
  const kind = ctx.contextKind();
  if (kind === 'access_revoked') {
    return router.createUrlTree(['/organizations/suspended']);
  }
  if (kind === 'invalid') {
    return router.createUrlTree(['/organizations/closed']);
  }
  // Pure personal accounts → business landing, not a permanent org sidebar shell.
  if (!ctx.organizations().length) {
    return router.createUrlTree(['/business']);
  }
  return router.createUrlTree(['/organizations/none']);
};

/**
 * Gate enterprise modules by membership + subscription tier + optional permission.
 * UX-only; backend still authorizes each request.
 */
export function organizationModuleGuard(
  moduleKind: OrgModuleKind,
  requiredPermission?: string | null,
): CanActivateFn {
  return async (route) => {
    const ctx = inject(OrganizationContextService);
    const router = inject(Router);
    await ctx.ensureReady();
    const qOrg = Number(route.queryParamMap.get('organization_id') || 0);
    if (qOrg > 0 && ctx.organizationId() !== qOrg) {
      const listed = ctx.organizations().find((o) => o.id === qOrg);
      if (listed) {
        try {
          await ctx.activate(qOrg);
        } catch {
          /* fall through */
        }
      }
    }
    if (!ctx.hasOrganization()) {
      if (!ctx.organizations().length) {
        return router.createUrlTree(['/business']);
      }
      return router.createUrlTree(['/organizations/none']);
    }
    if (ctx.canAccessModule(moduleKind, requiredPermission ?? null)) {
      return true;
    }
    const tier = ctx.accessTier();
    if (tier === 'onboarding') {
      return router.createUrlTree(['/organizations/onboarding']);
    }
    if (tier === 'recovery') {
      return router.createUrlTree(['/subscriptions/overview']);
    }
    return router.createUrlTree(['/access-denied']);
  };
}

/**
 * Syncs active org to route :id via activate API (clears previous permissions).
 * UX-only; backend still authorizes each request.
 */
export const organizationPathContextGuard: CanActivateFn = async (route) => {
  const ctx = inject(OrganizationContextService);
  const router = inject(Router);
  await ctx.ensureReady();
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
  if (ctx.organizationId() == null) {
    return router.createUrlTree(['/organizations/none']);
  }
  return true;
};

/** UX-only permission check; never replaces backend authorization. */
export function organizationPermissionGuard(permission: string): CanActivateFn {
  return async () => {
    const ctx = inject(OrganizationContextService);
    const router = inject(Router);
    await ctx.ensureReady();
    if (!ctx.hasOrganization()) {
      return router.createUrlTree(['/organizations/none']);
    }
    if (!ctx.hasPermission(permission)) {
      return router.createUrlTree(['/access-denied']);
    }
    return true;
  };
}
