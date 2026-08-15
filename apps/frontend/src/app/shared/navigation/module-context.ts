/**
 * Spec 043 hotfix + Spec 054 — resolve module context chrome from the current URL.
 * Pure helpers (no DI) for breadcrumb / back / secondary tabs.
 * Tabs are filtered by the product-surface registry when access context is provided.
 */

import {
  listVisibleContextTabs,
  resolveSurfacePath,
  type ProductSurfaceContext,
} from '../../core/product-surface';

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
  moduleId: 'catalog' | 'organization' | 'reports' | 'engineering' | 'platformOps';
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

function registryTabs(
  contextGroup: string,
  access: ProductSurfaceContext | undefined,
  organizationId?: number,
): ModuleTab[] | null {
  if (!access) return null;
  return listVisibleContextTabs(contextGroup, access).map((surface) => ({
    label: surface.tabLabel || surface.labelKey,
    path: resolveSurfacePath(surface, organizationId ?? access.organizationId),
    exact: surface.exact,
    matchPrefixes: surface.matchPrefixes?.map((p) =>
      organizationId != null ? p.replace(/:id/g, String(organizationId)) : p,
    ),
  }));
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
    return tab.matchPrefixes.some(
      (p) => path === p || path.startsWith(p + '/') || (p === tab.path && path.startsWith(p)),
    );
  }
  return path === tab.path || path.startsWith(tab.path + '/');
}

function activeCatalogTab(path: string, tabs: ModuleTab[]): ModuleTab | null {
  const ordered = [...tabs].sort((a, b) => {
    const la = (a.matchPrefixes?.[0] || a.path).length;
    const lb = (b.matchPrefixes?.[0] || b.path).length;
    return lb - la;
  });
  if (path === '/artist/releases/new' || path.startsWith('/artist/releases/new/')) {
    return tabs.find((t) => t.path === '/artist/releases/new') || null;
  }
  if (path.startsWith('/artist/releases/') && path !== '/artist/releases') {
    return tabs.find((t) => t.path === '/artist/releases') || null;
  }
  for (const tab of ordered) {
    if (tab.path === '/artist/releases/new') continue;
    if (matchesTab(path, tab)) return tab;
  }
  return null;
}

function catalogContext(
  path: string,
  access?: ProductSurfaceContext,
): ModuleContextView | null {
  const isCatalogSurface =
    path === '/catalog' ||
    path.startsWith('/artist-profiles') ||
    path.startsWith('/artist/profile') ||
    path.startsWith('/artist/tracks') ||
    path.startsWith('/artist/releases') ||
    path.startsWith('/catalog-review') ||
    path.startsWith('/catalog-rights');

  if (!isCatalogSurface) return null;

  const tabs = registryTabs('catalog', access) ?? CATALOG_TABS;
  const tab = activeCatalogTab(path, tabs);
  const isHub = path === '/catalog';
  const crumbs: BreadcrumbCrumb[] = [{ label: 'Catálogo y publicación', path: '/catalog' }];

  if (!isHub && tab) {
    crumbs.push({
      label: tab.label,
      path: tab.path === path ? undefined : tab.path,
    });
  }

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
    crumbs[crumbs.length - 1] = {
      label: 'Lanzamientos (derechos)',
      path: '/catalog-rights/releases',
    };
  } else if (path.startsWith('/artist-profiles/') && path !== '/artist-profiles') {
    crumbs.push({ label: 'Perfil' });
  }

  return {
    moduleId: 'catalog',
    hubLabel: 'Catálogo y publicación',
    hubPath: '/catalog',
    backLabel: 'Catálogo y publicación',
    showBack: false,
    crumbs,
    tabs,
    activeTabPath: tab?.path ?? (isHub ? '/catalog' : null),
  };
}

function orgContext(
  path: string,
  access?: ProductSurfaceContext,
): ModuleContextView | null {
  const m = path.match(/^\/organizations\/(\d+)(\/.*)?$/);
  if (!m) return null;
  const id = Number(m[1]);
  const rest = m[2] || '';
  const hubPath = `/organizations/${id}`;

  const defaultTabs: ModuleTab[] = [
    { label: 'Resumen', path: hubPath, exact: true },
    { label: 'Perfil', path: `${hubPath}/settings`, matchPrefixes: [`${hubPath}/settings`] },
    { label: 'Miembros', path: `${hubPath}/members`, matchPrefixes: [`${hubPath}/members`] },
    {
      label: 'Invitaciones',
      path: `${hubPath}/invitations`,
      matchPrefixes: [`${hubPath}/invitations`],
    },
    { label: 'Roles y permisos', path: `${hubPath}/roles`, matchPrefixes: [`${hubPath}/roles`] },
    { label: 'Auditoría', path: `${hubPath}/audit`, matchPrefixes: [`${hubPath}/audit`] },
    {
      label: 'Plan y facturación',
      path: '/subscriptions/overview',
      matchPrefixes: ['/subscriptions', '/billing'],
    },
  ];

  const tabs =
    registryTabs('organization', access ? { ...access, organizationId: id } : undefined, id) ??
    defaultTabs;

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
    sectionLabel = 'Roles y permisos';
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
    backLabel: 'Organización',
    showBack: false,
    crumbs,
    tabs,
    activeTabPath,
  };
}

function reportsContext(
  path: string,
  query: Record<string, string>,
  access?: ProductSurfaceContext,
): ModuleContextView | null {
  const isReports =
    path === '/reports' ||
    path.startsWith('/simple-reports') ||
    path.startsWith('/complex-reports');
  if (!isReports) return null;

  const isSimple = path.startsWith('/simple-reports') || query['type'] === 'simple';
  const isComplex = path.startsWith('/complex-reports') || query['type'] === 'complex';
  const isHub = path === '/reports' && !query['type'];

  const viewingReport = !!(query['report'] || '').trim();
  const filtered = registryTabs('reports', access);
  const tabs: ModuleTab[] = viewingReport
    ? []
    : filtered ?? [
        { label: 'Informes simples', path: '/simple-reports' },
        { label: 'Informes complejos', path: '/complex-reports' },
      ];

  const crumbs: BreadcrumbCrumb[] = [{ label: 'Reportes', path: '/reports' }];
  let activeTabPath: string | null = null;

  if (isSimple || (path === '/reports' && query['type'] === 'simple')) {
    crumbs.push({ label: 'Informes simples', path: '/simple-reports' });
    activeTabPath = viewingReport ? null : '/simple-reports';
  } else if (isComplex || (path === '/reports' && query['type'] === 'complex')) {
    crumbs.push({ label: 'Informes complejos', path: '/complex-reports' });
    activeTabPath = viewingReport ? null : '/complex-reports';
  }

  const fromWp = query['from'] === 'workpanel' || query['context'] === 'workpanel';
  const secondaryBack = fromWp
    ? { label: 'Workpanel', path: '/workpanel' }
    : undefined;

  if (viewingReport) {
    return {
      moduleId: 'reports',
      hubLabel: 'Reportes',
      hubPath: '/reports',
      backLabel: 'Reportes',
      showBack: false,
      crumbs: [],
      tabs: [],
      activeTabPath: null,
      secondaryBack,
    };
  }

  return {
    moduleId: 'reports',
    hubLabel: 'Reportes',
    hubPath: '/reports',
    backLabel: 'Reportes',
    showBack: false,
    crumbs,
    tabs,
    activeTabPath: activeTabPath ?? (isHub ? null : '/simple-reports'),
    secondaryBack,
  };
}

function platformOpsContext(
  path: string,
  access?: ProductSurfaceContext,
): ModuleContextView | null {
  if (!path.startsWith('/platform-ops')) return null;

  const defaultTabs: ModuleTab[] = [
    {
      label: 'Panel de Ops',
      path: '/platform-ops',
      matchPrefixes: ['/platform-ops'],
      exact: true,
    },
    {
      label: 'Audio no resuelto',
      path: '/platform-ops/audio-unresolved',
      matchPrefixes: ['/platform-ops/audio-unresolved'],
    },
    {
      label: 'Solicitudes de artista',
      path: '/platform-ops/artist-requests',
      matchPrefixes: ['/platform-ops/artist-requests'],
    },
  ];
  const tabs = registryTabs('platformOps', access) ?? defaultTabs;

  const isAudio = path.includes('audio');
  const isArtistReq = path.includes('artist-requests');
  const crumbs: BreadcrumbCrumb[] = [
    { label: 'Administración de plataforma', path: '/platform-ops' },
  ];
  if (isAudio) crumbs.push({ label: 'Audio no resuelto' });
  else if (isArtistReq) crumbs.push({ label: 'Solicitudes de artista' });
  else crumbs.push({ label: 'Panel de Ops' });

  return {
    moduleId: 'platformOps',
    hubLabel: 'Administración de plataforma',
    hubPath: '/platform-ops',
    backLabel: 'Administración de plataforma',
    showBack: false,
    crumbs,
    tabs,
    activeTabPath: isAudio
      ? '/platform-ops/audio-unresolved'
      : isArtistReq
        ? '/platform-ops/artist-requests'
        : '/platform-ops',
  };
}

function engineeringContext(
  path: string,
  access?: ProductSurfaceContext,
): ModuleContextView | null {
  const isEng = path.startsWith('/elt-pipeline') || path.startsWith('/explorer');
  if (!isEng) return null;

  const defaultTabs: ModuleTab[] = [
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
  const tabs = registryTabs('engineering', access) ?? defaultTabs;

  const isElt = path.startsWith('/elt-pipeline');
  const isExplorer = path.startsWith('/explorer');

  const crumbs: BreadcrumbCrumb[] = [{ label: 'Datos', path: '/elt-pipeline' }];
  if (isExplorer) {
    crumbs.push({ label: 'Explorador del almacén' });
  } else if (isElt) {
    crumbs.push({ label: 'Ingeniería de datos' });
  }

  return {
    moduleId: 'engineering',
    hubLabel: 'Ingeniería de datos',
    hubPath: '/elt-pipeline',
    backLabel: 'Ingeniería de datos',
    showBack: false,
    crumbs,
    tabs,
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
 * When `access` is provided, tabs are filtered by the Spec 054 registry.
 */
export function resolveModuleContext(
  url: string,
  access?: ProductSurfaceContext,
): ModuleContextView | null {
  const path = pathOnly(url);
  const query = parseQueryParams(url);

  return (
    catalogContext(path, access) ||
    orgContext(path, access) ||
    reportsContext(path, query, access) ||
    platformOpsContext(path, access) ||
    engineeringContext(path, access)
  );
}
