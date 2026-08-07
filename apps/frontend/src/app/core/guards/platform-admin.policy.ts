/**
 * Platform Admin eligibility (Spec 045) — pure, aligned with SpaceContextService.
 *
 * Data Ops uses hasEngineerAccess() (admin | engineer) separately.
 * Platform Admin must NOT treat pure engineer as authorized.
 */
export function canAccessPlatformAdmin(input: {
  isAdmin: boolean;
  crmRoles: readonly string[];
}): boolean {
  if (input.isAdmin) return true;
  return input.crmRoles.includes('platform_admin');
}
