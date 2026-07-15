import { inject } from '@angular/core';
import { AuthService } from '../../core/services/auth.service';
import { OrganizationContextService } from '../organizations/services/organization-context.service';

/** Read-only when presentation_nav / demo.business or missing action permission. */
export function royaltiesAccess() {
  const auth = inject(AuthService);
  const orgCtx = inject(OrganizationContextService);

  const isPresentation = (): boolean => {
    const user = auth.getUser();
    const username = (user?.username ?? '').toLowerCase();
    if (username === 'demo.business') return true;
    return user?.preferences?.presentation_nav === true;
  };

  const can = (code: string): boolean => !isPresentation() && orgCtx.hasPermission(code);

  return {
    isPresentation,
    isReadOnly: (): boolean => isPresentation(),
    canApprove: (): boolean => can('royalty.approve'),
    canSettle: (): boolean => can('royalty.settle'),
    canPayout: (): boolean => can('royalty.payout'),
    canManagePool: (): boolean => can('royalty.pool.manage'),
  };
}
