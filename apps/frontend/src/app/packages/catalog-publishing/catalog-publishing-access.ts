import { inject } from '@angular/core';
import { AuthService } from '../../core/services/auth.service';
import { OrganizationContextService } from '../organizations/services/organization-context.service';

/** Artist portal / Spec 031 access helpers. */
export function catalogPublishingAccess() {
  const auth = inject(AuthService);
  const orgCtx = inject(OrganizationContextService);

  const isArtistPortalDemo = (): boolean => {
    const user = auth.getUser();
    const username = (user?.username ?? '').toLowerCase();
    if (username === 'demo.artist') return true;
    const role = (user?.preferences?.presentation_role ?? '').toLowerCase();
    if (role === 'artist' || role === 'artist_portal') return true;
    return false;
  };

  const can = (code: string): boolean => orgCtx.hasPermission(code);

  return {
    isArtistPortalDemo,
    canView: (): boolean => can('publishing.view') || isArtistPortalDemo(),
    canCreate: (): boolean => can('publishing.create') || isArtistPortalDemo(),
    canSubmit: (): boolean => can('publishing.submit') || isArtistPortalDemo(),
    canReview: (): boolean => can('publishing.review'),
    canPublish: (): boolean => can('publishing.publish'),
    canViewContracts: (): boolean =>
      can('catalog.view') || can('rights.view') || can('contract.view') || can('publishing.view'),
    isReadOnlyRoyalties: (): boolean => isArtistPortalDemo(),
  };
}
