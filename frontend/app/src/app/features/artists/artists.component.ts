/**
 * ArtistsComponent
 * ================
 * Vista completa de artistas con:
 * - Búsqueda con debounce + debounce reactivo vía RxJS
 * - Filtro por popularidad mínima (client-side)
 * - Ordenamiento client-side por columna
 * - Paginación server-side + display paginado client-side
 * - KPI row de top artistas
 * - Estados: cargando (skeleton), vacío, error, datos
 *
 * Endpoints: GET /api/v1/artists · /top
 */

import {
  Component,
  inject,
  signal,
  computed,
  OnInit,
  OnDestroy,
} from '@angular/core';
import { FormsModule }   from '@angular/forms';
import { DecimalPipe }   from '@angular/common';
import {
  Subject,
  debounceTime,
  distinctUntilChanged,
  switchMap,
  startWith,
  takeUntil,
} from 'rxjs';

import { ArtistsService }            from '../../services/artists.service';
import { KpiCardComponent }          from '../../shared/components/kpi-card/kpi-card.component';
import { LoadingSpinnerComponent }   from '../../shared/components/loading-spinner/loading-spinner.component';
import { TableSearchComponent }      from '../../shared/components/table-search/table-search.component';
import { TablePaginationComponent }  from '../../shared/components/table-pagination/table-pagination.component';
import { TableFilterComponent }      from '../../shared/components/table-filter/table-filter.component';
import { SortHeaderComponent }       from '../../shared/components/sort-header/sort-header.component';
import { EmptyStateComponent }       from '../../shared/components/empty-state/empty-state.component';
import { MetricBarComponent }        from '../../shared/components/metric-bar/metric-bar.component';
import { SpotifyLinkComponent }      from '../../shared/components/spotify-link/spotify-link.component';
import { TableSkeletonComponent }    from '../../shared/components/table-skeleton/table-skeleton.component';
import {
  Artista,
  PaginatedResponse,
  TopArtista,
} from '../../shared/models/api.models';
import {
  SortState,
  ActiveFilter,
  FilterConfig,
} from '../../shared/models/table.models';

@Component({
  selector: 'app-artists',
  standalone: true,
  imports: [
    FormsModule,
    DecimalPipe,
    KpiCardComponent,
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
  templateUrl: './artists.component.html',
  styleUrl: './artists.component.css',
})
export class ArtistsComponent implements OnInit, OnDestroy {
  private readonly service  = inject(ArtistsService);
  private readonly destroy$ = new Subject<void>();

  // ── State signals ────────────────────────────────────────────────────────
  protected readonly isLoading   = signal(true);
  protected readonly hasError    = signal(false);
  protected readonly page        = signal(1);
  protected readonly limit       = 50;
  protected readonly searchVal   = signal('');
  protected readonly sort        = signal<SortState>({ column: '', direction: null });
  protected readonly activeFilters = signal<ActiveFilter[]>([]);

  protected readonly response   = signal<PaginatedResponse<Artista> | null>(null);
  protected readonly topArtists = signal<TopArtista[]>([]);

  private readonly search$ = new Subject<string>();

  // ── Filter configuration ─────────────────────────────────────────────────
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
      key: 'has_image',
      label: 'Con imagen',
      type: 'toggle',
    },
    {
      key: 'has_spotify',
      label: 'Con link Spotify',
      type: 'toggle',
    },
  ];

  // ── Raw artists from API ─────────────────────────────────────────────────
  protected readonly rawArtists  = computed(() => this.response()?.items ?? []);
  protected readonly serverTotal = computed(() => this.response()?.total ?? 0);
  protected readonly totalPages  = computed(() =>
    Math.ceil(this.serverTotal() / this.limit)
  );

  // ── Client-side filter + sort ────────────────────────────────────────────
  protected readonly filteredArtists = computed(() => {
    let data = [...this.rawArtists()];
    const filters = this.activeFilters();

    for (const f of filters) {
      if (f.key === 'min_popularity') {
        data = data.filter(a => (a.popularidad ?? 0) >= Number(f.value));
      }
      if (f.key === 'has_image' && f.value === true) {
        data = data.filter(a => !!a.url_imagen);
      }
      if (f.key === 'has_spotify' && f.value === true) {
        data = data.filter(a => !!a.url_spotify);
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

  protected readonly artists = computed(() => this.filteredArtists());

  // Total for pagination: use server total when no client filters active
  protected readonly displayTotal = computed(() =>
    this.activeFilters().length > 0
      ? this.filteredArtists().length
      : this.serverTotal()
  );

  protected readonly maxPop = computed(() =>
    Math.max(...this.topArtists().map(a => a.promedio_popularidad ?? 0), 1)
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
        return this.service.listArtists(this.page(), this.limit, term || undefined);
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

    this.service.getTopArtists(5).pipe(takeUntil(this.destroy$)).subscribe({
      next: data => this.topArtists.set(data),
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
  protected barWidth(value?: number | null, max = 100): string {
    if (!value || max === 0) return '2%';
    return `${Math.max(2, Math.round((value / max) * 100))}%`;
  }

  protected genreList(generos?: string[] | null): string {
    if (!generos?.length) return '—';
    return generos.slice(0, 2).join(', ') + (generos.length > 2 ? ` +${generos.length - 2}` : '');
  }

  protected followersDisplay(n?: number | null): string {
    if (n == null) return '—';
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
    if (n >= 1_000)     return `${(n / 1_000).toFixed(0)}K`;
    return String(n);
  }
}
