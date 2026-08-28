import { Component, DestroyRef, OnInit, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { interval, switchMap, catchError, of, forkJoin, tap, retry, timer } from 'rxjs';
import { DashboardService } from '../../../core/services/dashboard.service';
import { EnterpriseTracksService } from '../../../core/services/tracks.service';
import { StatsService } from '../services/stats.service';
import { analyticsDateRange, formatChartDate, mergeTrendSeries } from '../../../core/utils/analytics-date-range';
import {
  ArtistGrowth,
  DashboardOverview,
  StreamsAnalytics,
  TopTrack,
} from '../../../core/models/enterprise-api.models';
import { MetricCardComponent } from '../../../shared/components/metric-card/metric-card.component';
import {
  ChartWidgetComponent,
  ChartSeries,
} from '../../../shared/components/chart-widget/chart-widget.component';
import {
  TableWidgetComponent,
  TableColumn,
} from '../../../shared/components/table-widget/table-widget.component';
import { EmptyStateComponent } from '../../../shared/components/empty-state/empty-state.component';

type ArtistRow = ArtistGrowth & Record<string, unknown>;
type TrackRow = TopTrack & Record<string, unknown>;

@Component({
  selector: 'app-enterprise-dashboard',
  standalone: true,
  imports: [
    MetricCardComponent,
    ChartWidgetComponent,
    TableWidgetComponent,
    EmptyStateComponent,
  ],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss',
})
export class DashboardComponent implements OnInit {
  private readonly dashboard = inject(DashboardService);
  private readonly tracks = inject(EnterpriseTracksService);
  private readonly stats = inject(StatsService);
  private readonly destroyRef = inject(DestroyRef);

  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  readonly overview = signal<DashboardOverview | null>(null);
  readonly streams = signal<StreamsAnalytics | null>(null);
  readonly topTrackRows = signal<TrackRow[]>([]);

  readonly totalStreams = computed(() => this.overview()?.total_streams ?? null);
  readonly activeUsers = computed(() => this.overview()?.active_users ?? null);
  readonly topGenre = computed(() => this.overview()?.top_genres?.[0]?.nombre_genero ?? '—');
  readonly growthPct = computed(() => this.computeGrowthPct());

  readonly trendPoints = computed(() =>
    mergeTrendSeries(this.streams(), this.overview()?.growth_trends),
  );

  readonly streamLabels = computed(() => this.trendPoints().map((p) => formatChartDate(p.fecha)));

  readonly streamSeries = computed((): ChartSeries[] => {
    const series = this.trendPoints();
    return [
      { name: 'Streams', data: series.map((p) => p.total_streams), color: '#e8a33d', yAxisIndex: 0 },
      { name: 'Usuarios', data: series.map((p) => p.unique_users), color: '#38bdf8', yAxisIndex: 1 },
    ];
  });

  readonly genrePie = computed((): ChartSeries[] => {
    const genres = this.overview()?.top_genres ?? [];
    return [
      {
        name: 'Géneros',
        data: genres.map((g) => ({ name: g.nombre_genero, value: g.streams_7d || 1 })),
      },
    ];
  });

  readonly deviceLabels = computed(() =>
    (this.overview()?.device_usage ?? []).map((d) => `${d.device_type} · ${d.platform}`),
  );

  readonly deviceSeries = computed((): ChartSeries[] => [
    {
      name: 'Participación %',
      data: (this.overview()?.device_usage ?? []).map((d) => d.share_pct),
      color: '#e8a33d',
    },
  ]);

  readonly artistRows = computed((): ArtistRow[] =>
    (this.overview()?.top_artists ?? []) as ArtistRow[],
  );

  readonly artistColumns: TableColumn<ArtistRow>[] = [
    { key: 'nombre_artista', header: 'Artista', format: 'text' },
    { key: 'streams_7d', header: 'Streams (7d)', align: 'right', format: 'number' },
    { key: 'growth_pct', header: 'Crecimiento', align: 'right', format: 'percent' },
    { key: 'total_followers', header: 'Seguidores', align: 'right', format: 'number' },
  ];

  readonly trackColumns: TableColumn<TrackRow>[] = [
    { key: 'nombre_track', header: 'Track', format: 'text' },
    { key: 'nombre_artista', header: 'Artista', format: 'text' },
    { key: 'popularity', header: 'Popularidad', align: 'right', format: 'number' },
    { key: 'total_streams', header: 'Streams', align: 'right', format: 'number' },
  ];

  ngOnInit(): void {
    this.loadDashboard();
    interval(30_000)
      .pipe(
        switchMap(() => this.fetchDashboard()),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe();
  }

  retry(): void {
    this.loadDashboard();
  }

  private loadDashboard(): void {
    this.fetchDashboard().pipe(takeUntilDestroyed(this.destroyRef)).subscribe();
  }

  private fetchDashboard() {
    this.loading.set(true);
    this.error.set(null);

    return this.dashboard.getOverview().pipe(
      retry({ count: 2, delay: () => timer(600) }),
      catchError((err: Error) => {
        this.error.set(err.message || 'No se pudo conectar con el warehouse analítico.');
        return of(null);
      }),
      switchMap((overview) => {
        const range = analyticsDateRange(overview?.growth_trends, 30);
        return forkJoin({
          overview: of(overview),
          streams: this.dashboard
            .getStreamAnalytics(range.start, range.end)
            .pipe(
              retry({ count: 2, delay: () => timer(600) }),
              catchError(() => of(null)),
            ),
          topTracks: this.tracks.getTopTracks(10).pipe(catchError(() => of([] as TopTrack[]))),
          statsSummary: this.stats.getSummary().pipe(catchError(() => of(null))),
        });
      }),
      tap(({ overview, streams, topTracks, statsSummary }) => {
        let ov = overview;
        if (statsSummary && ov) {
          ov = {
            ...ov,
            total_streams: ov.total_streams || statsSummary.total_streams || statsSummary.total_events || 0,
            active_users: ov.active_users || statsSummary.active_users || 0,
          };
        } else if (statsSummary && !ov) {
          ov = {
            total_streams: statsSummary.total_streams ?? statsSummary.total_events ?? 0,
            active_users: statsSummary.active_users ?? 0,
            top_genres: [],
            top_artists: [],
            device_usage: [],
            growth_trends: [],
          };
        }
        if (!ov) {
          this.error.set(this.error() ?? 'No se pudo cargar el resumen del panel.');
        } else if (!this.trendPoints().length && !ov.top_genres?.length) {
          this.error.set(
            'Conexión parcial: algunos gráficos pueden estar vacíos. Comprueba que el backend y DuckDB estén activos.',
          );
        } else {
          this.error.set(null);
        }
        this.overview.set(ov);
        this.streams.set(streams);
        this.topTrackRows.set(topTracks as TrackRow[]);
        this.loading.set(false);
      }),
    );
  }

  private computeGrowthPct(): number | null {
    const trends = this.overview()?.growth_trends ?? [];
    if (trends.length < 2) {
      const artists = this.overview()?.top_artists ?? [];
      if (!artists.length) return null;
      const avg = artists.reduce((s, a) => s + (a.growth_pct ?? 0), 0) / artists.length;
      return Math.round(avg * 10) / 10;
    }
    const last = trends[trends.length - 1]?.total_streams ?? 0;
    const prev = trends[trends.length - 2]?.total_streams ?? 0;
    if (!prev) return null;
    return Math.round(((last - prev) / prev) * 1000) / 10;
  }
}
