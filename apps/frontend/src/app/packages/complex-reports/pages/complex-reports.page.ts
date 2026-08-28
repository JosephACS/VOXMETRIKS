import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import {
  ComplexCatalogItem,
  ComplexReportData,
  ComplexReportsApiService,
} from '../services/complex-reports-api.service';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import {
  ChartWidgetComponent,
  ChartSeries,
  ChartWidgetType,
} from '../../../shared/components/chart-widget/chart-widget.component';
import { userFacingHttpError } from '../../../core/i18n/user-facing-error';
import { I18nService } from '../../../core/services/i18n.service';
import { TrackCoverService } from '../../../shared/services/track-cover.service';
import {
  classificationLabelEs,
  formatAnalyzedPeriod,
  formatCellDisplay,
  formatSeriesLabel,
  formatUpdatedAtEs,
  humanColumnLabel,
  inclusiveEndIso,
  isTechnicalColumnKey,
} from '../complex-reports-presentation';
import {
  ReportKpi,
  ReportVisualizationId,
  artistDistributionUseful,
  buildLeaderboardRows,
  buildReportInsight,
  buildReportKpis,
  chartPresetForVisualization,
  collapseOtros,
  cumulativeValues,
  genreCompositionUseful,
  genreDonutUseful,
  humanizeStatusLabel,
  LeaderboardRow,
  topNSeries,
  useReleaseStatusComposition,
  useTemporalSnapshot,
  visualizationIdForReport,
  visualizationTestId,
} from '../complex-reports-visualization';

@Component({
  selector: 'app-complex-reports-page',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ...ENTERPRISE_UI_IMPORTS,
    ChartWidgetComponent,
  ],
  styleUrls: ['../../../shared/styles/reports-surface.css'],
  template: `
    <div class="vx-enterprise vx-report-page complex-reports-page">
      @if (!selectedId) {
        <header class="vx-report-page-header">
          <h1>Informes complejos</h1>
          <p>Indicadores tácticos con periodo y visualización. Elige un informe para empezar.</p>
        </header>

        @if (recommended.length) {
          <p class="vx-report-group-label">Recomendados</p>
          <div class="vx-report-rec-row">
            @for (r of recommended; track r.id) {
              <button type="button" class="vx-report-rec-card" (click)="pickRecommended(r.id)">
                <strong>{{ r.title }}</strong>
                <span>{{ r.business_module_label || r.business_module }} · {{ r.area }}</span>
              </button>
            }
          </div>
        }

        <div class="vx-report-selector">
          <label class="vx-report-field">
            <span>Módulo</span>
            <select class="select" [(ngModel)]="selectedModule" (ngModelChange)="onModuleChange()">
              <option value="">Todos los módulos</option>
              @for (m of modules; track m.id) {
                <option [value]="m.id">{{ m.label }}</option>
              }
            </select>
          </label>
          <label class="vx-report-field">
            <span>Informe</span>
            <select class="select" [(ngModel)]="selectedId" (ngModelChange)="onReportChange()">
              <option value="">Seleccione un informe</option>
              @for (r of filtered; track r.id) {
                <option [value]="r.id">{{ r.title }}{{ r.available ? '' : ' (no disponible)' }}</option>
              }
            </select>
          </label>
        </div>
      } @else {
        <app-enterprise-page-header
          [reportMode]="true"
          backPath="/reports"
          backLabel="Reportes"
          [title]="reportTitle"
          [subtitle]="reportLede"
          badge="Complejo"
        />

        <div class="vx-report-toolbar sbd-toolbar" data-testid="enterprise-filter-bar">
          <div class="vx-report-period sbd-period">
            <label class="vx-report-field sbd-field">
              <span>Desde</span>
              <input class="input vx-report-input sbd-input" type="date" [(ngModel)]="dateFrom" data-testid="complex-date-from" />
            </label>
            <label class="vx-report-field sbd-field">
              <span>Hasta</span>
              <input class="input vx-report-input sbd-input" type="date" [(ngModel)]="dateTo" data-testid="complex-date-to" />
            </label>
            <button
              type="button"
              class="btn btn--primary vx-report-run sbd-run"
              (click)="run()"
              [disabled]="loading || !selected?.available"
              data-testid="sbd-run"
            >
              Actualizar
            </button>
            <button
              type="button"
              class="vx-report-more sbd-more"
              (click)="showMoreFilters = !showMoreFilters"
              [attr.aria-expanded]="showMoreFilters"
              data-testid="sbd-more-filters"
            >
              {{ showMoreFilters ? 'Ocultar filtros' : 'Más filtros' }}
            </button>
          </div>
        </div>

        @if (showMoreFilters) {
          <div class="vx-report-advanced sbd-advanced" data-testid="sbd-advanced-filters">
            <div class="vx-report-selector">
              <label class="vx-report-field">
                <span>Módulo</span>
                <select class="select" [(ngModel)]="selectedModule" (ngModelChange)="onModuleChange()">
                  <option value="">Todos los módulos</option>
                  @for (m of modules; track m.id) {
                    <option [value]="m.id">{{ m.label }}</option>
                  }
                </select>
              </label>
              <label class="vx-report-field">
                <span>Área</span>
                <select class="select" [(ngModel)]="selectedArea" (ngModelChange)="onAreaChange()">
                  <option value="">Todas las áreas</option>
                  @for (a of areas; track a) {
                    <option [value]="a">{{ a }}</option>
                  }
                </select>
              </label>
              <label class="vx-report-field">
                <span>Informe</span>
                <select class="select" [(ngModel)]="selectedId" (ngModelChange)="onReportChange()">
                  <option value="">Seleccione un informe</option>
                  @for (r of filtered; track r.id) {
                    <option [value]="r.id">{{ r.title }}{{ r.available ? '' : ' (no disponible)' }}</option>
                  }
                </select>
              </label>
            </div>
            <div class="vx-report-advanced__actions sbd-advanced__actions">
              <button type="button" class="btn btn--secondary" (click)="clearDates()">Limpiar fechas</button>
            </div>
          </div>
        }

        @if (false) {
          <p class="vx-report-period-hint sbd-period-hint" data-testid="complex-period-hint">{{ periodHint }}</p>
        }

        @if (isCampaignRoi) {
          <section class="vx-report-unavailable" [attr.data-testid]="vizTestId" aria-label="No disponible">
            <h2>Retorno de inversión por campaña</h2>
            <p class="vx-report-unavailable__status">No disponible actualmente</p>
            <p>
              Los datos disponibles no permiten calcular este indicador de forma consistente.
            </p>
            <details class="vx-report-method sbd-method">
              <summary>Datos necesarios</summary>
              <div class="vx-report-method__body">
                <p>{{ selected?.calculation || 'Se requieren ingresos atribuibles y coste de campaña por periodo, con trazabilidad homogénea.' }}</p>
                <p class="vx-report-method__id"><strong>ID:</strong> campaign-roi</p>
              </div>
            </details>
          </section>
        } @else if (!selected?.available) {
          <app-enterprise-empty-state [title]="selected?.unavailable_reason || 'Informe no disponible todavía.'" />
        } @else if (loading) {
          <app-enterprise-loading-skeleton [rows]="5" />
        } @else if (error) {
          <app-enterprise-error-state [message]="error" (retry)="run()" />
        } @else if (data) {
          @if (!data.available) {
            <app-enterprise-empty-state [title]="data.unavailable_reason || 'Informe no disponible todavía.'" />
          } @else if (!data.series.length && !data.rows.length) {
            <app-enterprise-empty-state title="Sin datos para los filtros actuales." />
          } @else {
            <section class="vx-report-kpis sbd-kpis" [class.vx-report-kpis--2x2]="kpis.length === 4" aria-label="Indicadores">
              @for (k of kpis; track k.key) {
                <div class="sbd-kpi">
                  <p class="vx-report-kpi__value sbd-kpi__value" [class.is-accent]="k.accent">{{ formatKpi(k) }}</p>
                  <p class="vx-report-kpi__label sbd-kpi__label">{{ k.label }}</p>
                </div>
              }
            </section>

            <p class="vx-report-meta sbd-meta" data-testid="complex-updated-line">
              <span data-testid="complex-period-line">{{ periodLine }}</span>
              <span aria-hidden="true">·</span>
              <span>Actualizado {{ updatedLine }}</span>
            </p>

            @if (showSnapshot) {
              <section class="vx-report-snapshot" [attr.data-testid]="vizTestId" aria-label="Instantánea del periodo">
                @for (card of snapshotCards; track card.key) {
                  <div class="vx-report-snapshot__card" [class.is-accent]="card.accent">
                    <p class="vx-report-snapshot__value">{{ card.value }}</p>
                    <p class="vx-report-snapshot__label">{{ card.label }}</p>
                    @if (card.hint) {
                      <p class="vx-report-snapshot__hint">{{ card.hint }}</p>
                    }
                    @if (card.progress != null) {
                      <div class="vx-report-snapshot__bar" aria-hidden="true">
                        <i [style.width.%]="card.progress"></i>
                      </div>
                    }
                  </div>
                }
              </section>
            } @else if (showLeaderboard) {
              <section class="vx-report-leaderboard" [attr.data-testid]="vizTestId" aria-label="Leaderboard Top 10">
                @for (row of leaderboard; track row.rank) {
                  <div
                    class="vx-lb-row"
                    [class.vx-lb-row--1]="row.rank === 1"
                    [class.vx-lb-row--top]="row.rank === 2 || row.rank === 3"
                    [class.vx-lb-row--rest]="row.rank >= 4"
                  >
                    <span class="vx-lb-rank">{{ row.rank }}</span>
                    <div class="vx-lb-cover" [attr.data-initials]="coverInitials(row)" [style.background]="coverGradient(row)">
                      @if (coverFor(row); as img) {
                        <img [src]="img" [alt]="''" (error)="onCoverError(row.trackId)" />
                      } @else {
                        <span class="vx-lb-cover__mark">VX</span>
                      }
                    </div>
                    <div class="vx-lb-meta">
                      <span class="vx-lb-song">{{ row.title }}</span>
                      <span class="vx-lb-artist">{{ row.artist }}</span>
                    </div>
                    <div class="vx-lb-bar" aria-hidden="true">
                      <i [style.width.%]="row.barPct"></i>
                    </div>
                    <span class="vx-lb-plays">{{ fmtCompact(row.plays) }}</span>
                  </div>
                }
              </section>
            } @else if (chartSeries.length && chartWidgetType) {
              <section class="vx-report-chart sbd-chart" [attr.data-testid]="vizTestId" aria-label="Gráfico">
                <app-chart-widget
                  [type]="chartWidgetType"
                  [labels]="chartLabels"
                  [series]="chartSeries"
                  [height]="chartHeight"
                  [title]="null"
                  [flat]="true"
                  [dualAxis]="useDualAxis"
                  [highlightPeak]="highlightPeak"
                  [percentAxis]="usePercentAxis"
                />
              </section>
            }

            @if (insight) {
              <aside class="vx-report-insight" data-testid="report-insight">
                <span class="vx-report-insight__bar" aria-hidden="true"></span>
                <p>{{ insight }}</p>
              </aside>
            }

            @if (data.rows.length && visibleColumns.length && !hideDetailTable) {
              <section class="vx-report-detail sbd-detail" aria-label="Detalle">
                <h2 class="vx-report-section-title sbd-section-title">
                  Detalle
                  <span class="vx-report-section__meta">{{ tableVisibleRows.length }} / {{ data.rows.length }}</span>
                </h2>
                <div class="vx-report-table sbd-table">
                  <table>
                    <thead>
                      <tr>
                        @for (c of visibleColumns; track c.key) {
                          <th>{{ columnLabel(c) }}</th>
                        }
                      </tr>
                    </thead>
                    <tbody>
                      @for (row of tableVisibleRows; track $index) {
                        <tr>
                          @for (c of visibleColumns; track c.key) {
                            <td>{{ displayCell(row[c.key], c.key) }}</td>
                          }
                        </tr>
                      }
                    </tbody>
                  </table>
                </div>
                @if (tableVisibleRows.length < data.rows.length) {
                  <div class="vx-report-actions">
                    <button
                      type="button"
                      class="btn btn--secondary"
                      data-testid="complex-table-more"
                      (click)="showMoreTableRows()"
                    >
                      Ver más
                    </button>
                  </div>
                }
              </section>
            }

            <details class="vx-report-method sbd-method" data-testid="sbd-methodology">
              <summary>Cómo se calcula</summary>
              <div class="vx-report-method__body sbd-method__body">
                <p><strong>Qué muestra:</strong> {{ plainWhat }}</p>
                <p><strong>Para qué sirve:</strong> {{ plainWhy }}</p>
                <p><strong>Cómo se calcula:</strong> {{ plainHow }}</p>
                @if (selected?.data_classification || data.data_classification) {
                  <p>
                    <strong>Origen de los datos:</strong>
                    {{ classificationLabel(selected?.data_classification || data.data_classification) }}
                  </p>
                }
                @if (data.includes_synthetic_events || data.data_classification === 'synthetic' || data.data_classification === 'mixed') {
                  <p class="vx-report-muted" role="status">
                    {{ data.classification_note || 'Este resultado incluye eventos sintéticos utilizados para pruebas analíticas.' }}
                  </p>
                }
                @if (data.monetary_classification === 'simulated' || selected?.monetary_classification === 'simulated') {
                  <p class="vx-report-muted" role="status">Valores monetarios simulados. No son cobros reales.</p>
                }
                <p class="vx-report-method__id"><strong>ID:</strong> {{ selected?.id || data.report_id }}</p>
              </div>
            </details>
          }
        }
      }
    </div>
  `,
})
export class ComplexReportsPage implements OnInit {
  private readonly api = inject(ComplexReportsApiService);
  private readonly i18n = inject(I18nService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly covers = inject(TrackCoverService);

  catalog: ComplexCatalogItem[] = [];
  areas: string[] = [];
  modules: { id: string; label: string }[] = [];
  selectedArea = '';
  selectedModule = '';
  selectedId = '';
  selected: ComplexCatalogItem | null = null;
  dateFrom = '';
  dateTo = '';
  loading = false;
  error = '';
  data: ComplexReportData | null = null;
  showMoreFilters = false;
  tableShowCount = 12;
  private readonly coverMap = signal<Record<number, string | null>>({});

  private get tablePageSize(): number {
    if (typeof window !== 'undefined' && window.matchMedia('(max-width: 520px)').matches) {
      return 8;
    }
    return 12;
  }

  get tableVisibleRows(): Record<string, unknown>[] {
    const rows = this.data?.rows || [];
    return rows.slice(0, this.tableShowCount);
  }

  showMoreTableRows(): void {
    this.tableShowCount += this.tablePageSize;
  }

  private resetTablePaging(): void {
    this.tableShowCount = this.tablePageSize;
  }

  get isCampaignRoi(): boolean {
    return (this.selectedId || this.data?.report_id) === 'campaign-roi';
  }

  get reportTitle(): string {
    return this.selected?.title || 'Informe';
  }

  get reportLede(): string {
    if (this.selectedId === 'top-tracks-period') {
      return 'Las canciones con mayor número de reproducciones durante el periodo seleccionado.';
    }
    if (this.selectedId === 'streams-by-day') {
      return 'Serie temporal de reproducciones del catálogo en el periodo seleccionado.';
    }
    return (
      this.selected?.description ||
      this.selected?.decision ||
      'Consulta el periodo y actualiza para ver el resultado.'
    );
  }

  get filtered(): ComplexCatalogItem[] {
    let items = this.catalog;
    if (this.selectedModule) {
      items = items.filter((r) => r.business_module === this.selectedModule);
    }
    if (this.selectedArea) {
      items = items.filter((r) => r.area === this.selectedArea);
    }
    return items;
  }

  get recommended(): ComplexCatalogItem[] {
    const prefer = ['streams-by-day', 'top-tracks-period', 'releases-status-month'];
    const hits = prefer
      .map((id) => this.catalog.find((c) => c.id === id))
      .filter((x): x is ComplexCatalogItem => !!x);
    if (hits.length) return hits;
    return this.catalog.slice(0, 3);
  }

  get plainWhat(): string {
    return this.selected?.description || this.selected?.question || '—';
  }

  get plainWhy(): string {
    return this.selected?.decision || this.selected?.question || '—';
  }

  get plainHow(): string {
    return this.selected?.calculation || '—';
  }

  get periodHint(): string {
    if (!this.data?.period_start) return '';
    return formatAnalyzedPeriod(this.data.period_start, this.data.period_end_exclusive);
  }

  get periodLine(): string {
    return this.periodHint;
  }

  get updatedLine(): string {
    return formatUpdatedAtEs(this.data?.updated_at);
  }

  get visibleColumns(): { key: string; label: string }[] {
    const cols = this.data?.columns || [];
    return cols.filter((c) => !isTechnicalColumnKey(c.key) && c.key !== 'track_id');
  }

  get activeViz(): ReportVisualizationId {
    const id = this.selectedId || this.data?.report_id || '';
    let viz = visualizationIdForReport(id);
    if (viz === 'artist-treemap') {
      const values = (this.data?.series || []).map((s) => Number(s.value) || 0);
      if (!artistDistributionUseful(values)) viz = 'artist-ranking';
    }
    return viz;
  }

  get vizTestId(): string {
    const id = this.selectedId || this.data?.report_id || '';
    if (id === 'top-genres-period') return 'visualization-genre-composition';
    if (this.showSnapshot) {
      if (id === 'income-by-month') return 'visualization-monthly-combo';
      if (id === 'opportunity-win-rate-month') return 'visualization-percent-trend';
      if (id === 'subscription-growth-month') return 'visualization-subscription-columns';
      if (id === 'releases-status-month') return 'visualization-stacked-status';
    }
    return visualizationTestId(this.activeViz);
  }

  get showSnapshot(): boolean {
    const id = this.selectedId || this.data?.report_id || '';
    return useTemporalSnapshot(id, this.data?.series || []);
  }

  get showReleaseComposition(): boolean {
    const id = this.selectedId || this.data?.report_id || '';
    return useReleaseStatusComposition(id, this.data?.series || []);
  }

  get snapshotCards(): { key: string; value: string; label: string; hint?: string; progress?: number; accent?: boolean }[] {
    const id = this.selectedId || this.data?.report_id || '';
    const series = this.data?.series || [];
    const rows = this.data?.rows || [];
    const summary = this.data?.summary || {};
    if (id === 'opportunity-win-rate-month') {
      const row = rows[0] || {};
      const rec = row as Record<string, unknown>;
      const sum = summary as Record<string, unknown>;
      const pct = Number(rec['porcentaje'] ?? sum['average'] ?? series[0]?.value ?? 0) || 0;
      const won = Number(rec['ganadas'] ?? 0) || 0;
      const closed = Number(rec['cerradas'] ?? 0) || 0;
      return [
        {
          key: 'rate',
          value: `${pct.toLocaleString('es-ES', { maximumFractionDigits: 1 })} %`,
          label: 'Tasa del periodo',
          accent: true,
          progress: Math.max(0, Math.min(100, pct)),
        },
        { key: 'won', value: String(won), label: 'Ganadas' },
        { key: 'closed', value: String(closed), label: 'Cerradas' },
      ];
    }
    if (id === 'income-by-month') {
      const v = Number((summary as Record<string, unknown>)['total'] ?? series[0]?.value ?? 0) || 0;
      return [
        {
          key: 'income',
          value: this.fmtCompact(v),
          label: 'Ingresos del mes',
          hint: this.displaySeriesLabel(String(series[0]?.label || '')),
          accent: true,
        },
      ];
    }
    if (id === 'subscription-growth-month') {
      const v = Number((summary as Record<string, unknown>)['total'] ?? series[0]?.value ?? 0) || 0;
      return [
        {
          key: 'subs',
          value: String(Math.round(v)),
          label: 'Nuevas suscripciones',
          hint: this.displaySeriesLabel(String(series[0]?.label || '')),
          accent: true,
        },
      ];
    }
    if (id === 'releases-status-month') {
      const total = rows.reduce((a, r) => a + (Number((r as Record<string, unknown>)['cantidad']) || 0), 0) || 1;
      return rows.slice(0, 6).map((r, i) => {
        const rec = r as Record<string, unknown>;
        const n = Number(rec['cantidad']) || 0;
        return {
          key: `st-${i}`,
          value: String(n),
          label: humanizeStatusLabel(String(rec['estado'] || '')),
          progress: Math.round((n / total) * 100),
        };
      });
    }
    return [];
  }

  get showLeaderboard(): boolean {
    return this.activeViz === 'leaderboard' && this.leaderboard.length > 0;
  }

  readonly hideDetailTable = false;

  get leaderboard(): LeaderboardRow[] {
    if ((this.selectedId || this.data?.report_id) !== 'top-tracks-period') return [];
    return buildLeaderboardRows(this.data?.rows || [], this.data?.series || [], 10);
  }

  get kpis(): ReportKpi[] {
    if (!this.data) return [];
    return buildReportKpis(this.selectedId || this.data.report_id, this.data.summary || {}, this.data.series || []);
  }

  get insight(): string | null {
    if (!this.data) return null;
    return buildReportInsight(
      this.selectedId || this.data.report_id,
      this.data.series || [],
      this.data.summary || {},
    );
  }

  get chartWidgetType(): ChartWidgetType | null {
    if (this.showSnapshot) return null;
    const id = this.selectedId || this.data?.report_id || '';
    if (this.showReleaseComposition) return 'stacked-bar';
    if (id === 'top-genres-period') {
      const values = (this.data?.series || []).map((s) => Number(s.value) || 0);
      // Prefer composition / lollipop; donut only when few varied slices.
      if (genreDonutUseful(values) && !genreCompositionUseful(values)) return 'pie';
      return 'hbar';
    }
    const preset = chartPresetForVisualization(this.activeViz);
    return preset;
  }

  get highlightPeak(): boolean {
    return this.activeViz === 'temporal-line';
  }

  get usePercentAxis(): boolean {
    return this.activeViz === 'percent-trend';
  }

  get useDualAxis(): boolean {
    return this.activeViz === 'monthly-combo';
  }

  get chartHeight(): number {
    if (typeof window !== 'undefined' && window.matchMedia('(max-width: 520px)').matches) {
      if (this.activeViz === 'genre-composition' || this.selectedId === 'top-genres-period') return 320;
      return this.activeViz === 'temporal-line' ? 260 : 280;
    }
    return 400;
  }

  private get chartSourceSeries(): { label: string; value: number }[] {
    const series = this.data?.series || [];
    const id = this.selectedId || this.data?.report_id || '';
    const mapped = series.map((p) => ({
      label: String(p.label ?? ''),
      value: Number(p.value) || 0,
    }));
    if (id === 'top-tracks-period' || id === 'top-artists-period') {
      return mapped.slice(0, 10);
    }
    if (id === 'top-genres-period') {
      return mapped; // collapseOtros limits slices in chartSeries
    }
    return mapped;
  }

  get chartLabels(): string[] {
    const series = this.chartSourceSeries;
    const id = this.selectedId || this.data?.report_id || '';
    if (id === 'top-genres-period' && this.chartWidgetType === 'pie') {
      return [];
    }
    if (id === 'top-genres-period') {
      const values = series.map((s) => s.value);
      const composition = collapseOtros(series, 7);
      const otros = composition.find((p) => p.name === 'Otros');
      const compositionTotal = composition.reduce((a, p) => a + p.value, 0) || 1;
      const otrosShare = otros ? otros.value / compositionTotal : 0;
      const useTopN = series.length > 8 && (otrosShare > 0.4 || !artistDistributionUseful(values));
      return (useTopN ? topNSeries(series, 8) : composition).map((p) => p.name);
    }
    if (this.activeViz === 'artist-treemap') {
      return [];
    }
    if (this.selectedId === 'releases-status-month') {
      if (this.showReleaseComposition) {
        return ['Distribución'];
      }
      const months: string[] = [];
      for (const p of series) {
        const raw = String(p.label || '');
        const month = raw.split('·').map((s) => s.trim())[0] || raw;
        if (!months.includes(month)) months.push(month);
      }
      return months.map((m) => this.displaySeriesLabel(m));
    }
    return series.map((p) => this.displaySeriesLabel(p.label));
  }

  get chartSeries(): ChartSeries[] {
    const series = this.chartSourceSeries;
    const viz = this.activeViz;
    const id = this.selectedId || this.data?.report_id || '';

    if (id === 'top-genres-period' && this.chartWidgetType === 'pie') {
      return [{ name: 'Géneros', data: collapseOtros(series, 7) }];
    }
    if (id === 'top-genres-period') {
      const values = series.map((s) => s.value);
      const composition = collapseOtros(series, 7);
      const otros = composition.find((p) => p.name === 'Otros');
      const compositionTotal = composition.reduce((a, p) => a + p.value, 0) || 1;
      const otrosShare = otros ? otros.value / compositionTotal : 0;
      // Flat long-tail or Otros >40% → Top 8 ranking (plays), not composition % with giant Otros.
      const useTopN = series.length > 8 && (otrosShare > 0.4 || !artistDistributionUseful(values));
      const collapsed = useTopN ? topNSeries(series, 8) : composition;
      return [
        {
          name: useTopN ? 'Reproducciones' : 'Participación',
          data: useTopN
            ? collapsed.map((p) => p.value)
            : collapsed.map((p) => Math.round((p.value / compositionTotal) * 1000) / 10),
          color: '#e8a33d',
        },
      ];
    }
    if (viz === 'artist-treemap') {
      return [
        {
          name: 'Artistas',
          data: series.map((s) => ({ name: s.label, value: s.value })),
        },
      ];
    }
    if (viz === 'monthly-combo') {
      const values = series.map((p) => p.value);
      return [
        { name: 'Ingreso mensual', data: values, color: '#e8a33d', type: 'bar', yAxisIndex: 0 },
        {
          name: 'Acumulado',
          data: cumulativeValues(values),
          color: '#38bdf8',
          type: 'line',
          yAxisIndex: 1,
        },
      ];
    }
    if (this.selectedId === 'releases-status-month') {
      const months: string[] = [];
      const statuses = new Set<string>();
      const map = new Map<string, number>();
      const byStatus = new Map<string, number>();
      for (const p of series) {
        const raw = String(p.label || '');
        const parts = raw.split('·').map((s) => s.trim());
        const month = parts[0] || raw;
        const status = parts[1] || 'total';
        if (!months.includes(month)) months.push(month);
        statuses.add(status);
        const n = Number(p.value) || 0;
        map.set(`${month}||${status}`, n);
        byStatus.set(status, (byStatus.get(status) || 0) + n);
      }
      if (this.showReleaseComposition) {
        const total = [...byStatus.values()].reduce((a, v) => a + v, 0) || 1;
        return [...byStatus.entries()].map(([status, n], i) => ({
          name: humanizeStatusLabel(status),
          data: [Math.round((n / total) * 1000) / 10],
          color: ['#e8a33d', '#149E74', '#2A9D8F', '#5EAAA8', '#7A8B87', '#A8B5B0', '#3D5A56', '#88C9B0'][
            i % 8
          ],
        }));
      }
      return [...statuses].map((status, i) => ({
        name: humanizeStatusLabel(status),
        data: months.map((m) => map.get(`${m}||${status}`) ?? 0),
        color: ['#e8a33d', '#149E74', '#2A9D8F', '#5EAAA8', '#7A8B87', '#A8B5B0', '#3D5A56', '#88C9B0'][
          i % 8
        ],
      }));
    }
    if (viz === 'percent-trend') {
      return [
        {
          name: 'Win rate',
          data: series.map((p) => {
            const v = Number(p.value) || 0;
            return v <= 1 ? v * 100 : v;
          }),
          color: '#e8a33d',
        },
      ];
    }
    return [
      {
        name:
          this.selectedId === 'streams-by-day'
            ? 'Reproducciones'
            : this.selectedId === 'subscription-growth-month'
              ? 'Nuevas suscripciones'
              : 'Valor',
        data: series.map((p) => Number(p.value) || 0),
        color: '#e8a33d',
      },
    ];
  }

  pickRecommended(id: string): void {
    this.selectedId = id;
    this.onReportChange();
  }

  ngOnInit(): void {
    const qp = this.route.snapshot.queryParamMap;
    this.selectedModule = qp.get('module') || '';
    this.api.catalog().subscribe({
      next: (res) => {
        this.catalog = res.items;
        this.areas = [...new Set(res.items.map((i) => i.area))];
        this.modules = res.modules?.length
          ? res.modules
          : [...new Map(res.items.map((i) => [i.business_module || '', i.business_module_label || ''])).entries()]
              .filter(([id]) => id)
              .map(([id, label]) => ({ id, label }));
        const q = qp.get('report');
        if (q) {
          this.selectedId = q;
          this.onReportChange();
        }
      },
      error: (err) => {
        this.error = userFacingHttpError(this.i18n, err);
      },
    });
  }

  onModuleChange(): void {
    if (this.selected && this.selectedModule && this.selected.business_module !== this.selectedModule) {
      this.selectedId = '';
      this.selected = null;
      this.data = null;
    }
  }

  onAreaChange(): void {
    if (this.selected && this.selected.area !== this.selectedArea && this.selectedArea) {
      this.selectedId = '';
      this.selected = null;
      this.data = null;
    }
  }

  onReportChange(): void {
    this.selected = this.catalog.find((r) => r.id === this.selectedId) || null;
    this.data = null;
    this.error = '';
    this.showMoreFilters = false;
    this.resetTablePaging();
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: {
        report: this.selectedId || null,
        module: this.selectedModule || this.selected?.business_module || null,
      },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });
    if (this.selected?.available) this.run();
  }

  clearDates(): void {
    this.dateFrom = '';
    this.dateTo = '';
    this.run();
  }

  run(): void {
    if (!this.selectedId || !this.selected?.available) return;
    if (this.dateFrom && this.dateTo && this.dateFrom > this.dateTo) {
      this.error = 'La fecha inicial no puede ser posterior a la fecha final.';
      return;
    }
    this.loading = true;
    this.error = '';
    this.api
      .data(this.selectedId, {
        from: this.dateFrom || undefined,
        to: this.dateTo || undefined,
        limit: this.selectedId?.startsWith('top-') ? 50 : 40,
      })
      .subscribe({
        next: (res) => {
          this.data = res;
          this.syncDateInputsFromResult(res);
          this.resetTablePaging();
          this.prefetchCovers();
          this.loading = false;
        },
        error: (err) => {
          this.error = userFacingHttpError(this.i18n, err);
          this.loading = false;
        },
      });
  }

  private prefetchCovers(): void {
    for (const row of this.leaderboard) {
      if (!row.trackId) continue;
      this.covers.cover$(row.trackId).subscribe((url) => {
        this.coverMap.update((m) => ({ ...m, [row.trackId!]: url }));
      });
    }
  }

  coverFor(row: LeaderboardRow): string | null {
    if (!row.trackId) return null;
    return this.coverMap()[row.trackId] ?? null;
  }

  onCoverError(trackId: number | null): void {
    if (!trackId) return;
    this.coverMap.update((m) => ({ ...m, [trackId]: null }));
  }

  coverInitials(row: LeaderboardRow): string {
    const t = (row.title || '?').trim();
    const a = (row.artist || '').trim();
    const c0 = t.charAt(0).toUpperCase();
    const c1 = (a.charAt(0) || t.charAt(1) || '').toUpperCase();
    return `${c0}${c1}`;
  }

  coverGradient(row: LeaderboardRow): string {
    const hues = [160, 210, 270, 40, 190, 200, 300, 195, 220, 140];
    const h = hues[(row.rank - 1) % hues.length];
    return `linear-gradient(145deg, hsl(${h} 28% 22%), hsl(${h} 20% 10%))`;
  }

  formatKpi(k: ReportKpi): string {
    if (k.value == null || Number.isNaN(Number(k.value))) return '—';
    if (k.format === 'percent') {
      const v = Number(k.value);
      const pct = v <= 1 && v >= 0 ? v * 100 : v;
      return `${pct.toLocaleString('es-ES', { maximumFractionDigits: 0 })} %`;
    }
    return this.fmtCompact(k.value);
  }

  fmtCompact(v: number | null | undefined): string {
    if (v == null || Number.isNaN(Number(v))) return '—';
    const n = Number(v);
    const abs = Math.abs(n);
    if (abs >= 1_000_000) {
      const s = (n / 1_000_000).toFixed(1).replace(/\.0$/, '').replace('.', ',');
      return `${s}M`;
    }
    if (abs >= 1_000) {
      const s = (n / 1_000).toFixed(1).replace(/\.0$/, '').replace('.', ',');
      return `${s}K`;
    }
    return n.toLocaleString('es-ES', { maximumFractionDigits: 0 });
  }

  classificationLabel(code?: string | null): string {
    return classificationLabelEs(code);
  }

  columnLabel(c: { key: string; label: string }): string {
    return humanColumnLabel(c.key, c.label);
  }

  displayCell(value: unknown, key: string): string {
    if (key === 'estado' || key === 'status') {
      return humanizeStatusLabel(value == null ? null : String(value));
    }
    return formatCellDisplay(value, key);
  }

  displaySeriesLabel(label: string): string {
    return formatSeriesLabel(label);
  }

  private syncDateInputsFromResult(res: ComplexReportData): void {
    if (!res.period_start || !res.period_end_exclusive) return;
    this.dateFrom = res.period_start.slice(0, 10);
    this.dateTo = inclusiveEndIso(res.period_end_exclusive);
  }
}
