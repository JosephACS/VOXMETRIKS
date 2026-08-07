import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import {
  ComplexCatalogItem,
  ComplexReportData,
  ComplexReportsApiService,
} from '../services/complex-reports-api.service';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import { ChartWidgetComponent, ChartSeries, ChartWidgetType } from '../../../shared/components/chart-widget/chart-widget.component';
import { userFacingHttpError } from '../../../core/i18n/user-facing-error';
import { I18nService } from '../../../core/services/i18n.service';
import {
  classificationLabelEs,
  countStatLabel,
  formatAnalyzedPeriod,
  formatCellDisplay,
  formatSeriesLabel,
  formatUpdatedAtEs,
  humanColumnLabel,
  inclusiveEndIso,
  isTechnicalColumnKey,
} from '../complex-reports-presentation';

@Component({
  selector: 'app-complex-reports-page',
  standalone: true,
  imports: [CommonModule, FormsModule, ...ENTERPRISE_UI_IMPORTS, ChartWidgetComponent],
  template: `
    <div class="vx-enterprise complex-reports-page">
      <app-enterprise-page-header
        title="Reportes"
        subtitle="Indicadores tácticos por módulo. Datos preparados en el servidor; fórmulas sin cambios."
      />

      @if (!selectedId && recommended.length) {
        <app-enterprise-section-card title="Recomendados para empezar">
          <div class="rec-row">
            @for (r of recommended; track r.id) {
              <button type="button" class="rec-card" (click)="pickRecommended(r.id)">
                <strong>{{ r.title }}</strong>
                <span>{{ r.business_module_label || r.business_module }} · {{ r.area }}</span>
              </button>
            }
          </div>
        </app-enterprise-section-card>
      }

      <app-enterprise-section-card title="Selector">
        <div class="form-grid">
          <app-enterprise-form-field label="Módulo">
            <select class="select" [(ngModel)]="selectedModule" (ngModelChange)="onModuleChange()">
              <option value="">Todos los módulos</option>
              @for (m of modules; track m.id) {
                <option [value]="m.id">{{ m.label }}</option>
              }
            </select>
          </app-enterprise-form-field>
          <app-enterprise-form-field label="Área">
            <select class="select" [(ngModel)]="selectedArea" (ngModelChange)="onAreaChange()">
              <option value="">Todas las áreas</option>
              @for (a of areas; track a) {
                <option [value]="a">{{ a }}</option>
              }
            </select>
          </app-enterprise-form-field>
          <app-enterprise-form-field label="Informe">
            <select class="select" [(ngModel)]="selectedId" (ngModelChange)="onReportChange()">
              <option value="">Seleccione un informe</option>
              @for (r of filtered; track r.id) {
                <option [value]="r.id">{{ r.title }}{{ r.available ? '' : ' (no disponible)' }}</option>
              }
            </select>
          </app-enterprise-form-field>
        </div>

        @if (selected) {
          <div class="plain-summary">
            <p><strong>Qué muestra:</strong> {{ plainWhat }}</p>
            <p><strong>Para qué sirve:</strong> {{ plainWhy }}</p>
            <p><strong>Cómo se calcula:</strong> {{ plainHow }}</p>
          </div>
          <details class="tech-details">
            <summary>Ver detalles del informe</summary>
            <div class="meta">
              <p><strong>Módulo:</strong> {{ selected.business_module_label || selected.area }}</p>
              <p><strong>Categoría:</strong> {{ selected.category || '—' }}</p>
              <p><strong>Pregunta:</strong> {{ selected.question }}</p>
              <p><strong>Decisión:</strong> {{ selected.decision || selected.question }}</p>
              <p><strong>Explicación:</strong> {{ selected.description }}</p>
              <p><strong>Cálculo:</strong> {{ selected.calculation }}</p>
              @if (selected.data_classification) {
                <p><strong>Clasificación:</strong> {{ classificationLabel(selected.data_classification) }}</p>
              }
              @if (selected.monetary_classification === 'simulated') {
                <p class="muted" role="status">Valores monetarios simulados. No son cobros reales.</p>
              }
              @if (!selected.available) {
                <p class="muted"><strong>No disponible:</strong> {{ selected.unavailable_reason }}</p>
              }
            </div>
          </details>
        }
      </app-enterprise-section-card>

      @if (selected?.available) {
        <app-enterprise-section-card title="Periodo">
          <div class="form-grid">
            <app-enterprise-form-field label="Fecha inicial">
              <input class="input" type="date" [(ngModel)]="dateFrom" data-testid="complex-date-from" />
            </app-enterprise-form-field>
            <app-enterprise-form-field label="Fecha final">
              <input class="input" type="date" [(ngModel)]="dateTo" data-testid="complex-date-to" />
            </app-enterprise-form-field>
          </div>
          @if (periodHint) {
            <p class="period-hint" data-testid="complex-period-hint">{{ periodHint }}</p>
          }
          <div class="actions">
            <button type="button" class="btn btn--primary" (click)="run()" [disabled]="loading">
              Ejecutar consulta
            </button>
            <button type="button" class="btn btn--secondary" (click)="clearDates()">Limpiar fechas</button>
          </div>
        </app-enterprise-section-card>
      }

      @if (selected) {
        @if (loading) {
          <app-enterprise-loading-skeleton [rows]="6" />
        } @else if (error) {
          <app-enterprise-error-state [message]="error" (retry)="run()" />
        } @else if (data) {
          @if (!data.available) {
            <app-enterprise-empty-state [title]="data.unavailable_reason || 'Informe no disponible todavía.'" />
          } @else if (!data.series.length && !data.rows.length) {
            <app-enterprise-empty-state title="No existen datos para el periodo seleccionado." />
          } @else {
            <app-enterprise-section-card title="Resumen">
              <div class="kpi-grid">
                <app-enterprise-stat-card label="Total" [value]="fmt(data.summary['total'])" />
                <app-enterprise-stat-card label="Promedio" [value]="fmt(data.summary['average'])" />
                <app-enterprise-stat-card label="Máximo" [value]="fmt(data.summary['max'])" />
                <app-enterprise-stat-card [label]="pointsLabel" [value]="fmt(data.summary['count'])" />
              </div>
              <p class="muted" data-testid="complex-period-line">{{ periodLine }}</p>
              <p class="muted" data-testid="complex-updated-line">Última actualización: {{ updatedLine }}</p>
              @if (data.includes_synthetic_events || data.data_classification === 'synthetic' || data.data_classification === 'mixed') {
                <p class="muted" role="status">
                  {{ data.classification_note || 'Este resultado incluye eventos sintéticos utilizados para pruebas analíticas.' }}
                </p>
              }
              @if (data.data_classification) {
                <p class="muted">{{ classificationLabel(data.data_classification) }}</p>
              }
              @if (data.monetary_classification === 'simulated') {
                <p class="muted" role="status">
                  Valores monetarios simulados / de prueba académica. No representan cobros reales.
                </p>
              }
            </app-enterprise-section-card>

            @if (data.series.length) {
              <app-enterprise-section-card title="Visualización">
                <app-chart-widget
                  [type]="chartWidgetType"
                  [labels]="chartLabels"
                  [series]="chartSeries"
                  [height]="320"
                  [title]="null"
                />
              </app-enterprise-section-card>
            }

            @if (data.rows.length && visibleColumns.length) {
              <app-enterprise-section-card [title]="'Detalle (' + data.rows.length + ')'">
                <div class="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        @for (c of visibleColumns; track c.key) {
                          <th>{{ columnLabel(c) }}</th>
                        }
                      </tr>
                    </thead>
                    <tbody>
                      @for (row of data.rows; track $index) {
                        <tr>
                          @for (c of visibleColumns; track c.key) {
                            <td>{{ displayCell(row[c.key], c.key) }}</td>
                          }
                        </tr>
                      }
                    </tbody>
                  </table>
                </div>
              </app-enterprise-section-card>
            }
          }
        }
      }
    </div>
  `,
  styles: [
    `
      .form-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 1rem;
      }
      .plain-summary {
        margin-top: 0.85rem;
        padding: 0.75rem 0.85rem;
        border: 1px solid var(--border-color, rgba(255, 255, 255, 0.08));
        border-radius: 0.45rem;
      }
      .plain-summary p {
        margin: 0.35rem 0;
        font-size: 0.95rem;
        line-height: 1.4;
      }
      .tech-details {
        margin-top: 0.65rem;
      }
      .tech-details summary {
        cursor: pointer;
        font-weight: 600;
        font-size: 0.9rem;
      }
      .meta p,
      .muted {
        margin: 0.35rem 0;
        font-size: 0.92rem;
      }
      .period-hint {
        margin: 0.65rem 0 0;
        font-size: 0.9rem;
        font-weight: 600;
      }
      .actions {
        display: flex;
        gap: 0.75rem;
        margin-top: 0.75rem;
      }
      .kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: 0.75rem;
      }
      .bars {
        display: flex;
        flex-direction: column;
        gap: 0.45rem;
      }
      .bar-row {
        display: grid;
        grid-template-columns: minmax(90px, 180px) 1fr 70px;
        gap: 0.5rem;
        align-items: center;
      }
      .bar-label {
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        font-size: 0.85rem;
      }
      .bar-track {
        background: rgba(255, 255, 255, 0.08);
        border-radius: 999px;
        height: 10px;
        overflow: hidden;
      }
      .bar-fill {
        height: 100%;
        background: #3dba7a;
        border-radius: 999px;
        min-width: 2px;
      }
      .bar-value {
        text-align: right;
        font-size: 0.85rem;
      }
      .rec-row {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
        gap: 0.65rem;
      }
      .rec-card {
        text-align: left;
        border: 1px solid var(--border-subtle, rgba(255, 255, 255, 0.06));
        background: var(--color-surface, rgba(24, 24, 24, 0.9));
        color: inherit;
        border-radius: 10px;
        padding: 0.85rem 1rem;
        cursor: pointer;
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
      }
      .rec-card:hover {
        border-color: rgba(30, 216, 150, 0.35);
      }
      .rec-card span {
        font-size: 0.78rem;
        opacity: 0.7;
      }
      .table-wrap {
        overflow: auto;
      }
      table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.9rem;
      }
      th,
      td {
        padding: 0.45rem 0.6rem;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        text-align: left;
      }
    `,
  ],
})
export class ComplexReportsPage implements OnInit {
  private readonly api = inject(ComplexReportsApiService);
  private readonly i18n = inject(I18nService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

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
  private maxSeries = 1;

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

  get pointsLabel(): string {
    return countStatLabel(this.selectedId || this.data?.report_id || '');
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
    return cols.filter((c) => !isTechnicalColumnKey(c.key));
  }

  get chartWidgetType(): ChartWidgetType {
    const t = (this.data?.chart_type || 'bar').toLowerCase();
    if (t === 'line') return 'line';
    if (t === 'hbar') return 'hbar';
    if (t === 'table') return 'bar';
    if (this.selectedId === 'releases-status-month') return 'stacked-bar';
    return 'bar';
  }

  get chartLabels(): string[] {
    const series = this.data?.series || [];
    if (this.selectedId === 'releases-status-month') {
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
    const series = this.data?.series || [];
    if (this.selectedId === 'releases-status-month') {
      const months: string[] = [];
      const statuses = new Set<string>();
      const map = new Map<string, number>();
      for (const p of series) {
        const raw = String(p.label || '');
        const parts = raw.split('·').map((s) => s.trim());
        const month = parts[0] || raw;
        const status = parts[1] || 'total';
        if (!months.includes(month)) months.push(month);
        statuses.add(status);
        map.set(`${month}||${status}`, Number(p.value) || 0);
      }
      return [...statuses].map((status) => ({
        name: status,
        data: months.map((m) => map.get(`${m}||${status}`) ?? 0),
      }));
    }
    return [
      {
        name: this.pointsLabel || 'Valor',
        data: series.map((p) => Number(p.value) || 0),
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
        limit: 25,
      })
      .subscribe({
        next: (res) => {
          this.data = res;
          this.maxSeries = Math.max(1, ...res.series.map((s) => Number(s.value || 0)));
          this.syncDateInputsFromResult(res);
          this.loading = false;
        },
        error: (err) => {
          this.error = userFacingHttpError(this.i18n, err);
          this.loading = false;
        },
      });
  }

  barWidth(value: number | null | undefined): number {
    const v = Number(value || 0);
    return Math.max(0, Math.min(100, (v / this.maxSeries) * 100));
  }

  fmt(v: number | null | undefined): string {
    if (v == null || Number.isNaN(Number(v))) return '—';
    return Number(v).toLocaleString(undefined, { maximumFractionDigits: 2 });
  }

  classificationLabel(code?: string | null): string {
    return classificationLabelEs(code);
  }

  columnLabel(c: { key: string; label: string }): string {
    return humanColumnLabel(c.key, c.label);
  }

  displayCell(value: unknown, key: string): string {
    return formatCellDisplay(value, key);
  }

  displaySeriesLabel(label: string): string {
    return formatSeriesLabel(label);
  }

  /** Fill date inputs with the period actually used by the backend (inclusive). */
  private syncDateInputsFromResult(res: ComplexReportData): void {
    if (!res.period_start || !res.period_end_exclusive) return;
    this.dateFrom = res.period_start.slice(0, 10);
    this.dateTo = inclusiveEndIso(res.period_end_exclusive);
  }
}
