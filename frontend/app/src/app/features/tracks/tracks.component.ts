/**
 * TracksComponent
 * ===============
 * Vista completa de tracks con:
 * - Búsqueda server-side con debounce
 * - Filtros client-side: explicit, duración mínima
 * - Ordenamiento client-side por columna
 * - Paginación server-side
 * - Muestra audio features (energy, danceability, valence) cuando están disponibles
 * - Estados: skeleton, vacío, error, datos
 *
 * Endpoints: GET /api/v1/tracks
 */

import {
  Component,
  inject,
  signal,
  computed,
  OnInit,
  OnDestroy,
} from '@angular/core';
import { FormsModule }  from '@angular/forms';
import { DecimalPipe }  from '@angular/common';
import {
  Subject,
  debounceTime,
  distinctUntilChanged,
  switchMap,
  startWith,
  takeUntil,
} from 'rxjs';

import { TracksService }             from '../../services/tracks.service';
import { LoadingSpinnerComponent }   from '../../shared/components/loading-spinner/loading-spinner.component';
import { DurationPipe }              from '../../shared/pipes/duration.pipe';
import { TableSearchComponent }      from '../../shared/components/table-search/table-search.component';
import { TablePaginationComponent }  from '../../shared/components/table-pagination/table-pagination.component';
import { TableFilterComponent }      from '../../shared/components/table-filter/table-filter.component';
import { SortHeaderComponent }       from '../../shared/components/sort-header/sort-header.component';
import { EmptyStateComponent }       from '../../shared/components/empty-state/empty-state.component';
import { MetricBarComponent }        from '../../shared/components/metric-bar/metric-bar.component';
import { SpotifyLinkComponent }      from '../../shared/components/spotify-link/spotify-link.component';
import { TableSkeletonComponent }    from '../../shared/components/table-skeleton/table-skeleton.component';
import {
  Track,
  PaginatedResponse,
} from '../../shared/models/api.models';
import {
  SortState,
  ActiveFilter,
  FilterConfig,
} from '../../shared/models/table.models';

@Component({
  selector: 'app-tracks',
  standalone: true,
  imports: [
    FormsModule,
    DecimalPipe,
    DurationPipe,
    LoadingSpinnerComponent,
    TableSearchComponent,
    TablePaginationComponent,
    TableFilterComponent,
    SortHeaderComponent,
    EmptyStateComponent,
    MetricBarComponent,
    SpotifyLinkComponent,
    TableSkeletonComponent,
  ],
  templateUrl: './tracks.component.html',
  styleUrl: './tracks.component.css',
})
export class TracksComponent implements OnInit, OnDestroy {
  private readonly service  = inject(TracksService);
  private readonly destroy$ = new Subject<void>();

  // ── State signals ────────────────────────────────────────────────────────
  protected readonly isLoading   = signal(true);
  protected readonly hasError    = signal(false);
  protected readonly page        = signal(1);
  protected readonly limit       = 50;
  protected readonly searchVal   = signal('');
  protected readonly sort        = signal<SortState>({ column: 'nombre_track', direction: 'asc' });
  protected readonly activeFilters = signal<ActiveFilter[]>([]);

  protected readonly response = signal<PaginatedResponse<Track> | null>(null);

  private readonly search$ = new Subject<string>();

  // ── Filter configs ───────────────────────────────────────────────────────
  protected readonly filterConfigs: FilterConfig[] = [
    {
      key: 'explicit',
      label: 'Solo explicit',
      type: 'toggle',
    },
    {
      key: 'has_features',
      label: 'Con audio features',
      type: 'toggle',
    },
    {
      key: 'min_duration',
      label: 'Duración mínima (min)',
      type: 'range',
      min: 0,
      max: 10,
      step: 1,
      suffix: ' min',
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
  ];

  // ── Computed ─────────────────────────────────────────────────────────────
  protected readonly rawTracks   = computed(() => this.response()?.items ?? []);
  protected readonly serverTotal = computed(() => this.response()?.total ?? 0);
  protected readonly totalPages  = computed(() =>
    Math.ceil(this.serverTotal() / this.limit)
  );

  protected readonly filteredTracks = computed(() => {
    let data = [...this.rawTracks()];
    const filters = this.activeFilters();

    for (const f of filters) {
      if (f.key === 'explicit' && f.value === true) {
        data = data.filter(t => t.explicit === true);
      }
      if (f.key === 'has_features' && f.value === true) {
        data = data.filter(t => t.energy != null || t.danceability != null);
      }
      if (f.key === 'min_duration') {
        const minMs = Number(f.value) * 60_000;
        data = data.filter(t => (t.duration_ms ?? 0) >= minMs);
      }
      if (f.key === 'min_energy') {
        const minE = Number(f.value) / 100;
        data = data.filter(t => (t.energy ?? 0) >= minE);
      }
    }

    // Sort
    const s = this.sort();
    if (s.column && s.direction) {
      data.sort((a, b) => {
        const va = (a as any)[s.column] ?? '';
        const vb = (b as any)[s.column] ?? '';
        const cmp = typeof va === 'number'
          ? va - vb
          : String(va).localeCompare(String(vb));
        return s.direction === 'asc' ? cmp : -cmp;
      });
    }

    return data;
  });

  protected readonly tracks = computed(() => this.filteredTracks());

  protected readonly displayTotal = computed(() =>
    this.activeFilters().length > 0
      ? this.filteredTracks().length
      : this.serverTotal()
  );

  // ── Lifecycle ────────────────────────────────────────────────────────────
  ngOnInit(): void {
    this.search$.pipe(
      startWith(''),
      debounceTime(350),
      distinctUntilChanged(),
      switchMap(term => {
        this.isLoading.set(true);
        this.hasError.set(false);
        return this.service.listTracks(this.page(), this.limit, term || undefined);
      }),
      takeUntil(this.destroy$),
    ).subscribe({
      next: res => {
        this.response.set(res);
        this.isLoading.set(false);
      },
      error: () => {
        this.hasError.set(true);
        this.isLoading.set(false);
      },
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  // ── Event handlers ───────────────────────────────────────────────────────
  protected onSearch(term: string): void {
    this.searchVal.set(term);
    this.page.set(1);
    this.search$.next(term);
  }

  protected goTo(p: number): void {
    if (p < 1 || p > this.totalPages()) return;
    this.page.set(p);
    this.search$.next(this.searchVal());
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
    this.search$.next(this.searchVal());
  }

  // ── Helpers ──────────────────────────────────────────────────────────────
  protected energyPct(energy?: number | null): number {
    return Math.round((energy ?? 0) * 100);
  }

  protected dancePct(dance?: number | null): number {
    return Math.round((dance ?? 0) * 100);
  }

  protected valencePct(valence?: number | null): number {
    return Math.round((valence ?? 0) * 100);
  }

  protected hasAnyFeature(track: Track): boolean {
    return track.energy != null || track.danceability != null || track.valence != null;
  }
}
