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
  template: `
    <div class="vx-enterprise simple-reports-page">
      <app-enterprise-page-header
        title="Reportes"
        subtitle="Informes operacionales por módulo. Un solo motor; sin duplicar consultas."
      />

      @if (contextModuleLabel) {
        <p class="context-banner" role="status">
          Contexto: {{ contextModuleLabel }}
          <a [routerLink]="contextBackLink" class="context-back">Volver al módulo</a>
        </p>
      }

      <app-enterprise-section-card title="Filtros del catálogo">
        <div class="form-grid">
          <app-enterprise-form-field label="Buscar">
            <div class="sr-search">
              <input
                class="input"
                [(ngModel)]="searchText"
                (ngModelChange)="onCatalogFiltersChanged()"
                placeholder="Título, proceso, módulo o categoría"
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
          </app-enterprise-form-field>
          <app-enterprise-form-field label="Módulo">
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
          </app-enterprise-form-field>
          <app-enterprise-form-field label="Categoría">
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
          </app-enterprise-form-field>
        </div>

        <div class="sr-filter-bar">
          <span class="sr-filter-count" data-testid="simple-catalog-count">
            {{ visibleCountLabel }}
          </span>
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
      </app-enterprise-section-card>

      <div class="sr-groups">
        @for (g of grouped; track g.module) {
          <app-enterprise-section-card [title]="g.label + ' (' + g.items.length + ')'">
            <div class="report-cards">
              @for (r of g.items; track r.id) {
                <button
                  type="button"
                  class="report-card"
                  [class.report-card--active]="selectedReportId === r.id"
                  (click)="selectReport(r.id)"
                >
                  <span class="report-card__title">{{ r.title }}</span>
                  <span class="report-card__meta">{{ r.category }} · {{ r.business_process }}</span>
                  <span class="badges">
                    <span class="badge">{{ classificationLabel(r.data_classification) }}</span>
                    @if (r.monetary_classification === 'simulated') {
                      <span class="badge badge--money">Dinero simulado</span>
                    }
                  </span>
                </button>
              }
            </div>
          </app-enterprise-section-card>
        } @empty {
          <app-enterprise-empty-state
            title="No se encontraron informes con los filtros actuales."
            description="Los filtros de módulo, categoría o búsqueda están limitando el catálogo."
            ctaLabel="Limpiar filtros"
            (ctaClick)="clearCatalogFilters()"
          />
        }
      </div>

      @if (selected) {
        <app-enterprise-section-card [title]="selected.title">
          <div class="sr-meta">
            <p><strong>Proceso:</strong> {{ selected.business_process || '—' }}</p>
            <p><strong>Decisión:</strong> {{ selected.decision || selected.objective }}</p>
            <p><strong>Módulo:</strong> {{ selected.business_module_label || selected.area }}</p>
            <p><strong>Clasificación:</strong> {{ classificationLabel(selected.data_classification) }}</p>
            @if (selected.monetary_classification === 'simulated') {
              <p class="muted" role="status">Valores monetarios simulados. No representan cobros reales.</p>
            }
            @if (selected.demo_backend_dependency) {
              <p class="muted">Fuente de datos de demostración ({{ selected.demo_backend_dependency }}); el módulo UI demo no forma parte del MVP.</p>
            }
            <p class="muted">{{ selected.description }}</p>
          </div>

          <div class="form-grid">
            <app-enterprise-form-field label="Buscar en resultados">
              <input class="input" [(ngModel)]="resultSearch" placeholder="Texto libre" />
            </app-enterprise-form-field>
            @for (f of selected.filters; track f.key) {
              <app-enterprise-form-field [label]="f.label">
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
              </app-enterprise-form-field>
            }
          </div>
          <div class="sr-actions">
            <button type="button" class="btn btn--primary" (click)="runQuery()" [disabled]="loading">
              Ejecutar consulta
            </button>
            <button type="button" class="btn btn--secondary" (click)="clearResultFilters()">
              Limpiar filtros de resultado
            </button>
          </div>
        </app-enterprise-section-card>
      }

      @if (selected) {
        @if (loading) {
          <app-enterprise-loading-skeleton [rows]="6" />
        } @else if (error) {
          <app-enterprise-error-state [message]="error" (retry)="runQuery()" />
        } @else if (data) {
          <app-enterprise-section-card [title]="'Resultados (' + data.total + ')'">
            @if (data.data_classification === 'synthetic' || data.data_classification === 'demo' || data.data_classification === 'mixed') {
              <p class="muted" role="status">{{ data.classification_note || classificationLabel(data.data_classification) }}</p>
            }
            @if (data.monetary_classification === 'simulated') {
              <p class="muted" role="status">Dinero simulado / académico.</p>
            }
            @if (!data.items.length) {
              <app-enterprise-empty-state
                [title]="data.empty_message || 'Sin resultados'"
                description="Pruebe otros filtros o verifique que existan datos operacionales."
              />
            } @else {
              <app-enterprise-data-table>
                <table class="data-table">
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
              </app-enterprise-data-table>
              <div class="sr-pager">
                <button type="button" class="btn btn--secondary" [disabled]="page <= 1 || loading" (click)="prevPage()">
                  Anterior
                </button>
                <span>Página {{ page }} · {{ pageSize }} por página</span>
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
          </app-enterprise-section-card>
        }
      }
    </div>
  `,
  styles: [
    `
      .muted { color: var(--text-muted, #666); margin: 0.25rem 0 0; }
      .context-banner {
        display: flex; flex-wrap: wrap; gap: 0.75rem; align-items: center;
        padding: 0.65rem 0.85rem; margin-bottom: 0.75rem;
        border: 1px solid var(--border-color, #ddd); border-radius: 0.4rem;
      }
      .context-back { font-weight: 600; }
      .form-grid {
        display: grid; gap: 0.75rem;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      }
      .sr-search { position: relative; }
      .sr-search .input { width: 100%; padding-right: 2rem; }
      .sr-search__clear {
        position: absolute; right: 0.35rem; top: 50%; transform: translateY(-50%);
        border: 0; background: transparent; cursor: pointer; font-size: 1.25rem;
        line-height: 1; padding: 0.2rem 0.45rem; opacity: 0.7;
      }
      .sr-search__clear:hover { opacity: 1; }
      .sr-filter-bar {
        display: flex; flex-wrap: wrap; gap: 0.65rem; align-items: center;
        margin-top: 0.85rem;
      }
      .sr-filter-count { font-size: 0.9rem; font-weight: 600; }
      .sr-chips { display: flex; flex-wrap: wrap; gap: 0.4rem; }
      .sr-chip {
        border: 1px solid var(--border-color, #ccc); background: transparent;
        border-radius: 999px; padding: 0.15rem 0.55rem; font-size: 0.78rem; cursor: pointer;
      }
      .sr-groups { display: grid; gap: 1rem; margin: 1rem 0; }
      .report-cards {
        display: grid; gap: 0.65rem;
        grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
      }
      .report-card {
        text-align: left; padding: 0.75rem; border-radius: 0.4rem;
        border: 1px solid var(--border-color, #ccc); background: transparent; cursor: pointer;
        display: flex; flex-direction: column; gap: 0.35rem;
      }
      .report-card--active { border-color: var(--vx-accent, #1a7a4c); box-shadow: inset 0 0 0 1px var(--vx-accent, #1a7a4c); }
      .report-card__title { font-weight: 600; font-size: 0.95rem; }
      .report-card__meta { font-size: 0.8rem; opacity: 0.8; }
      .badges { display: flex; flex-wrap: wrap; gap: 0.35rem; }
      .badge {
        font-size: 0.7rem; padding: 0.15rem 0.4rem; border-radius: 0.25rem;
        border: 1px solid currentColor; opacity: 0.85;
      }
      .badge--money { color: #8a5a00; }
      .sr-meta p { margin: 0.3rem 0; }
      .sr-actions, .sr-pager { display: flex; gap: 0.75rem; margin-top: 0.75rem; flex-wrap: wrap; align-items: center; }
      @media (max-width: 480px) {
        .report-cards { grid-template-columns: 1fr; }
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
  pageSize = 25;
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
        return 'Datos demo';
      case 'mixed':
        return 'Datos mixtos';
      case 'real':
        return 'Datos reales';
      case 'operational':
        return 'Datos operacionales';
      case 'simulated':
        return 'Simulado';
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
