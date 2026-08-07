import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { ArtistContextService } from '../services/artist-context.service';
import { SpaceContextService } from '../../../core/spaces/space-context.service';
import { ArtistSpacePermission } from '../models/artist-space.models';

/** Requires an active artist space (membership-backed). */
export const artistRequiredGuard: CanActivateFn = async () => {
  const artistCtx = inject(ArtistContextService);
  const spaceCtx = inject(SpaceContextService);
  const router = inject(Router);

  await spaceCtx.ensureReady();
  if (artistCtx.hasArtist()) return true;

  const active = spaceCtx.activeSpace();
  if (active?.kind === 'artist' && active.artistProfileId != null) {
    await spaceCtx.bootstrap({ force: true });
    if (artistCtx.hasArtist()) return true;
  }
  return router.createUrlTree(['/artist-space/claim']);
};

export function artistPermissionGuard(
  permission: ArtistSpacePermission | string,
): CanActivateFn {
  return async () => {
    const artistCtx = inject(ArtistContextService);
    const spaceCtx = inject(SpaceContextService);
    const router = inject(Router);

    await spaceCtx.ensureReady();
    if (!artistCtx.hasArtist()) {
      return router.createUrlTree(['/artist-space/claim']);
    }
    if (artistCtx.can(permission)) return true;
    return router.createUrlTree(['/access-denied']);
  };
}
