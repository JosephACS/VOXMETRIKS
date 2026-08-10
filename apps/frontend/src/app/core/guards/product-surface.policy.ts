/**
 * Pure product-surface decisions (038 + 045). No Angular DI.
 */

import {
  classifyProductDeepLink,
  type NavAccessContext,
} from '../navigation/nav-access.policy';
import { spaceAllowsProductPath } from '../spaces/space-access.policy';
import type { SpaceKind } from '../spaces/space.models';

export type ProductSurfaceDecision = 'allow' | 'staff-block' | 'unavailable';

export interface PresentationAuthUser {
  username?: string | null;
  preferences?: { presentation_nav?: boolean; presentation_role?: string } | null;
}

export function presentationModeFromUser(user: PresentationAuthUser | null | undefined): boolean {
  const username = (user?.username || '').toLowerCase();
  const prefs = user?.preferences;
  return !!(
    prefs?.presentation_nav ||
    prefs?.presentation_role ||
    username === 'demo.business' ||
    username === 'demo.artist' ||
    username === 'finance.manager'
  );
}

/**
 * Spec 038 OUT_OF_PRODUCT + Spec 045 space exceptions.
 * Staff blocks still win over space allowlists.
 */
export function decideProductSurfaceAccess(
  path: string,
  ctx: NavAccessContext,
  activeSpaceKind: SpaceKind | null | undefined,
): ProductSurfaceDecision {
  if (spaceAllowsProductPath(path, activeSpaceKind)) {
    const staffOrAllow = classifyProductDeepLink(path, ctx);
    // Organization reporting has its own membership + permission check in
    // staffCapabilityGuard. Let that authoritative UX gate decide instead of
    // rejecting valid organization owners as identity-only listeners.
    const normalized = (path || '').split('?')[0];
    const organizationReporting =
      activeSpaceKind === 'organization' &&
      (normalized === '/reports' ||
        normalized.startsWith('/reports/') ||
        normalized === '/business-decisions' ||
        normalized.startsWith('/business-decisions/'));
    if (organizationReporting) return 'allow';
    if (staffOrAllow === 'staff-block') return 'staff-block';
    return 'allow';
  }
  return classifyProductDeepLink(path, ctx);
}
