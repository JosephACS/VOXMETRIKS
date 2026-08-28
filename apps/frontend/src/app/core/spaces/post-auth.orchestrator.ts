import { Injectable, inject } from '@angular/core';
import { Router } from '@angular/router';
import { ProfileSwitchService } from '../../packages/personal-account/services/profile-switch.service';
import { consumeReturnUrl, isSafeReturnUrl, peekReturnUrl } from './return-url';
import {
  SessionBootstrap,
  kindRequiredByPath,
  pendingHas,
} from './session-bootstrap.model';
import { SpaceContextService } from './space-context.service';

export function returnUrlAllowedForManifest(
  returnUrl: string,
  manifest: SessionBootstrap,
): boolean {
  if (!isSafeReturnUrl(returnUrl)) return false;
  const needed = kindRequiredByPath(returnUrl);
  if (!needed) {
    return returnUrl.startsWith('/');
  }
  return manifest.spaces.some((s) => s.kind === needed);
}

/** Keep previously issued product links usable after route consolidation. */
export function canonicalPostAuthPath(path: string): string {
  if (!isSafeReturnUrl(path)) return path;
  const parsed = new URL(path, 'https://voxmetriks.local');
  if (parsed.pathname !== '/home') return path;
  return `/discover${parsed.search}${parsed.hash}`;
}

export function resolvePostAuthPath(input: {
  manifest: SessionBootstrap;
  returnUrl: string | null;
  householdPath: string | null;
}): string {
  const { manifest, returnUrl, householdPath } = input;
  if (returnUrl && returnUrlAllowedForManifest(returnUrl, manifest)) {
    const canonicalReturnUrl = canonicalPostAuthPath(returnUrl);
    const needed = kindRequiredByPath(canonicalReturnUrl);
    if (needed === 'personal' && householdPath) return householdPath;
    return canonicalReturnUrl;
  }
  if (pendingHas(manifest, 'choose_space') && manifest.spaces.length > 1) {
    return '/welcome/spaces';
  }
  if (pendingHas(manifest, 'first_run')) {
    return '/welcome';
  }
  const recommended = manifest.recommended_path || '/discover';
  if (kindRequiredByPath(recommended) === 'personal' && householdPath) {
    return householdPath;
  }
  return recommended;
}

export function extractInvitationNavigation(path: string): {
  path: string;
  invitationToken: string;
} | null {
  if (!isSafeReturnUrl(path)) return null;
  const parsed = new URL(path, 'https://voxmetriks.local');
  if (
    parsed.pathname !== '/invitations/accept' &&
    parsed.pathname !== '/artist-invitations/accept'
  ) {
    return null;
  }
  const invitationToken = parsed.searchParams.get('token')?.trim() ?? '';
  if (!invitationToken) return null;
  parsed.searchParams.delete('token');
  const query = parsed.searchParams.toString();
  return {
    path: `${parsed.pathname}${query ? `?${query}` : ''}${parsed.hash}`,
    invitationToken,
  };
}

@Injectable({ providedIn: 'root' })
export class PostAuthOrchestrator {
  private readonly spaces = inject(SpaceContextService);
  private readonly household = inject(ProfileSwitchService);
  private readonly router = inject(Router);

  /**
   * Throws (SessionBootstrapError) when the manifest cannot be loaded. The captured
   * returnUrl survives that failure so a retry can still land on the intended page.
   */
  async afterAuthenticated(): Promise<string> {
    const manifest = await this.spaces.bootstrapFromSession();
    const returnUrl = peekReturnUrl();
    const personalDest =
      !returnUrl ||
      kindRequiredByPath(returnUrl) === 'personal' ||
      !returnUrlAllowedForManifest(returnUrl, manifest);
    let householdPath: string | null = null;
    if (personalDest) {
      const resolved = await this.household.resolvePostLoginDestination('/discover');
      householdPath = resolved === '/account/profiles' ? resolved : null;
    }
    const path = resolvePostAuthPath({ manifest, returnUrl, householdPath });
    // Destination is final now, so the pending returnUrl must not replay later.
    consumeReturnUrl();
    return path;
  }

  async goAfterAuthenticated(): Promise<void> {
    const path = await this.afterAuthenticated();
    const invitation = extractInvitationNavigation(path);
    if (invitation) {
      await this.router.navigateByUrl(invitation.path, {
        state: { invitationToken: invitation.invitationToken },
      });
      return;
    }
    await this.router.navigateByUrl(path);
  }
}
