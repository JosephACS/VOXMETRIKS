import { describe, expect, it } from 'vitest';
import type { SimpleReportCatalogItem } from './services/simple-reports-api.service';
import {
  filterSimpleReportCatalog,
  foldSearchText,
} from './simple-reports-catalog.filter';

function item(
  partial: Partial<SimpleReportCatalogItem> & Pick<SimpleReportCatalogItem, 'id' | 'title'>,
): SimpleReportCatalogItem {
  return {
    area: partial.area || 'ops',
    description: partial.description || '',
    objective: partial.objective || '',
    access: 'admin',
    org_scoped: true,
    implementation: 'ready',
    pending_reason: '',
    columns: [],
    filters: [],
    business_module: partial.business_module,
    business_module_label: partial.business_module_label,
    business_process: partial.business_process,
    category: partial.category,
    decision: partial.decision,
    ...partial,
  };
}

const ALL: SimpleReportCatalogItem[] = [
  item({
    id: 'b2c-cancellations',
    title: 'Cancelaciones personales',
    description: 'Suscripciones canceladas',
    business_module: 'organization',
    business_module_label: 'Organización',
    category: 'Suscripciones',
    business_process: 'Cancelación',
    decision: 'Revisar bajas',
  }),
  item({
    id: 'b2c-cancel-pending',
    title: 'Cancelaciones pendientes',
    description: 'Cola de cancelación',
    business_module: 'organization',
    business_module_label: 'Organización',
    category: 'Suscripciones',
    business_process: 'Cancelación',
  }),
  item({
    id: 'sessions-active',
    title: 'Sesiones vigentes',
    description: 'Sesiones activas',
    business_module: 'organization',
    business_module_label: 'Organización',
    category: 'Accesos',
  }),
  item({
    id: 'b2c-subscriptions-active',
    title: 'Suscripciones personales activas',
    description: 'Activas',
    business_module: 'organization',
    business_module_label: 'Organización',
    category: 'Suscripciones',
  }),
  item({
    id: 'org-members',
    title: 'Miembros de organización',
    description: 'Miembros',
    business_module: 'organization',
    business_module_label: 'Organización',
    category: 'Equipo',
  }),
  item({
    id: 'org-invites',
    title: 'Invitaciones pendientes',
    description: 'Invites',
    business_module: 'organization',
    business_module_label: 'Organización',
    category: 'Equipo',
  }),
  item({
    id: 'org-audit',
    title: 'Auditoría reciente',
    description: 'Audit',
    business_module: 'organization',
    business_module_label: 'Organización',
    category: 'Gobierno',
  }),
  item({
    id: 'tracks-without-cover',
    title: 'Canciones sin portada',
    description: 'Catálogo incompleto',
    business_module: 'catalog_publishing',
    business_module_label: 'Catálogo y publicación',
    category: 'Calidad',
    business_process: 'Portadas',
  }),
  item({
    id: 'tracks-without-audio',
    title: 'Canciones sin fuente de audio',
    description: 'Audio pendiente',
    business_module: 'catalog_publishing',
    business_module_label: 'Catálogo y publicación',
    category: 'Calidad',
  }),
];

describe('filterSimpleReportCatalog', () => {
  it('CASO 1: Organización 7 → Canc 2 → borrar → Organización 7', () => {
    const org = filterSimpleReportCatalog(ALL, {
      moduleId: 'organization',
      category: '',
      searchText: '',
    });
    expect(org).toHaveLength(7);

    const canc = filterSimpleReportCatalog(ALL, {
      moduleId: 'organization',
      category: '',
      searchText: 'Canc',
    });
    expect(canc).toHaveLength(2);
    expect(canc.every((r) => /cancel/i.test(r.title + r.description + r.business_process))).toBe(true);

    const restored = filterSimpleReportCatalog(ALL, {
      moduleId: 'organization',
      category: '',
      searchText: '',
    });
    expect(restored).toHaveLength(7);
    expect(restored.map((r) => r.id).sort()).toEqual(org.map((r) => r.id).sort());
  });

  it('CASO 2: Organización + canciones vacío; limpiar; canciones visibles', () => {
    const empty = filterSimpleReportCatalog(ALL, {
      moduleId: 'organization',
      category: '',
      searchText: 'canciones',
    });
    expect(empty).toHaveLength(0);

    const cleared = filterSimpleReportCatalog(ALL, {
      moduleId: '',
      category: '',
      searchText: '',
    });
    expect(cleared).toHaveLength(ALL.length);

    const songs = filterSimpleReportCatalog(ALL, {
      moduleId: '',
      category: '',
      searchText: 'canciones',
    });
    expect(songs.length).toBeGreaterThanOrEqual(2);
    expect(songs.some((r) => r.id === 'tracks-without-cover')).toBe(true);
  });

  it('CASO 3: seleccionar tras Canc no muta la fuente maestra', () => {
    const master = [...ALL];
    const before = master.length;
    const visible = filterSimpleReportCatalog(master, {
      moduleId: 'organization',
      category: '',
      searchText: 'Canc',
    });
    expect(visible).toHaveLength(2);
    // Simulate selection using master find — must not shrink master
    const selected = master.find((r) => r.id === visible[0].id);
    expect(selected).toBeTruthy();
    expect(master).toHaveLength(before);
    const afterClear = filterSimpleReportCatalog(master, {
      moduleId: 'organization',
      category: '',
      searchText: '',
    });
    expect(afterClear).toHaveLength(7);
  });

  it('CASO 4: deep-link selection does not destroy catalog filtering', () => {
    const selected = ALL.find((r) => r.id === 'tracks-without-cover')!;
    expect(selected).toBeTruthy();
    const afterClear = filterSimpleReportCatalog(ALL, {
      moduleId: '',
      category: '',
      searchText: '',
    });
    expect(afterClear.map((r) => r.id)).toContain('tracks-without-cover');
    expect(afterClear).toHaveLength(ALL.length);
  });

  it('CASO 5: cambios rápidos no cachean resultados previos', () => {
    let v = filterSimpleReportCatalog(ALL, {
      moduleId: 'organization',
      category: '',
      searchText: 'Canc',
    });
    expect(v).toHaveLength(2);
    v = filterSimpleReportCatalog(ALL, {
      moduleId: 'organization',
      category: '',
      searchText: '',
    });
    expect(v).toHaveLength(7);
    v = filterSimpleReportCatalog(ALL, {
      moduleId: 'catalog_publishing',
      category: '',
      searchText: 'canciones',
    });
    expect(v.every((r) => r.business_module === 'catalog_publishing')).toBe(true);
    expect(v.length).toBeGreaterThanOrEqual(2);
    expect(v.some((r) => /cancel/i.test(r.title))).toBe(false);
  });

  it('CASO 6: mayúsculas y tildes', () => {
    expect(foldSearchText('CANCIÓN')).toBe('cancion');
    const withAccentTitle = [
      ...ALL,
      item({
        id: 'accent-demo',
        title: 'Decisión de canción',
        description: 'áéíóú',
        business_module: 'catalog_publishing',
        business_module_label: 'Catálogo y publicación',
        decision: 'Revisión',
      }),
    ];
    const hits = filterSimpleReportCatalog(withAccentTitle, {
      moduleId: '',
      category: '',
      searchText: 'CANCION',
    });
    expect(hits.some((r) => r.id === 'accent-demo')).toBe(true);
    expect(hits.some((r) => r.id === 'tracks-without-cover')).toBe(true);
  });

  it('never filters destructively over a previous filtered array when used correctly', () => {
    const step1 = filterSimpleReportCatalog(ALL, {
      moduleId: 'organization',
      category: '',
      searchText: 'Canc',
    });
    // Anti-pattern (bug): filtering step1 again with empty search would stay at 2.
    const wrong = step1.filter(() => true);
    expect(wrong).toHaveLength(2);
    // Correct: always from ALL
    const right = filterSimpleReportCatalog(ALL, {
      moduleId: 'organization',
      category: '',
      searchText: '',
    });
    expect(right).toHaveLength(7);
  });
});
