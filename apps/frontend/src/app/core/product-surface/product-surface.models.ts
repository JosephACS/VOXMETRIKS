/**
 * Spec 054 — typed product-surface registry models.
 * Presentation metadata only; backend RBAC remains authoritative.
 */

import type { SpaceKind } from '../spaces/space.models';
import type { SpaceNavIconId } from '../spaces/space-nav.icons';

/** Minimum org subscription tier required (maps to OrgAccessTier; recovery preserved). */
export type ProductOrganizationTier = 'onboarding' | 'recovery' | 'operational';

export interface ProductSurfaceDefinition {
  id: string;
  labelKey: string;
  iconId: SpaceNavIconId;
  /** Static path or `/organizations/:id…` template resolved with organizationId. */
  path: string;
  spaces: readonly SpaceKind[];
  /** Minimum organization tier when the surface is organization-scoped. */
  organizationTier?: ProductOrganizationTier;
  /** Org membership permission OR artist capability code (checked against the matching set). */
  capability?: string;
  /** At least one of these capability codes must be present. */
  capabilitiesAny?: readonly string[];
  /** Every listed capability code must be present. */
  capabilitiesAll?: readonly string[];
  /** Staff shell capability (e.g. identity.staff). */
  staffCapability?: string;
  /** Platform CRM role required (e.g. platform_admin). */
  platformRole?: string;
  /** Module-context tab group id. */
  contextGroup?: string;
  /** Sidebar section grouping. */
  sectionId: string;
  sectionTitleKey: string;
  order: number;
  exact?: boolean;
  /** Optional human tab label when contextGroup is used (chrome may use Spanish literals today). */
  tabLabel?: string;
  matchPrefixes?: readonly string[];
}

export interface ProductSurfaceContext {
  ready: boolean;
  activeSpace: SpaceKind;
  organizationId?: number;
  organizationTier?: ProductOrganizationTier;
  permissions: ReadonlySet<string>;
  artistCapabilities: ReadonlySet<string>;
  staffCapabilities: ReadonlySet<string>;
  platformRoles: ReadonlySet<string>;
}

export type ProductSurfaceVerdict = 'allow' | 'deny';

/** Path-level access for productSurfaceGuard (Spec 054 audit). */
export type ProductPathAccessResult =
  | 'allow'
  | 'unregistered'
  | 'permission-denied'
  | 'unavailable';

/** Canonical staff capability codes hydrated from identity (not org RBAC). */
export const STAFF_CAPABILITY = {
  shell: 'identity.staff',
  engineering: 'identity.engineering',
} as const;
