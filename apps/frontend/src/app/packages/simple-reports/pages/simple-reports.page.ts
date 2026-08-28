import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import {
  SimpleReportCatalogItem,
  SimpleReportData,
  SimpleReportsApiService,
} from '../services/simple-reports-api.service';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import { userFacingHttpError } from '../../../core/i18n/user-facing-error';
import { I18nService } from '../../../core/services/i18n.service';
import { filterSimpleReportCatalog } from '../simple-reports-catalog.filter';
import { productVisibleColumns } from '../../../shared/reports/report-presentation';

@Component({
  selector: 'app-simple-reports-page',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  styleUrls: ['../../../shared/styles/reports-surface.css'],
  template: `
    <div class="vx-enterprise vx-report-page simple-reports-page">
      @if (!selected) {
        <header class="vx-report-page-header">
          <h1>Informes simples</h1>
          <p>Listados operacionales por módulo. Elige un informe del catálogo.</p>
        </header>
      }

      @if (contextModuleLabel) {
        <p class="context-banner" role="status">
          Contexto: {{ contextModuleLabel }}
          <a [routerLink]="contextBackLink" class="context-back">Volver al módulo</a>
        </p>
      }

      @if (!selected) {
        <div class="vx-report-filters">
          <label class="vx-report-field">
            <span>Buscar</span>
            <div class="sr-search">
              <input
                class="input"
                [(ngModel)]="searchText"
                (ngModelChange)="onCatalogFiltersChanged()"
                placeholder="Título o tema…"
                data-testid="simple-catalog-search"
              />
              @if (searchText.trim()) {
                <button
                  type="button"
                  class="sr-search__clear"
                  data-testid="simple-catalog-search-clear"
                  (click)="clearCatalogSearch()"
                  aria-label="Borrar búsqueda"
                >
                  ×
                </button>
              }
            </div>
          </label>
          <label class="vx-report-field">
            <span>Módulo</span>
            <select
              class="select"
              [(ngModel)]="selectedModule"
              (ngModelChange)="onCatalogFiltersChanged()"
              data-testid="simple-catalog-module"
            >
              <option value="">Todos los módulos</option>
              @for (m of modules; track m.id) {
                <option [value]="m.id">{{ m.label }}</option>
              }
            </select>
          </label>
          <label class="vx-report-field">
            <span>Categoría</span>
            <select
              class="select"
              [(ngModel)]="selectedCategory"
              (ngModelChange)="onCatalogFiltersChanged()"
              data-testid="simple-catalog-category"
            >
              <option value="">Todas</option>
              @for (c of categories; track c) {
                <option [value]="c">{{ c }}</option>
              }
            </select>
          </label>
        </div>

        <div class="vx-report-filter-bar">
          <span data-testid="simple-catalog-count">{{ visibleCountLabel }}</span>
          @if (hasActiveCatalogFilters) {
            <div class="sr-chips" aria-label="Filtros activos">
              @if (selectedModule) {
                <button type="button" class="sr-chip" (click)="clearModuleFilter()">
                  {{ moduleLabel(selectedModule) }} ×
                </button>
              }
              @if (selectedCategory) {
                <button type="button" class="sr-chip" (click)="clearCategoryFilter()">
                  {{ selectedCategory }} ×
                </button>
              }
              @if (searchText.trim()) {
                <button type="button" class="sr-chip" (click)="clearCatalogSearch()">
                  Búsqueda: {{ searchText.trim() }} ×
                </button>
              }
            </div>
            <button
              type="button"
              class="btn btn--secondary"
              data-testid="simple-catalog-clear-filters"
              (click)="clearCatalogFilters()"
            >
              Limpiar filtros
            </button>
          }
        </div>

        <div class="sr-groups">
          @for (g of grouped; track g.module) {
            <p class="vx-report-group-label">{{ g.label }} ({{ g.items.length }})</p>
            <div class="vx-report-cards">
              @for (r of g.items; track r.id) {
                <button
                  type="button"
                  class="vx-report-card"
                  [class.vx-report-card--active]="selectedReportId === r.id"
                  (click)="selectReport(r.id)"
                >
                  <span class="vx-report-card__title">{{ r.title }}</span>
                  <span class="vx-report-card__meta">{{ r.category }}</span>
                  @if (r.monetary_classification === 'simulated') {
                    <span class="vx-report-badges">
                      <span class="vx-report-badge vx-report-badge--warn">Importes estimados</span>
                    </span>
                  }
                </button>
              }
            </div>
          } @empty {
            <app-enterprise-empty-state
              title="No se encontraron informes con los filtros actuales."
              description="Los filtros de módulo, categoría o búsqueda están limitando el catálogo."
              ctaLabel="Limpiar filtros"
              (ctaClick)="clearCatalogFilters()"
            />
          }
        </div>
      }

      @if (selected) {
        <app-enterprise-page-header
          [reportMode]="true"
          backPath="/reports"
          backLabel="Reportes"
          [title]="selected.title"
          [subtitle]="selected.description || selected.objective || 'Consulta operacional.'"
          badge="Simple"
        />

        <div class="vx-report-toolbar" data-testid="enterprise-filter-bar">
          <div class="vx-report-period">
            <label class="vx-report-field">
              <span>Buscar en resultados</span>
              <input class="input" [(ngModel)]="resultSearch" placeholder="Texto libre" />
            </label>
            @for (f of selected.filters; track f.key) {
              <label class="vx-report-field">
                <span>{{ f.label }}</span>
                @if (f.kind === 'select' && f.options.length) {
                  <select class="select" [(ngModel)]="filterValues[f.key]">
                    <option value="">Todos</option>
                    @for (o of f.options; track o) {
                      <option [value]="o">{{ o }}</option>
                    }
                  </select>
                } @else {
                  <input class="input" [(ngModel)]="filterValues[f.key]" />
                }
              </label>
            }
            <button type="button" class="btn btn--primary" (click)="runQuery()" [disabled]="loading">
              Actualizar
            </button>
            <button type="button" class="btn btn--secondary" (click)="clearResultFilters()">
              Limpiar
            </button>
          </div>
        </div>

        <details class="vx-report-method" data-testid="simple-more-info">
          <summary>Más información</summary>
          <div class="vx-report-method__body">
            @if (selected.decision || selected.objective) {
              <p><strong>Para qué sirve:</strong> {{ selected.decision || selected.objective }}</p>
            }
            <p><strong>Módulo:</strong> {{ selected.business_module_label || selected.area }}</p>
            @if (selected.business_process) {
              <p><strong>Proceso:</strong> {{ selected.business_process }}</p>
            }
            <p><strong>Origen de los datos:</strong> {{ classificationLabel(selected.data_classification) }}</p>
            @if (selected.monetary_classification === 'simulated') {
              <p class="vx-report-muted" role="status">Valores monetarios simulados. No representan cobros reales.</p>
            }
            @if (selected.demo_backend_dependency) {
              <p class="vx-report-muted">Fuente de catálogo ({{ selected.demo_backend_dependency }}).</p>
            }
            <p class="vx-report-method__id"><strong>ID:</strong> {{ selected.id }}</p>
          </div>
        </details>

        @if (loading) {
          <app-enterprise-loading-skeleton [rows]="6" />
        } @else if (error) {
          <app-enterprise-error-state [message]="error" (retry)="runQuery()" />
        } @else if (data) {
          <section class="vx-report-detail" aria-label="Resultados">
            <h2 class="vx-report-section-title">Resultados ({{ data.total }})</h2>
            @if (data.data_classification === 'synthetic' || data.data_classification === 'demo' || data.data_classification === 'mixed') {
              <p class="vx-report-muted" role="status">{{ data.classification_note || classificationLabel(data.data_classification) }}</p>
            }
            @if (data.monetary_classification === 'simulated') {
              <p class="vx-report-muted" role="status">Dinero simulado / académico.</p>
            }
            @if (!data.items.length) {
              <app-enterprise-empty-state
                [title]="emptyTitle"
                [description]="emptyDescription"
                data-testid="simple-empty-state"
              />
            } @else {
              <div class="vx-report-table">
                <table>
                  <thead>
                    <tr>
                      @for (c of visibleColumns; track c.key) {
                        <th>{{ c.label }}</th>
                      }
                    </tr>
                  </thead>
                  <tbody>
                    @for (row of data.items; track $index) {
                      <tr>
                        @for (c of visibleColumns; track c.key) {
                          <td>{{ displayCell(row[c.key]) }}</td>
                        }
                      </tr>
                    }
                  </tbody>
                </table>
              </div>
              <div class="vx-report-actions sr-pager">
                <button type="button" class="btn btn--secondary" [disabled]="page <= 1 || loading" (click)="prevPage()">
                  Anterior
                </button>
                <span class="vx-report-muted">Página {{ page }} · {{ pageSize }} por página</span>
                <button
                  type="button"
                  class="btn btn--secondary"
                  [disabled]="page * pageSize >= data.total || loading"
                  (click)="nextPage()"
                >
                  Siguiente
                </button>
              </div>
            }
          </section>
        }
      }
    </div>
  `,
  styles: [
    `
      .context-banner {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        align-items: center;
        padding: 0.55rem 0;
        margin-bottom: 0.75rem;
        font-size: 0.88rem;
        color: var(--text-muted, rgba(255, 255, 255, 0.55));
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      }
      .context-back {
        font-weight: 600;
        color: var(--accent, #e8a33d);
      }
      .sr-search {
        position: relative;
      }
      .sr-search .input {
        width: 100%;
        padding-right: 2rem;
      }
      .sr-search__clear {
        position: absolute;
        right: 0.35rem;
        top: 50%;
        transform: translateY(-50%);
        border: 0;
        background: transparent;
        cursor: pointer;
        font-size: 1.25rem;
        line-height: 1;
        padding: 0.2rem 0.45rem;
        opacity: 0.7;
        color: inherit;
      }
      .sr-search__clear:hover {
        opacity: 1;
      }
      .sr-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem;
      }
      .sr-chip {
        border: 1px solid rgba(255, 255, 255, 0.12);
        background: transparent;
        border-radius: 6px;
        padding: 0.15rem 0.55rem;
        font-size: 0.78rem;
        cursor: pointer;
        color: inherit;
      }
      .sr-groups {
        display: grid;
        gap: 0.35rem;
        margin: 0.5rem 0 1.5rem;
      }
    `,
  ],
})
export class SimpleReportsPage implements OnInit {
  private readonly api = inject(SimpleReportsApiService);
  private readonly i18n = inject(I18nService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  /** Master catalog — never overwritten by search/module/category filters. */
  allReports: SimpleReportCatalogItem[] = [];
  modules: { id: string; label: string }[] = [];
  categories: string[] = [];
  selectedModule = '';
  selectedCategory = '';
  searchText = '';
  selectedReportId = '';
  selected: SimpleReportCatalogItem | null = null;
  filterValues: Record<string, string> = {};
  /** Result-table free-text filter (not the catalog search). */
  resultSearch = '';
  page = 1;
  pageSize = 12;
  loading = false;
  error = '';
  data: SimpleReportData | null = null;
  contextModule = '';

  get contextModuleLabel(): string {
    return this.modules.find((m) => m.id === this.contextModule)?.label || '';
  }

  get visibleColumns() {
    return productVisibleColumns(this.data?.columns || []);
  }

  get emptyTitle(): string {
    const id = this.selected?.id || '';
    switch (id) {
      case 'business-alerts-open':
        return 'Sin alertas abiertas';
      case 'job-executions-failed':
        return 'Sin ejecuciones fallidas';
      case 'ops-incidents-open':
        return 'Sin incidentes abiertos';
      case 'support-cases-open':
        return 'Sin casos de soporte abiertos';
      case 'crm-opportunities-open':
        return 'Sin oportunidades abiertas';
      case 'data-quality-failed':
        return 'Sin fallos de calidad';
      case 'etl-loads-failed':
        return 'Sin cargas fallidas';
      case 'payment-attempts-failed':
        return 'Sin intentos de pago fallidos';
      case 'audio-source-errors':
        return 'Sin errores de audio';
      default:
        return this.data?.empty_message || 'Sin datos para los filtros actuales.';
    }
  }

  get emptyDescription(): string {
    const id = this.selected?.id || '';
    switch (id) {
      case 'business-alerts-open':
        return 'No hay incidencias de negocio pendientes en este momento.';
      case 'job-executions-failed':
        return 'Los trabajos registrados finalizaron correctamente.';
      case 'ops-incidents-open':
        return 'No hay incidentes operativos pendientes.';
      case 'support-cases-open':
        return 'La bandeja de soporte está al día.';
      case 'crm-opportunities-open':
        return 'No hay oportunidades CRM pendientes de seguimiento.';
      case 'data-quality-failed':
        return 'Las comprobaciones de calidad no reportan fallos abiertos.';
      case 'etl-loads-failed':
        return 'Las cargas registradas finalizaron sin error.';
      case 'payment-attempts-failed':
        return 'No hay intentos de cobro fallidos en el alcance actual.';
      case 'audio-source-errors':
        return 'No hay errores de resolución de audio pendientes.';
      default:
        return 'Pruebe otros filtros o verifique que existan datos operacionales.';
    }
  }

  get contextBackLink(): string {
    switch (this.contextModule) {
      case 'control_decision':
        return '/workpanel';
      case 'catalog_publishing':
        return '/catalog-rights/assets';
      case 'organization':
        return '/organizations';
      case 'data_engineering':
        return '/elt-pipeline';
      default:
        return '/workpanel';
    }
  }

  /** Visible catalog — always derived from allReports. */
  get visibleReports(): SimpleReportCatalogItem[] {
    return filterSimpleReportCatalog(this.allReports, {
      moduleId: this.selectedModule,
      category: this.selectedCategory,
      searchText: this.searchText,
    });
  }

  get hasActiveCatalogFilters(): boolean {
    return !!(this.selectedModule || this.selectedCategory || this.searchText.trim());
  }

  get visibleCountLabel(): string {
    const n = this.visibleReports.length;
    if (this.selectedModule) {
      return `${this.moduleLabel(this.selectedModule)} (${n})`;
    }
    return `Todos los módulos (${n})`;
  }

  get grouped(): { module: string; label: string; items: SimpleReportCatalogItem[] }[] {
    const map = new Map<string, SimpleReportCatalogItem[]>();
    for (const r of this.visibleReports) {
      const key = r.business_module || 'other';
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(r);
    }
    return [...map.entries()].map(([module, items]) => ({
      module,
      label: items[0]?.business_module_label || module,
      items,
    }));
  }

  ngOnInit(): void {
    if (typeof window !== 'undefined' && window.matchMedia('(max-width: 520px)').matches) {
      this.pageSize = 8;
    }
    const qp = this.route.snapshot.queryParamMap;
    this.contextModule = qp.get('module') || qp.get('context') || '';
    if (this.contextModule) this.selectedModule = this.contextModule;
    this.loadCatalog(qp.get('report'));
  }

  loadCatalog(preselect?: string | null): void {
    this.loading = true;
    this.error = '';
    this.api.catalog().subscribe({
      next: (res) => {
        this.allReports = [...res.items];
        this.modules = res.modules?.length
          ? res.modules
          : [...new Map(res.items.map((i) => [i.business_module || '', i.business_module_label || ''])).entries()]
              .filter(([id]) => id)
              .map(([id, label]) => ({ id, label }));
        this.categories = res.categories?.length
          ? res.categories
          : [...new Set(res.items.map((i) => i.category || '').filter(Boolean))];
        this.loading = false;
        if (preselect) this.selectReport(preselect, false);
      },
      error: (err) => {
        this.loading = false;
        this.error = userFacingHttpError(this.i18n, err);
      },
    });
  }

  onCatalogFiltersChanged(): void {
    /* visibleReports recomputes from allReports; selection stays intact */
  }

  clearCatalogSearch(): void {
    this.searchText = '';
    this.onCatalogFiltersChanged();
  }

  clearModuleFilter(): void {
    this.selectedModule = '';
    this.syncModuleQueryParam();
    this.onCatalogFiltersChanged();
  }

  clearCategoryFilter(): void {
    this.selectedCategory = '';
    this.onCatalogFiltersChanged();
  }

  /** Clears catalog search + module + category. Keeps selected report and org context. */
  clearCatalogFilters(): void {
    this.searchText = '';
    this.selectedModule = '';
    this.selectedCategory = '';
    this.syncModuleQueryParam();
    this.onCatalogFiltersChanged();
  }

  moduleLabel(id: string): string {
    return this.modules.find((m) => m.id === id)?.label || id;
  }

  selectReport(id: string, navigate = true): void {
    this.selectedReportId = id;
    this.selected = this.allReports.find((r) => r.id === id) || null;
    this.filterValues = {};
    this.resultSearch = '';
    this.page = 1;
    this.data = null;
    this.error = '';
    if (this.selected) {
      for (const f of this.selected.filters) this.filterValues[f.key] = '';
    }
    // Do not silently change catalog module/category/search on selection.
    if (navigate) {
      void this.router.navigate([], {
        relativeTo: this.route,
        queryParams: {
          report: id || null,
          module: this.selectedModule || this.contextModule || null,
        },
        queryParamsHandling: 'merge',
        replaceUrl: true,
      });
    }
    if (this.selected) this.runQuery();
  }

  backToCatalog(): void {
    this.selectedReportId = '';
    this.selected = null;
    this.data = null;
    this.error = '';
    this.filterValues = {};
    this.resultSearch = '';
    this.page = 1;
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: {
        report: null,
        module: this.selectedModule || this.contextModule || null,
      },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });
  }

  clearResultFilters(): void {
    this.resultSearch = '';
    for (const k of Object.keys(this.filterValues)) this.filterValues[k] = '';
    this.page = 1;
    this.runQuery();
  }

  /** @deprecated alias kept for any external callers — result filters only */
  clearFilters(): void {
    this.clearResultFilters();
  }

  runQuery(): void {
    if (!this.selectedReportId) return;
    this.loading = true;
    this.error = '';
    this.api
      .getData(this.selectedReportId, {
        page: this.page,
        page_size: this.pageSize,
        search: this.resultSearch || undefined,
        filters: { ...this.filterValues },
      })
      .subscribe({
        next: (res) => {
          this.data = res;
          this.loading = false;
        },
        error: (err) => {
          this.loading = false;
          this.error = userFacingHttpError(this.i18n, err);
          this.data = null;
        },
      });
  }

  prevPage(): void {
    if (this.page > 1) {
      this.page -= 1;
      this.runQuery();
    }
  }

  nextPage(): void {
    this.page += 1;
    this.runQuery();
  }

  displayCell(value: unknown): string {
    if (value === null || value === undefined || value === '') return '—';
    return String(value);
  }

  classificationLabel(code?: string): string {
    switch ((code || '').toLowerCase()) {
      case 'synthetic':
        return 'Datos sintéticos';
      case 'demo':
        return 'Datos de catálogo';
      case 'mixed':
        return 'Datos mixtos';
      case 'real':
        return 'Datos reales';
      case 'operational':
        return 'Datos operacionales';
      case 'simulated':
        return 'Estimado';
      default:
        return code || 'Clasificación pendiente';
    }
  }

  private syncModuleQueryParam(): void {
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: {
        module: this.selectedModule || null,
      },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });
  }
}
