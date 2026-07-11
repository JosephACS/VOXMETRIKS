import { Component, DestroyRef, OnInit, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { retry, timer } from 'rxjs';
import { DashboardService } from '../../core/services/dashboard.service';
import { DashboardOverview, StreamsAnalytics } from '../../core/models/enterprise-api.models';
import { analyticsDateRange, formatChartDate, mergeTrendSeries } from '../../core/utils/analytics-date-range';
import { ChartWidgetComponent, ChartSeries } from '../../shared/components/chart-widget/chart-widget.component';

@Component({
  selector: 'app-analytics-feature',
  standalone: true,
  imports: [ReactiveFormsModule, ChartWidgetComponent],
  template: `
    <div class="feature-page feature-page--wide">
      <header class="feature-page__header">
        <h1>Analítica de streaming</h1>
        <p>Series temporales y horas pico desde el warehouse analítico.</p>
      </header>
      <form class="feature-page__filters" (submit)="$event.preventDefault(); load()">
        <label>
          Desde
          <input type="date" [formControl]="startCtrl" />
        </label>
        <label>
          Hasta
          <input type="date" [formControl]="endCtrl" />
        </label>
        <button type="button" (click)="load()">Aplicar</button>
      </form>
      @if (error()) {
        <p class="feature-page__error" role="alert">{{ error() }}</p>
      }
      <div class="feature-page__charts">
        <app-chart-widget
          class="feature-page__chart-span"
          type="line"
          title="Streams y usuarios"
          [labels]="labels()"
          [series]="series()"
          [dualAxis]="true"
          [height]="320"
        />
        <app-chart-widget
          type="bar"
          title="Horas pico"
          subtitle="Distribución por hora del día"
          [labels]="peakLabels()"
          [series]="peakSeries()"
          [height]="320"
        />
      </div>
    </div>
  `,
  styleUrl: './analytics.component.scss',
})
export class AnalyticsFeatureComponent implements OnInit {
  private readonly dashboard = inject(DashboardService);
  private readonly destroyRef = inject(DestroyRef);

  readonly startCtrl = new FormControl('');
  readonly endCtrl = new FormControl('');
  readonly overview = signal<DashboardOverview | null>(null);
  readonly data = signal<StreamsAnalytics | null>(null);
  readonly error = signal<string | null>(null);

  readonly trendPoints = computed(() =>
    mergeTrendSeries(this.data(), this.overview()?.growth_trends),
  );

  readonly labels = computed(() => this.trendPoints().map((p) => formatChartDate(p.fecha)));
  readonly series = computed((): ChartSeries[] => {
    const s = this.trendPoints();
    return [
      { name: 'Streams', data: s.map((p) => p.total_streams), yAxisIndex: 0 },
      { name: 'Usuarios', data: s.map((p) => p.unique_users), color: '#38bdf8', yAxisIndex: 1 },
    ];
  });
  readonly peakLabels = computed(() =>
    [...(this.data()?.peak_hours ?? [])]
      .sort((a, b) => a.hour_of_day - b.hour_of_day)
      .map((h) => `${h.hour_of_day}:00`),
  );
  readonly peakSeries = computed((): ChartSeries[] => {
    const sorted = [...(this.data()?.peak_hours ?? [])].sort(
      (a, b) => a.hour_of_day - b.hour_of_day,
    );
    return [{ name: 'Streams', data: sorted.map((h) => h.stream_count) }];
  });

  ngOnInit(): void {
    this.dashboard
      .getOverview()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: (overview) => {
          this.overview.set(overview);
          const range = analyticsDateRange(overview.growth_trends, 30);
          this.endCtrl.setValue(range.end);
          this.startCtrl.setValue(range.start);
          this.load();
        },
        error: () => {
          const range = analyticsDateRange(null, 30);
          this.endCtrl.setValue(range.end);
          this.startCtrl.setValue(range.start);
          this.load();
        },
      });
  }

  load(): void {
    const start = this.startCtrl.value;
    const end = this.endCtrl.value;
    if (!start || !end) return;
    this.error.set(null);
    this.dashboard
      .getStreamAnalytics(start, end)
      .pipe(
        retry({ count: 2, delay: () => timer(600) }),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe({
        next: (res) => {
          this.data.set(res);
          if (!this.trendPoints().length) {
            this.error.set('Sin datos en el rango seleccionado. Prueba ajustar las fechas al periodo del warehouse.');
          } else {
            this.error.set(null);
          }
        },
        error: (err: Error) =>
          this.error.set(err.message || 'Error de conexión con el API analítico.'),
      });
  }
}
