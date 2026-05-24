/**
 * GenresComponent
 * ===============
 * Vista de estadísticas por género con:
 * - Búsqueda client-side en tiempo real
 * - Filtros: popularidad mínima, energía mínima
 * - Ordenamiento client-side por columna
 * - KPI row de resumen
 * - Barras de métricas visuales
 * - Estados: skeleton, vacío, error
 *
 * Endpoint: GET /api/v1/genres/stats → agg_genero_popularidad
 */

import {
  Component,
  inject,
  signal,
  computed,
  OnInit,
} from '@angular/core';
import { DecimalPipe } from '@angular/common';

import { GenresService }             from '../../services/genres.service';
import { KpiCardComponent }          from '../../shared/components/kpi-card/kpi-card.component';
import { LoadingSpinnerComponent }   from '../../shared/components/loading-spinner/loading-spinner.component';
import { TableSearchComponent }      from '../../shared/components/table-search/table-search.component';
import { TableFilterComponent }      from '../../shared/components/table-filter/table-filter.component';
import { SortHeaderComponent }       from '../../shared/components/sort-header/sort-header.component';
import { EmptyStateComponent }       from '../../shared/components/empty-state/empty-state.component';
import { MetricBarComponent }        from '../../shared/components/metric-bar/metric-bar.component';
import { TableSkeletonComponent }    from '../../shared/components/table-skeleton/table-skeleton.component';
import { GeneroPopularidad }         from '../../shared/models/api.models';
import {
  SortState,
  ActiveFilter,
  FilterConfig,
} from '../../shared/models/table.models';

@Component({
  selector: 'app-genres',
  standalone: true,
  imports: [
    DecimalPipe,
    KpiCardComponent,
    LoadingSpinnerComponent,
    TableSearchComponent,
    TableFilterComponent,
    SortHeaderComponent,
    EmptyStateComponent,
    MetricBarComponent,
    TableSkeletonComponent,
  ],
  templateUrl: './genres.component.html',
  styleUrl: './genres.component.css',
})
export class GenresComponent implements OnInit {
  private readonly service = inject(GenresService);

  // ── State ────────────────────────────────────────────────────────────────
  protected readonly isLoading   = signal(true);
  protected readonly hasError    = signal(false);
  protected readonly allGenres   = signal<GeneroPopularidad[]>([]);
  protected readonly searchVal   = signal('');
  protected readonly sort        = signal<SortState>({ column: 'total_tracks', direction: 'desc' });
  protected readonly activeFilters = signal<ActiveFilter[]>([]);

  // ── Filter configs ───────────────────────────────────────────────────────
  protected readonly filterConfigs: FilterConfig[] = [
    {
      key: 'min_popularity',
      label: 'Popularidad mínima',
      type: 'range',
      min: 0,
      max: 100,
      step: 5,
      suffix: '',
    },
    {
      key: 'min_energy',
      label: 'Energía mínima',
      type: 'range',
      min: 0,
      max: 100,
      step: 5,
      suffix: '%',
    },
    {
      key: 'min_tracks',
      label: 'Tracks mínimos',
      type: 'range',
      min: 0,
      max: 500,
      step: 25,
      suffix: '',
    },
  ];

  // ── Computed: filtered + sorted ──────────────────────────────────────────
  protected readonly filteredGenres = computed(() => {
    let data = this.allGenres().filter(g => {
      if (!this.searchVal()) return true;
      const q = this.searchVal().toLowerCase();
      return (g.nombre_genero ?? '').toLowerCase().includes(q);
    });

    const filters = this.activeFilters();
    for (const f of filters) {
      if (f.key === 'min_popularity') {
        data = data.filter(g => (g.popularidad_promedio ?? 0) >= Number(f.value));
      }
      if (f.key === 'min_energy') {
        data = data.filter(g => (g.energia_promedio ?? 0) * 100 >= Number(f.value));
      }
      if (f.key === 'min_tracks') {
        data = data.filter(g => (g.total_tracks ?? 0) >= Number(f.value));
      }
    }

    const s = this.sort();
    if (s.column && s.direction) {
      data = [...data].sort((a, b) => {
        const va = (a as any)[s.column] ?? 0;
        const vb = (b as any)[s.column] ?? 0;
        const cmp = typeof va === 'number'
          ? va - vb
          : String(va).localeCompare(String(vb));
        return s.direction === 'asc' ? cmp : -cmp;
      });
    }

    return data;
  });

  protected readonly maxTracks = computed(() =>
    Math.max(...this.allGenres().map(g => g.total_tracks ?? 0), 1)
  );

  protected readonly topGenre = computed(() => {
    const g = this.allGenres();
    return g.reduce(
      (best, cur) => (cur.total_tracks ?? 0) > (best?.total_tracks ?? 0) ? cur : best,
      g[0] ?? null
    );
  });

  protected readonly avgPopularity = computed(() => {
    const g = this.allGenres().filter(x => x.popularidad_promedio != null);
    if (!g.length) return null;
    return g.reduce((sum, x) => sum + (x.popularidad_promedio ?? 0), 0) / g.length;
  });

  protected readonly avgEnergy = computed(() => {
    const g = this.allGenres().filter(x => x.energia_promedio != null);
    if (!g.length) return null;
    return g.reduce((sum, x) => sum + (x.energia_promedio ?? 0), 0) / g.length;
  });

  // ── Lifecycle ────────────────────────────────────────────────────────────
  ngOnInit(): void {
    this.service.getGenreStats(200).subscribe({
      next: data => {
        this.allGenres.set(data);
        this.isLoading.set(false);
      },
      error: () => {
        this.hasError.set(true);
        this.isLoading.set(false);
      },
    });
  }

  // ── Event handlers ───────────────────────────────────────────────────────
  protected onSearch(term: string): void {
    this.searchVal.set(term);
  }

  protected onSort(s: SortState): void {
    this.sort.set(s);
  }

  protected onFilter(filters: ActiveFilter[]): void {
    this.activeFilters.set(filters);
  }

  protected onClearFilters(): void {
    this.activeFilters.set([]);
  }

  protected onRetry(): void {
    this.hasError.set(false);
    this.isLoading.set(true);
    this.service.getGenreStats(200).subscribe({
      next: data => { this.allGenres.set(data); this.isLoading.set(false); },
      error: () => { this.hasError.set(true); this.isLoading.set(false); },
    });
  }

  // ── Helpers ──────────────────────────────────────────────────────────────
  protected barWidth(value?: number | null): string {
    const max = this.maxTracks();
    if (!value || max === 0) return '2%';
    return `${Math.max(2, Math.round((value / max) * 100))}%`;
  }

  protected popularityColor(pop?: number | null): string {
    const p = pop ?? 0;
    if (p >= 70) return 'var(--color-primary)';
    if (p >= 50) return 'var(--color-info)';
    if (p >= 30) return 'var(--color-warning)';
    return 'var(--color-text-muted)';
  }
}
