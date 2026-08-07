/**
 * Central navigation / route-access policy (specs 034 + 038).
 * Pure helpers — no Angular DI. Menu visibility and route guards share this.
 *
 * Identity roles (app_user.role): user | admin | engineer
 * Spec 038: product-final visibility — demos out of menu/deep-link product surface.
 */

export type IdentityRole = 'user' | 'admin' | 'engineer' | string;

/** Routes that require staff identity (admin/engineer) or platform admin. */
export const STAFF_REPORT_PATH_PREFIXES: readonly string[] = [
  '/workpanel',
  '/simple-reports',
  '/complex-reports',
  '/reports',
  '/business-decisions',
];

/** Analytics hub / legacy dashboards — redirect to Workpanel (038); staff-gated meanwhile. */
export const STAFF_ANALYTICS_PATH_PREFIXES: readonly string[] = [
  '/dashboard',
  '/insights/analytics',
  '/insights/tracks',
  '/analytics',
  '/trending',
  '/comparatives',
];

/** Engineering tools — engineer or admin identity, or platform_admin. */
export const ENGINEERING_PATH_PREFIXES: readonly string[] = [
  '/elt-pipeline',
  '/etl-pipeline',
  '/explorer',
];

/**
 * Enterprise demos outside MVP product surface (036/038).
 * Keep backends; hide menu; deep-link → module unavailable (unless presentationMode).
 */
export const OUT_OF_PRODUCT_PATH_PREFIXES: readonly string[] = [
  '/crm',
  '/billing',
  '/royalties',
  '/payouts',
  '/campaigns',
  '/business-analytics',
  '/customer-success',
  '/support',
  '/subscriptions',
  '/compliance',
  // Spec 043: `/reports` is the product hub (simples + complejos). Keep decisions demo-blocked.
  '/business-decisions',
];

/** Nav section ids kept in the product-final shell (038). */
export const PRODUCT_FINAL_SECTION_IDS: ReadonlySet<string> = new Set([
  'main',
  'music',
  'personalAccount',
  'data',
  'organizations',
  'catalogHub',
  'artistPortal',
  'artistProfiles',
  'catalogRights',
  'reporting',
  'platformOps',
]);

/** Nav section ids treated as demos / out of product final. */
export const DEMO_SECTION_IDS: ReadonlySet<string> = new Set([
  'crm',
  'billing',
  'royalties',
  'campaigns',
  'businessAnalytics',
  'customerSuccess',
  'subscriptions',
  'compliance',
  'analytics',
  'recommendations',
  'artistContracts',
  'artistPublishing',
]);

/** Legacy path → canonical product path (038). Query string preserved by router. */
export const CANONICAL_REDIRECTS: ReadonlyArray<{ from: string; to: string }> = [
  { from: '/dashboard', to: '/workpanel' },
  { from: '/dashboard/analytics', to: '/workpanel' },
  { from: '/insights/analytics', to: '/workpanel' },
  { from: '/insights/tracks', to: '/reports?type=complex' },
  { from: '/analytics', to: '/workpanel' },
  { from: '/trending', to: '/reports?type=complex' },
  { from: '/comparatives', to: '/reports?type=complex' },
  { from: '/etl-pipeline', to: '/elt-pipeline' },
];

/**
 * Spec 043 — soft hub redirects for exact catalog paths only.
 * Query-bearing deep links to /simple-reports and /complex-reports stay on those routes.
 */
export const HUB_MENU_PATHS = {
  reports: '/reports',
  catalog: '/catalog',
} as const;

/** Principal (main) paths for staff product-final nav (043: Workpanel only in sidebar). */
export const STAFF_MAIN_PRODUCT_PATHS: ReadonlySet<string> = new Set([
  '/workpanel',
]);

/** Music nav items always available to authenticated listeners (incl. activity). */
export const LISTENER_MUSIC_EXTRA_PATHS: ReadonlySet<string> = new Set([
  '/activity',
]);

/** Music nav items that are technical — hide from pure listeners. */
export const LISTENER_HIDDEN_MUSIC_PATHS: ReadonlySet<string> = new Set([
  '/audio-features',
  '/artists',
  '/genres',
]);

/** Principal items allowed for pure listeners. */
export const LISTENER_MAIN_PATHS: ReadonlySet<string> = new Set([
  '/discover',
  '/search',
]);

/** Library paths for listeners (043). */
export const LISTENER_LIBRARY_PATHS: ReadonlySet<string> = new Set([
  '/tracks',
  '/playlists',
  '/liked',
  '/history',
  '/activity',
]);

/** Account paths for listeners (043) — settings only in sidebar; plans via user menu if needed. */
export const LISTENER_ACCOUNT_PATHS: ReadonlySet<string> = new Set([
  '/settings',
]);

/** Reporting items kept in product-final nav (043 hub). */
export const PRODUCT_REPORTING_PATHS: ReadonlySet<string> = new Set([
  '/reports',
  '/simple-reports',
  '/complex-reports',
]);

/** Platform ops / unresolved — not primary nav (043). */
export const HIDDEN_PRIMARY_OPS_PATHS: ReadonlySet<string> = new Set([
  '/platform-ops',
  '/platform-ops/unresolved-audio',
]);

export interface NavAccessContext {
  identityRole: IdentityRole;
  /** Platform CRM role platform_admin */
  platformAdmin?: boolean;
  /** Presentation / artist / finance demo modes bypass some filters in layout */
  presentationMode?: boolean;
}

export function normalizeIdentityRole(role: string | null | undefined): IdentityRole {
  return (role || 'user').toLowerCase();
}

export function isStaffIdentity(role: IdentityRole): boolean {
  const r = normalizeIdentityRole(role);
  return r === 'admin' || r === 'engineer';
}

export function hasEngineeringNavAccess(ctx: NavAccessContext): boolean {
  return isStaffIdentity(ctx.identityRole) || !!ctx.platformAdmin;
}

export function hasStaffReportsNavAccess(ctx: NavAccessContext): boolean {
  return isStaffIdentity(ctx.identityRole) || !!ctx.platformAdmin;
}

export function pathMatchesPrefixes(path: string, prefixes: readonly string[]): boolean {
  const p = (path || '').split('?')[0];
  return prefixes.some((prefix) => p === prefix || p.startsWith(prefix + '/'));
}

export function isOutOfProductPath(path: string): boolean {
  return pathMatchesPrefixes(path, OUT_OF_PRODUCT_PATH_PREFIXES);
}

export function resolveCanonicalRedirect(path: string): string | null {
  const p = (path || '').split('?')[0];
  const hit = CANONICAL_REDIRECTS.find(
    (r) => p === r.from || p.startsWith(r.from + '/'),
  );
  return hit ? hit.to : null;
}

/** Whether the user may open this path via deep link (route guard). */
export function canActivateStaffPath(path: string, ctx: NavAccessContext): boolean {
  if (ctx.presentationMode) {
    return true;
  }
  if (pathMatchesPrefixes(path, ENGINEERING_PATH_PREFIXES)) {
    return hasEngineeringNavAccess(ctx);
  }
  if (pathMatchesPrefixes(path, STAFF_REPORT_PATH_PREFIXES)) {
    return hasStaffReportsNavAccess(ctx);
  }
  if (pathMatchesPrefixes(path, STAFF_ANALYTICS_PATH_PREFIXES)) {
    return hasStaffReportsNavAccess(ctx);
  }
  return true;
}

/**
 * Product-final deep links: demos blocked unless presentationMode.
 * Returns 'allow' | 'staff-block' | 'unavailable'.
 */
export function classifyProductDeepLink(
  path: string,
  ctx: NavAccessContext,
): 'allow' | 'staff-block' | 'unavailable' {
  if (ctx.presentationMode) return 'allow';
  if (isOutOfProductPath(path)) return 'unavailable';
  if (!canActivateStaffPath(path, ctx)) return 'staff-block';
  return 'allow';
}

export interface NavItemLike {
  path: string;
}

/**
 * Filter principal (main) section items for non-presentation users.
 * Spec 043: admin → Workpanel; engineer → Estado técnico + Workpanel; listener → Descubrir + Buscar.
 */
export function filterMainNavItems<T extends NavItemLike>(
  items: T[],
  ctx: NavAccessContext,
): T[] {
  if (ctx.presentationMode) return items;
  const role = normalizeIdentityRole(ctx.identityRole);
  if (role === 'engineer') {
    return items.filter((item) => {
      const p = item.path.split('?')[0];
      return p === '/elt-pipeline' || (p === '/workpanel' && hasStaffReportsNavAccess(ctx));
    });
  }
  if (hasStaffReportsNavAccess(ctx)) {
    return items.filter((item) => STAFF_MAIN_PRODUCT_PATHS.has(item.path.split('?')[0]));
  }
  return items.filter((item) => LISTENER_MAIN_PATHS.has(item.path.split('?')[0]));
}

/**
 * Filter music section — drop technical tools for pure listeners.
 */
export function filterMusicNavItems<T extends NavItemLike>(
  items: T[],
  ctx: NavAccessContext,
): T[] {
  if (ctx.presentationMode || isStaffIdentity(ctx.identityRole)) return items;
  return items.filter((item) => !LISTENER_HIDDEN_MUSIC_PATHS.has(item.path.split('?')[0]));
}

/** Filter reporting section to product hub only (043). */
export function filterReportingNavItems<T extends NavItemLike>(
  items: T[],
  ctx: NavAccessContext,
): T[] {
  if (ctx.presentationMode) return items;
  if (!hasStaffReportsNavAccess(ctx)) return [];
  // Prefer single hub entry; keep legacy paths if present for presentation demos.
  const hub = items.filter((item) => item.path.split('?')[0] === '/reports');
  if (hub.length) return hub;
  return items.filter((item) => PRODUCT_REPORTING_PATHS.has(item.path.split('?')[0]));
}

/** Listener library filter (043). */
export function filterListenerLibraryItems<T extends NavItemLike>(items: T[]): T[] {
  return items.filter((item) => LISTENER_LIBRARY_PATHS.has(item.path.split('?')[0]));
}

/** Listener account filter (043) — settings only in sidebar. */
export function filterListenerAccountItems<T extends NavItemLike>(items: T[]): T[] {
  return items.filter((item) => LISTENER_ACCOUNT_PATHS.has(item.path.split('?')[0]));
}

/** Whether platform ops belong in primary sidebar (043: never). */
export function showPlatformOpsInPrimaryNav(ctx: NavAccessContext): boolean {
  if (ctx.presentationMode) return true;
  return false;
}

/** Whether the analytics sidebar section should appear (038: never in product final). */
export function showAnalyticsSection(ctx: NavAccessContext): boolean {
  if (ctx.presentationMode) return false;
  // Legacy analytics hubs redirected; do not show duplicate section.
  return false;
}

/** Whether reporting / business-decisions sidebar section should appear. */
export function showReportingSection(ctx: NavAccessContext): boolean {
  return hasStaffReportsNavAccess(ctx);
}

/** Whether a nav section id belongs in the product-final shell. */
export function isProductFinalSection(sectionId: string, ctx: NavAccessContext): boolean {
  if (ctx.presentationMode) return true;
  if (DEMO_SECTION_IDS.has(sectionId)) return false;
  return PRODUCT_FINAL_SECTION_IDS.has(sectionId);
}

/**
 * Engineer-focused: hide commercial org demos already covered by DEMO_SECTION_IDS;
 * data tools remain via section filter in layout.
 */
export function isEngineerCommercialSection(sectionId: string): boolean {
  return (
    sectionId === 'crm' ||
    sectionId === 'billing' ||
    sectionId === 'royalties' ||
    sectionId === 'campaigns' ||
    sectionId === 'subscriptions' ||
    sectionId === 'customerSuccess' ||
    sectionId === 'businessAnalytics'
  );
}

export function homePathForRole(role: IdentityRole): string {
  void role;
  return '/discover';
}
