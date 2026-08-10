/**
 * Pure helpers for building / validating product spaces (045).
 * No Angular DI — unit-test friendly.
 */

import {
  AppSpace,
  PersistedSpaceRef,
  SpaceKind,
  dataOpsSpace,
  organizationSpace,
  personalSpace,
  platformAdminSpace,
} from './space.models';

export interface SpaceEligibilityInput {
  /** Always true when authenticated. */
  authenticated: boolean;
  /** Identity role: user | admin | engineer */
  identityRole: string;
  hasEngineerAccess: boolean;
  /** identity admin OR CRM platform_admin */
  hasPlatformAdminSpace: boolean;
  organizations: ReadonlyArray<{ id: number; name: string }>;
  /** Real artist memberships only — empty until backend exists. */
  artistMemberships: ReadonlyArray<{ id: number; name: string }>;
  personalLabel?: string;
  dataOpsLabel?: string;
  platformAdminLabel?: string;
}

export function buildAvailableSpaces(input: SpaceEligibilityInput): AppSpace[] {
  if (!input.authenticated) return [];

  const spaces: AppSpace[] = [
    personalSpace(input.personalLabel ?? 'Personal'),
  ];

  for (const org of input.organizations) {
    if (org?.id == null) continue;
    spaces.push(organizationSpace(org.id, org.name || `Organización ${org.id}`));
  }

  // Artist spaces: only when real memberships are supplied (never invent).
  for (const artist of input.artistMemberships) {
    if (artist?.id == null) continue;
    spaces.push({
      id: `artist:${artist.id}`,
      kind: 'artist',
      label: artist.name || `Artista ${artist.id}`,
      artistProfileId: artist.id,
    });
  }

  if (input.hasEngineerAccess) {
    spaces.push(dataOpsSpace(input.dataOpsLabel ?? 'Data Ops'));
  }

  if (input.hasPlatformAdminSpace) {
    spaces.push(
      platformAdminSpace(input.platformAdminLabel ?? 'Administración de plataforma'),
    );
  }

  return spaces;
}

export function findSpaceById(
  spaces: readonly AppSpace[],
  id: string | null | undefined,
): AppSpace | null {
  if (!id) return null;
  return spaces.find((s) => s.id === id) ?? null;
}

export function isPersistedSpaceStillValid(
  ref: PersistedSpaceRef | null | undefined,
  spaces: readonly AppSpace[],
): AppSpace | null {
  if (!ref?.id || !ref.kind) return null;
  const found = findSpaceById(spaces, ref.id);
  if (!found) return null;
  if (found.kind !== ref.kind) return null;
  if (
    found.kind === 'organization' &&
    ref.organizationId != null &&
    found.organizationId !== ref.organizationId
  ) {
    return null;
  }
  if (
    found.kind === 'artist' &&
    ref.artistProfileId != null &&
    found.artistProfileId !== ref.artistProfileId
  ) {
    return null;
  }
  return found;
}

export function toPersistedRef(space: AppSpace): PersistedSpaceRef {
  return {
    id: space.id,
    kind: space.kind,
    organizationId: space.organizationId,
    artistProfileId: space.artistProfileId,
  };
}

/**
 * Paths historically OUT_OF_PRODUCT that become reachable in organization space
 * (nav + deep link) while backend RBAC remains authoritative.
 */
export const ORGANIZATION_SPACE_ALLOWED_PREFIXES: readonly string[] = [
  '/campaigns',
  '/business-analytics',
  '/billing',
  '/reports',
  '/business-decisions',
  '/royalties',
  '/payouts',
  '/subscriptions',
];

export function isOrganizationSpaceCommercialPath(path: string): boolean {
  const p = (path || '').split('?')[0];
  return ORGANIZATION_SPACE_ALLOWED_PREFIXES.some(
    (prefix) => p === prefix || p.startsWith(prefix + '/'),
  );
}

export function spaceAllowsProductPath(
  path: string,
  spaceKind: SpaceKind | null | undefined,
): boolean {
  if (spaceKind === 'organization' && isOrganizationSpaceCommercialPath(path)) {
    return true;
  }
  if (spaceKind === 'platform_admin') {
    const p = (path || '').split('?')[0];
    if (p === '/platform-ops' || p.startsWith('/platform-ops/')) return true;
  }
  if (spaceKind === 'artist') {
    const p = (path || '').split('?')[0];
    if (p === '/artist-space' || p.startsWith('/artist-space/')) return true;
  }
  if (spaceKind === 'data_ops') {
    const p = (path || '').split('?')[0];
    if (
      p === '/elt-pipeline' ||
      p === '/etl-pipeline' ||
      p === '/explorer' ||
      p === '/workpanel' ||
      p === '/reports' ||
      p.startsWith('/reports/') ||
      p === '/simple-reports' ||
      p === '/complex-reports'
    ) {
      return true;
    }
  }
  return false;
}
