import { EnterpriseActionBarComponent } from './enterprise-action-bar.component';
import { EnterpriseDataTableComponent } from './enterprise-data-table.component';
import { EnterpriseEmptyStateComponent } from './enterprise-empty-state.component';
import { EnterpriseErrorStateComponent } from './enterprise-error-state.component';
import { EnterpriseFormFieldComponent } from './enterprise-form-field.component';
import { EnterpriseLoadingSkeletonComponent } from './enterprise-loading-skeleton.component';
import { EnterpriseOrgRequiredComponent } from './enterprise-org-required.component';
import { EnterprisePageHeaderComponent } from './enterprise-page-header.component';
import { EnterpriseSectionCardComponent } from './enterprise-section-card.component';
import { EnterpriseStatCardComponent } from './enterprise-stat-card.component';
import { EnterpriseStatusBadgeComponent } from './enterprise-status-badge.component';

export { EnterpriseActionBarComponent } from './enterprise-action-bar.component';
export { EnterpriseDataTableComponent } from './enterprise-data-table.component';
export { EnterpriseEmptyStateComponent } from './enterprise-empty-state.component';
export { EnterpriseErrorStateComponent } from './enterprise-error-state.component';
export { EnterpriseFormFieldComponent } from './enterprise-form-field.component';
export { EnterpriseLoadingSkeletonComponent } from './enterprise-loading-skeleton.component';
export { EnterpriseOrgRequiredComponent } from './enterprise-org-required.component';
export { EnterprisePageHeaderComponent } from './enterprise-page-header.component';
export { EnterpriseSectionCardComponent } from './enterprise-section-card.component';
export { EnterpriseStatCardComponent } from './enterprise-stat-card.component';
export { EnterpriseStatusBadgeComponent } from './enterprise-status-badge.component';

/**
 * Convenience array for page `imports: [...]`.
 * Confirm dialogs: use ConfirmDialogService (ConfirmDialogComponent is registered globally in app.ts — do not re-declare it here).
 */
export const ENTERPRISE_UI_IMPORTS = [
  EnterprisePageHeaderComponent,
  EnterpriseSectionCardComponent,
  EnterpriseStatCardComponent,
  EnterpriseStatusBadgeComponent,
  EnterpriseEmptyStateComponent,
  EnterpriseErrorStateComponent,
  EnterpriseOrgRequiredComponent,
  EnterpriseLoadingSkeletonComponent,
  EnterpriseActionBarComponent,
  EnterpriseFormFieldComponent,
  EnterpriseDataTableComponent,
] as const;
