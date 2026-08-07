import { Routes, CanActivateFn } from '@angular/router';

/**
 * Spec 038 — attach a guard first (before org/module guards; never with redirectTo).
 */
export function prependRouteGuard(routes: Routes, guard: CanActivateFn): Routes {
  return routes.map((r) => {
    if (r.redirectTo != null) {
      return r;
    }
    return {
      ...r,
      canActivate: [guard, ...(r.canActivate ?? [])],
    };
  });
}

/**
 * Packages that MUST be wrapped in app.routes.ts (038 demos / out-of-product).
 * Platform Ops is intentionally excluded (platformAdminGuard).
 */
export const PRODUCT_SURFACE_WRAPPED_PACKAGES = [
  'CRM_ROUTES',
  'SUBSCRIPTIONS_ROUTES',
  'BILLING_ROUTES',
  'ROYALTIES_ROUTES',
  'CAMPAIGNS_ROUTES',
  'BUSINESS_ANALYTICS_ROUTES',
  'COMPLIANCE_ROUTES',
  'REPORTING_ROUTES',
  'CUSTOMER_SUCCESS_ROUTES',
] as const;
