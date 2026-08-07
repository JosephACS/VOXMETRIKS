/**
 * Espacios de producto (045) — tipos puros, sin DI.
 * Distintos del rol de identidad (user|admin|engineer) y de roles org RBAC.
 */

export type SpaceKind =
  | 'personal'
  | 'organization'
  | 'artist'
  | 'data_ops'
  | 'platform_admin';

export interface AppSpace {
  /** Stable id, e.g. personal | org:12 | data_ops | platform_admin | artist:5 */
  id: string;
  kind: SpaceKind;
  /** Human-readable label (never raw role codes). */
  label: string;
  organizationId?: number;
  artistProfileId?: number;
}

export interface PersistedSpaceRef {
  id: string;
  kind: SpaceKind;
  organizationId?: number;
  artistProfileId?: number;
}

export const SPACE_STORAGE_KEY = 'voxmetriks_active_space_v1';

export function personalSpace(label = 'Personal'): AppSpace {
  return { id: 'personal', kind: 'personal', label };
}

export function organizationSpace(orgId: number, label: string): AppSpace {
  return {
    id: `org:${orgId}`,
    kind: 'organization',
    label,
    organizationId: orgId,
  };
}

export function dataOpsSpace(label = 'Data Ops'): AppSpace {
  return { id: 'data_ops', kind: 'data_ops', label };
}

export function platformAdminSpace(label = 'Administración'): AppSpace {
  return { id: 'platform_admin', kind: 'platform_admin', label };
}

export function artistSpace(artistId: number, label: string): AppSpace {
  return {
    id: `artist:${artistId}`,
    kind: 'artist',
    label,
    artistProfileId: artistId,
  };
}

export function homePathForSpace(space: AppSpace): string {
  switch (space.kind) {
    case 'personal':
      return '/discover';
    case 'organization':
      return space.organizationId != null
        ? `/organizations/${space.organizationId}`
        : '/discover';
    case 'artist':
      return space.artistProfileId != null
        ? `/artist-profiles/${space.artistProfileId}`
        : '/discover';
    case 'data_ops':
      return '/elt-pipeline';
    case 'platform_admin':
      return '/platform-ops';
    default:
      return '/discover';
  }
}
