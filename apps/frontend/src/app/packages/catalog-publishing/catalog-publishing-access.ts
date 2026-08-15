import { inject } from '@angular/core';
import { OrganizationContextService } from '../organizations/services/organization-context.service';

/** Catalog publishing access — permission-only (Spec 054: no demo.artist bypass). */
export function catalogPublishingAccess() {
  const orgCtx = inject(OrganizationContextService);

  const can = (code: string): boolean => orgCtx.hasPermission(code);

  return {
    isArtistPortalDemo: (): boolean => false,
    canView: (): boolean => can('publishing.view'),
    canCreate: (): boolean => can('publishing.create'),
    canSubmit: (): boolean => can('publishing.submit'),
    canReview: (): boolean => can('publishing.review'),
    canPublish: (): boolean => can('publishing.publish'),
    canViewContracts: (): boolean =>
      can('catalog.view') || can('rights.view') || can('contract.view') || can('publishing.view'),
    isReadOnlyRoyalties: (): boolean => false,
  };
}
