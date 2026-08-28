import type { Routes } from '@angular/router';
import { withProductSurfaceGuard } from './core/guards/with-product-surface-guard';
import { ARTIST_SPACE_ROUTES } from './packages/artist-space/artist-space.routes';
import { ARTIST_PROFILES_ROUTES } from './packages/artists/artists.routes';
import { BILLING_ROUTES } from './packages/billing/billing.routes';
import { BUSINESS_ANALYTICS_ROUTES } from './packages/business-analytics/business-analytics.routes';
import { CAMPAIGNS_ROUTES } from './packages/campaigns/campaigns.routes';
import { CATALOG_PUBLISHING_ROUTES } from './packages/catalog-publishing/catalog-publishing.routes';
import { CATALOG_RIGHTS_ROUTES } from './packages/catalog-rights/catalog-rights.routes';
import { COMPLEX_REPORTS_ROUTES } from './packages/complex-reports/complex-reports.routes';
import { COMPLIANCE_ROUTES } from './packages/compliance/compliance.routes';
import { CRM_ROUTES } from './packages/crm/crm.routes';
import { CUSTOMER_SUCCESS_ROUTES } from './packages/customer-success/customer-success.routes';
import { ORGANIZATIONS_ROUTES } from './packages/organizations/organizations.routes';
import { PERSONAL_ACCOUNT_ROUTES } from './packages/personal-account/personal-account.routes';
import { PLATFORM_OPS_ROUTES } from './packages/platform-ops/platform-ops.routes';
import { REPORTING_ROUTES } from './packages/reporting/reporting.routes';
import { ROYALTIES_ROUTES } from './packages/royalties/royalties.routes';
import { SIMPLE_REPORTS_ROUTES } from './packages/simple-reports/simple-reports.routes';
import { SUBSCRIPTIONS_ROUTES } from './packages/subscriptions/subscriptions.routes';
import { WORKPANEL_ROUTES } from './packages/workpanel/workpanel.routes';

/**
 * Product routes are loaded only after the authenticated shell is selected.
 * This keeps organization, billing, reporting and platform metadata out of the
 * public login bundle without changing any URL.
 */
export const PRODUCT_ROUTES: Routes = [
  ...ORGANIZATIONS_ROUTES,
  ...withProductSurfaceGuard(CRM_ROUTES),
  ...withProductSurfaceGuard(SUBSCRIPTIONS_ROUTES),
  ...withProductSurfaceGuard(BILLING_ROUTES),
  ...withProductSurfaceGuard(ROYALTIES_ROUTES),
  ...ARTIST_PROFILES_ROUTES,
  ...CATALOG_RIGHTS_ROUTES,
  ...CATALOG_PUBLISHING_ROUTES,
  ...withProductSurfaceGuard(CAMPAIGNS_ROUTES),
  ...withProductSurfaceGuard(BUSINESS_ANALYTICS_ROUTES),
  ...withProductSurfaceGuard(COMPLIANCE_ROUTES),
  ...PLATFORM_OPS_ROUTES,
  ...ARTIST_SPACE_ROUTES,
  ...withProductSurfaceGuard(REPORTING_ROUTES),
  ...SIMPLE_REPORTS_ROUTES,
  ...WORKPANEL_ROUTES,
  ...COMPLEX_REPORTS_ROUTES,
  ...withProductSurfaceGuard(CUSTOMER_SUCCESS_ROUTES),
  ...PERSONAL_ACCOUNT_ROUTES,
];
