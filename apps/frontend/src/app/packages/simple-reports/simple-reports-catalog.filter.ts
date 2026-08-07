import type { SimpleReportCatalogItem } from './services/simple-reports-api.service';

/** Fold accents / case for catalog search (es-ES friendly). */
export function foldSearchText(value: string): string {
  return String(value || '')
    .normalize('NFD')
    .replace(/\p{M}/gu, '')
    .toLowerCase()
    .trim();
}

export function catalogItemSearchBlob(item: SimpleReportCatalogItem): string {
  return foldSearchText(
    [
      item.title,
      item.description,
      item.business_module_label,
      item.business_module,
      item.area,
      item.category,
      item.business_process,
      item.decision,
      item.objective,
      item.id,
    ]
      .filter(Boolean)
      .join(' '),
  );
}

export interface CatalogFilterState {
  moduleId: string;
  category: string;
  searchText: string;
}

/**
 * Always derive the visible catalog from the master list.
 * Never pass a previously filtered array as `allReports`.
 */
export function filterSimpleReportCatalog(
  allReports: readonly SimpleReportCatalogItem[],
  state: CatalogFilterState,
): SimpleReportCatalogItem[] {
  const moduleId = (state.moduleId || '').trim();
  const category = (state.category || '').trim();
  const q = foldSearchText(state.searchText || '');

  return allReports.filter((r) => {
    if (moduleId && r.business_module !== moduleId) return false;
    if (category && r.category !== category) return false;
    if (q && !catalogItemSearchBlob(r).includes(q)) return false;
    return true;
  });
}
