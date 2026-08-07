/**
 * Spec 043 hotfix — resolve module context chrome from the current URL.
 * Pure helpers (no DI) for breadcrumb / back / secondary tabs.
 */

export interface ModuleTab {
  label: string;
  path: string;
  /** Match exact path only (hub resumen). */
  exact?: boolean;
  /** Prefixes that activate this tab (detail pages). */
  matchPrefixes?: readonly string[];
}

export interface BreadcrumbCrumb {
  label: string;
  path?: string;
  queryParams?: Record<string, string>;
}

export interface ModuleContextView {
  moduleId: 'catalog' | 'organization' | 'reports' | 'engineering';
  hubLabel: string;
  hubPath: string;
  hubQueryParams?: Record<string, string>;
  backLabel: string;
  /** Hide back on the hub itself. */
  showBack: boolean;
  crumbs: BreadcrumbCrumb[];
  tabs: ModuleTab[];
  activeTabPath: string | null;
  /** Optional secondary return (e.g. Workpanel). */
  secondaryBack?: { label: string; path: string; queryParams?: Record<string, string> };
}

const CATALOG_TABS: ModuleTab[] = [
  { label: 'Resumen', path: '/catalog', exact: true },
  {
    label: 'Artistas',
    path: '/artist-profiles',
    matchPrefixes: ['/artist-profiles', '/artist/profile'],
  },
  {
    label: 'Canciones',
    path: '/artist/tracks',
    matchPrefixes: ['/artist/tracks'],
  },
  {
    label: 'Lanzamientos',
    path: '/artist/releases',
    matchPrefixes: ['/artist/releases'],
  },
  {
    label: 'Publicar música',
    path: '/artist/releases/new',
    exact: true,
    matchPrefixes: ['/artist/releases/new'],
  },
  {
    label: 'Revisiones',
    path: '/catalog-review',
    matchPrefixes: ['/catalog-review'],
  },
  {
    label: 'Derechos y conflictos',
    path: '/catalog-rights/conflicts',
    matchPrefixes: ['/catalog-rights'],
  },
];

function pathOnly(url: string): string {
  return (url || '/').split('?')[0] || '/';
}

function matchesTab(path: string, tab: ModuleTab): boolean {
  if (tab.exact) {
    return path === tab.path;
  }
  if (tab.matchPrefixes?.length) {
    // Prefer more specific tabs (e.g. /artist/releases/new over /artist/releases)
    return tab.matchPrefixes.some(
      (p) => path === p || path.startsWith(p + '/') || (p === tab.path && path.startsWith(p)),
    );
  }
  return path === tab.path || path.startsWith(tab.path + '/');
}

function activeCatalogTab(path: string): ModuleTab | null {
  // Prefer longest / most specific match first
  const ordered = [...CATALOG_TABS].sort((a, b) => {
    const la = (a.matchPrefixes?.[0] || a.path).length;
    const lb = (b.matchPrefixes?.[0] || b.path).length;
    return lb - la;
  });
  // Special-case: new release is Publicar, not Lanzamientos
  if (path === '/artist/releases/new' || path.startsWith('/artist/releases/new/')) {
    return CATALOG_TABS.find((t) => t.path === '/artist/releases/new') || null;
  }
  if (path.startsWith('/artist/releases/') && path !== '/artist/releases') {
    return CATALOG_TABS.find((t) => t.path === '/artist/releases') || null;
  }
  for (const tab of ordered) {
    if (tab.path === '/artist/releases/new') continue;
    if (matchesTab(path, tab)) return tab;
  }
  return null;
}

function catalogContext(path: string): ModuleContextView | null {
  const isCatalogSurface =
    path === '/catalog' ||
    path.startsWith('/artist-profiles') ||
    path.startsWith('/artist/profile') ||
    path.startsWith('/artist/tracks') ||
    path.startsWith('/artist/releases') ||
    path.startsWith('/catalog-review') ||
    path.startsWith('/catalog-rights');

  if (!isCatalogSurface) return null;

  const tab = activeCatalogTab(path);
  const isHub = path === '/catalog';
  const crumbs: BreadcrumbCrumb[] = [{ label: 'Catálogo y publicación', path: '/catalog' }];

  if (!isHub && tab) {
    crumbs.push({
      label: tab.label,
      path: tab.path === path ? undefined : tab.path,
    });
  }

  // Detail layers
  if (path.match(/^\/artist\/releases\/[^/]+$/) && path !== '/artist/releases/new') {
    if (crumbs.length === 1) {
      crumbs.push({ label: 'Lanzamientos', path: '/artist/releases' });
    }
    crumbs.push({ label: 'Detalle' });
  } else if (path.match(/^\/catalog-review\/[^/]+$/)) {
    if (crumbs.length === 1 || crumbs[crumbs.length - 1]?.label !== 'Revisiones') {
      crumbs.push({ label: 'Revisiones', path: '/catalog-review' });
    }
    crumbs.push({ label: 'Detalle' });
  } else if (path.startsWith('/catalog-rights/assets')) {
    if (tab && crumbs[crumbs.length - 1]?.label !== tab.label) {
      /* already */
    }
    if (path !== '/catalog-rights/assets' && path.startsWith('/catalog-rights/assets/')) {
      crumbs.push({ label: 'Activo' });
    }
  } else if (path.startsWith('/catalog-rights/contracts')) {
    crumbs[crumbs.length - 1] = { label: 'Contratos', path: '/catalog-rights/contracts' };
    if (path !== '/catalog-rights/contracts') crumbs.push({ label: 'Detalle' });
  } else if (path.startsWith('/catalog-rights/conflicts')) {
    crumbs[crumbs.length - 1] = { label: 'Conflictos', path: '/catalog-rights/conflicts' };
    if (path !== '/catalog-rights/conflicts') crumbs.push({ label: 'Detalle' });
  } else if (path.startsWith('/catalog-rights/releases')) {
    crumbs[crumbs.length - 1] = { label: 'Lanzamientos (derechos)', path: '/catalog-rights/releases' };
  } else if (path.startsWith('/artist-profiles/') && path !== '/artist-profiles') {
    crumbs.push({ label: 'Perfil' });
  }

  return {
    moduleId: 'catalog',
    hubLabel: 'Catálogo y publicación',
    hubPath: '/catalog',
    backLabel: 'Volver a Catálogo y publicación',
    showBack: !isHub,
    crumbs,
    tabs: CATALOG_TABS,
    activeTabPath: tab?.path ?? (isHub ? '/catalog' : null),
  };
}

function orgContext(path: string): ModuleContextView | null {
  const m = path.match(/^\/organizations\/(\d+)(\/.*)?$/);
  if (!m) return null;
  const id = m[1];
  const rest = m[2] || '';
  const hubPath = `/organizations/${id}`;

  const tabs: ModuleTab[] = [
    { label: 'Resumen', path: hubPath, exact: true },
    { label: 'Perfil', path: `${hubPath}/settings`, matchPrefixes: [`${hubPath}/settings`] },
    { label: 'Miembros', path: `${hubPath}/members`, matchPrefixes: [`${hubPath}/members`] },
    {
      label: 'Invitaciones',
      path: `${hubPath}/invitations`,
      matchPrefixes: [`${hubPath}/invitations`],
    },
    { label: 'Auditoría', path: `${hubPath}/audit`, matchPrefixes: [`${hubPath}/audit`] },
  ];

  const isHub = rest === '';
  let sectionLabel = 'Resumen';
  let activeTabPath = hubPath;
  if (rest.startsWith('/settings')) {
    sectionLabel = 'Perfil';
    activeTabPath = `${hubPath}/settings`;
  } else if (rest.startsWith('/members')) {
    sectionLabel = 'Miembros';
    activeTabPath = `${hubPath}/members`;
  } else if (rest.startsWith('/invitations')) {
    sectionLabel = 'Invitaciones';
    activeTabPath = `${hubPath}/invitations`;
  } else if (rest.startsWith('/audit')) {
    sectionLabel = 'Auditoría';
    activeTabPath = `${hubPath}/audit`;
  } else if (rest.startsWith('/roles')) {
    sectionLabel = 'Roles';
    activeTabPath = `${hubPath}/roles`;
  }

  const crumbs: BreadcrumbCrumb[] = [{ label: 'Organización', path: hubPath }];
  if (!isHub) {
    crumbs.push({ label: sectionLabel });
  }

  return {
    moduleId: 'organization',
    hubLabel: 'Organización',
    hubPath,
    backLabel: 'Volver a Organización',
    showBack: !isHub,
    crumbs,
    tabs,
    activeTabPath,
  };
}

function reportsContext(
  path: string,
  query: Record<string, string>,
): ModuleContextView | null {
  const isReports =
    path === '/reports' ||
    path.startsWith('/simple-reports') ||
    path.startsWith('/complex-reports');
  if (!isReports) return null;

  const isSimple = path.startsWith('/simple-reports') || query['type'] === 'simple';
  const isComplex = path.startsWith('/complex-reports') || query['type'] === 'complex';
  const isHub = path === '/reports' && !query['type'];

  const tabs: ModuleTab[] = [
    { label: 'Informes simples', path: '/simple-reports' },
    { label: 'Informes complejos', path: '/complex-reports' },
  ];

  const crumbs: BreadcrumbCrumb[] = [{ label: 'Reportes', path: '/reports' }];
  let activeTabPath: string | null = null;

  if (isSimple || (path === '/reports' && query['type'] === 'simple')) {
    crumbs.push({ label: 'Informes simples', path: '/simple-reports' });
    activeTabPath = '/simple-reports';
    const report = query['report'];
    if (report) crumbs.push({ label: report });
  } else if (isComplex || (path === '/reports' && query['type'] === 'complex')) {
    crumbs.push({ label: 'Informes complejos', path: '/complex-reports' });
    activeTabPath = '/complex-reports';
    const report = query['report'];
    if (report) crumbs.push({ label: report });
  }

  const fromWp = query['from'] === 'workpanel' || query['context'] === 'workpanel';
  const secondaryBack = fromWp
    ? { label: 'Volver a Workpanel', path: '/workpanel' }
    : undefined;

  return {
    moduleId: 'reports',
    hubLabel: 'Reportes',
    hubPath: '/reports',
    backLabel: 'Volver a Reportes',
    showBack: !isHub,
    crumbs,
    tabs,
    activeTabPath: activeTabPath ?? (isHub ? null : '/simple-reports'),
    secondaryBack,
  };
}

function engineeringContext(path: string): ModuleContextView | null {
  const isEng =
    path.startsWith('/elt-pipeline') ||
    path.startsWith('/explorer') ||
    path.startsWith('/platform-ops');
  if (!isEng) return null;

  // Keep Ops out of primary tabs; only show when already on that surface
  const tabs: ModuleTab[] = [
    {
      label: 'Ingeniería de datos',
      path: '/elt-pipeline',
      matchPrefixes: ['/elt-pipeline'],
    },
    {
      label: 'Explorador del almacén',
      path: '/explorer',
      matchPrefixes: ['/explorer'],
    },
  ];

  const isElt = path.startsWith('/elt-pipeline');
  const isExplorer = path.startsWith('/explorer');
  const isOps = path.startsWith('/platform-ops');

  const crumbs: BreadcrumbCrumb[] = [{ label: 'Datos', path: '/elt-pipeline' }];
  if (isExplorer) {
    crumbs.push({ label: 'Explorador del almacén' });
  } else if (isOps) {
    crumbs.push({ label: 'Herramientas técnicas' });
    if (path.includes('audio')) crumbs.push({ label: 'Audio no resuelto' });
    else crumbs.push({ label: 'Panel de Ops' });
  } else if (isElt) {
    crumbs.push({ label: 'Ingeniería de datos' });
  }

  return {
    moduleId: 'engineering',
    hubLabel: 'Ingeniería de datos',
    hubPath: '/elt-pipeline',
    backLabel: 'Volver a Ingeniería de datos',
    showBack: !isElt || path !== '/elt-pipeline',
    crumbs,
    tabs: isOps ? tabs : tabs,
    activeTabPath: isExplorer ? '/explorer' : isElt ? '/elt-pipeline' : null,
  };
}

/** Parse query string into a flat string map. */
export function parseQueryParams(url: string): Record<string, string> {
  const q = (url || '').split('?')[1] || '';
  const out: Record<string, string> = {};
  if (!q) return out;
  for (const part of q.split('&')) {
    if (!part) continue;
    const [k, v] = part.split('=');
    if (k) out[decodeURIComponent(k)] = decodeURIComponent(v || '');
  }
  return out;
}

/**
 * Resolve module chrome for the current router URL (path + query).
 * Returns null when the page is outside consolidated hubs.
 */
export function resolveModuleContext(url: string): ModuleContextView | null {
  const path = pathOnly(url);
  const query = parseQueryParams(url);

  return (
    catalogContext(path) ||
    orgContext(path) ||
    reportsContext(path, query) ||
    engineeringContext(path)
  );
}
