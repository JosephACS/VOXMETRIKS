import { resolveModuleContext } from './module-context';

describe('resolveModuleContext (043 hotfix)', () => {
  it('resolves catalog artists with back + active tab', () => {
    const ctx = resolveModuleContext('/artist-profiles');
    expect(ctx?.moduleId).toBe('catalog');
    expect(ctx?.showBack).toBe(true);
    expect(ctx?.backLabel).toContain('Catálogo');
    expect(ctx?.hubPath).toBe('/catalog');
    expect(ctx?.activeTabPath).toBe('/artist-profiles');
    expect(ctx?.crumbs[0].path).toBe('/catalog');
    expect(ctx?.crumbs.some((c) => c.label === 'Artistas')).toBe(true);
  });

  it('marks Publicar música for new release wizard', () => {
    const ctx = resolveModuleContext('/artist/releases/new');
    expect(ctx?.activeTabPath).toBe('/artist/releases/new');
    expect(ctx?.crumbs.some((c) => c.label === 'Publicar música')).toBe(true);
  });

  it('adds Detalle crumb for release detail', () => {
    const ctx = resolveModuleContext('/artist/releases/42');
    expect(ctx?.activeTabPath).toBe('/artist/releases');
    expect(ctx?.crumbs.some((c) => c.label === 'Detalle')).toBe(true);
  });

  it('resolves rights conflicts under catalog', () => {
    const ctx = resolveModuleContext('/catalog-rights/conflicts');
    expect(ctx?.moduleId).toBe('catalog');
    expect(ctx?.activeTabPath).toBe('/catalog-rights/conflicts');
    expect(ctx?.showBack).toBe(true);
  });

  it('hides back on catalog hub', () => {
    const ctx = resolveModuleContext('/catalog');
    expect(ctx?.showBack).toBe(false);
    expect(ctx?.activeTabPath).toBe('/catalog');
  });

  it('resolves organization members with hub back', () => {
    const ctx = resolveModuleContext('/organizations/7/members');
    expect(ctx?.moduleId).toBe('organization');
    expect(ctx?.hubPath).toBe('/organizations/7');
    expect(ctx?.showBack).toBe(true);
    expect(ctx?.activeTabPath).toBe('/organizations/7/members');
  });

  it('resolves simple reports with report crumb and workpanel secondary', () => {
    const ctx = resolveModuleContext(
      '/simple-reports?report=tracks-without-cover&from=workpanel',
    );
    expect(ctx?.moduleId).toBe('reports');
    expect(ctx?.activeTabPath).toBe('/simple-reports');
    expect(ctx?.secondaryBack?.path).toBe('/workpanel');
    expect(ctx?.crumbs.some((c) => c.label === 'tracks-without-cover')).toBe(true);
  });

  it('resolves complex reports tab', () => {
    const ctx = resolveModuleContext('/complex-reports?report=streams-by-day');
    expect(ctx?.activeTabPath).toBe('/complex-reports');
    expect(ctx?.showBack).toBe(true);
  });

  it('resolves engineering explorer with back to ELT', () => {
    const ctx = resolveModuleContext('/explorer');
    expect(ctx?.moduleId).toBe('engineering');
    expect(ctx?.showBack).toBe(true);
    expect(ctx?.hubPath).toBe('/elt-pipeline');
    expect(ctx?.activeTabPath).toBe('/explorer');
  });

  it('returns null outside hubs', () => {
    expect(resolveModuleContext('/discover')).toBeNull();
    expect(resolveModuleContext('/liked')).toBeNull();
  });

  it('resolves platform-ops hub chrome with tabs', () => {
    const hub = resolveModuleContext('/platform-ops');
    expect(hub?.moduleId).toBe('platformOps');
    expect(hub?.hubPath).toBe('/platform-ops');
    expect(hub?.showBack).toBe(false);
    expect(hub?.activeTabPath).toBe('/platform-ops');
    expect(hub?.tabs.some((t) => t.path === '/platform-ops/artist-requests')).toBe(true);

    const requests = resolveModuleContext('/platform-ops/artist-requests');
    expect(requests?.moduleId).toBe('platformOps');
    expect(requests?.showBack).toBe(true);
    expect(requests?.activeTabPath).toBe('/platform-ops/artist-requests');
    expect(requests?.crumbs.some((c) => c.label === 'Solicitudes de artista')).toBe(true);
  });
});
