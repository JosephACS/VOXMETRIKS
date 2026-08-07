/**
 * Central B2B module access — UI gating only.
 * Backend remains the source of truth for every API call.
 */

export type OrgSubscriptionStatus =
  | 'trialing'
  | 'active'
  | 'past_due'
  | 'canceled'
  | 'expired'
  | 'suspended'
  | string;

export type OrgAccessState = 'full' | 'limited' | 'blocked' | string;

/** How far the org may go in the product shell. */
export type OrgAccessTier = 'none' | 'onboarding' | 'recovery' | 'operational';

export type OrgModuleKind =
  | 'onboarding'
  | 'recovery'
  | 'operational'
  | 'org_admin_basic'
  | 'org_admin_advanced';

export interface OrgMembershipSnapshot {
  active: boolean;
  permissions: readonly string[];
  roles?: readonly string[];
}

export interface OrgSubscriptionSnapshot {
  /** True when any row exists (including canceled/expired). */
  has_subscription: boolean;
  status: OrgSubscriptionStatus | null;
  access_state: OrgAccessState | null;
  /** Enabled entitlement feature codes from the active-like subscription, when known. */
  entitlements?: readonly string[] | null;
}

export interface CanAccessOrganizationModuleInput {
  authenticated: boolean;
  membership: OrgMembershipSnapshot | null;
  organizationSubscription: OrgSubscriptionSnapshot | null;
  /** Org RBAC permission required for the module (e.g. invoice.view). */
  requiredPermission?: string | null;
  /** Plan entitlement feature code when the module is plan-gated. */
  requiredCapability?: string | null;
  moduleKind: OrgModuleKind;
}

const ACTIVE_LIKE = new Set(['trialing', 'active']);
const RECOVERY_STATUSES = new Set(['past_due', 'canceled', 'expired', 'suspended']);

export function resolveOrgAccessTier(
  subscription: OrgSubscriptionSnapshot | null | undefined,
): OrgAccessTier {
  if (!subscription?.has_subscription || !subscription.status) {
    return 'onboarding';
  }
  const status = String(subscription.status).toLowerCase();
  const access = String(subscription.access_state ?? 'full').toLowerCase();

  if (ACTIVE_LIKE.has(status)) {
    if (access === 'blocked') return 'recovery';
    if (access === 'limited') return 'recovery';
    return 'operational';
  }
  if (RECOVERY_STATUSES.has(status)) return 'recovery';
  return 'onboarding';
}

function tierAllows(tier: OrgAccessTier, moduleKind: OrgModuleKind): boolean {
  switch (moduleKind) {
    case 'onboarding':
    case 'org_admin_basic':
      return tier === 'onboarding' || tier === 'recovery' || tier === 'operational';
    case 'recovery':
      return tier === 'recovery' || tier === 'operational';
    case 'org_admin_advanced':
    case 'operational':
      return tier === 'operational';
    default:
      return false;
  }
}

/**
 * Single gate for enterprise modules in the shell (nav + route guards).
 *
 * Requires: authenticated + active membership + authorized permission (when set)
 * + org subscription tier matching the module + optional plan capability.
 */
export function canAccessOrganizationModule(
  input: CanAccessOrganizationModuleInput,
): boolean {
  if (!input.authenticated) return false;
  const membership = input.membership;
  if (!membership?.active) return false;

  const tier = resolveOrgAccessTier(input.organizationSubscription);
  if (!tierAllows(tier, input.moduleKind)) return false;

  const perm = input.requiredPermission?.trim();
  if (perm && !membership.permissions.includes(perm)) return false;

  const cap = input.requiredCapability?.trim();
  if (cap) {
    const entitlements = input.organizationSubscription?.entitlements;
    // If entitlements were not loaded, do not invent access — require known enablement.
    if (!entitlements || !entitlements.includes(cap)) return false;
  }

  return true;
}

/** True when the user has membership but no usable trial/paid subscription yet. */
export function isOrgAwaitingPlan(
  subscription: OrgSubscriptionSnapshot | null | undefined,
): boolean {
  return resolveOrgAccessTier(subscription) === 'onboarding';
}

/** True when subscription is past_due / canceled / limited — recovery UI only. */
export function isOrgInRecovery(
  subscription: OrgSubscriptionSnapshot | null | undefined,
): boolean {
  return resolveOrgAccessTier(subscription) === 'recovery';
}
