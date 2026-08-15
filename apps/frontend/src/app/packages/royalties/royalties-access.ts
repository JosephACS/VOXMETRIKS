import { inject } from '@angular/core';
import { OrganizationContextService } from '../organizations/services/organization-context.service';

/** Royalties action gates — permission-only (Spec 054: no presentation username bypass). */
export function royaltiesAccess() {
  const orgCtx = inject(OrganizationContextService);

  const can = (code: string): boolean => orgCtx.hasPermission(code);

  return {
    isPresentation: (): boolean => false,
    isReadOnly: (): boolean => false,
    canApprove: (): boolean => can('royalty.approve'),
    canSettle: (): boolean => can('royalty.settle'),
    canPayout: (): boolean => can('royalty.payout'),
    canManagePool: (): boolean => can('royalty.pool.manage'),
  };
}
