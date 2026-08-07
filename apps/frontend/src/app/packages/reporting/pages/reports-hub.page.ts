import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import { AuthService } from '../../../core/services/auth.service';
import {
  SimpleReportCatalogItem,
  SimpleReportsApiService,
} from '../../simple-reports/services/simple-reports-api.service';
import {
  ComplexCatalogItem,
  ComplexReportsApiService,
} from '../../complex-reports/services/complex-reports-api.service';
import {
  readinessLabelEs,
  scopeBadgeLabel,
} from '../../../shared/reports/report-presentation';

/** Unified hub card (simple + complex catalogs). */
export interface HubReportItem {
  id: string;
  kind: 'simple' | 'complex';
  title: string;
  description: string;
  business_module: string;
  business_module_label: string;
  category: string;
  scope: 'organization' | 'platform' | 'global_analytics';
  readiness: 'available' | 'empty' | 'demo' | 'unavailable' | 'adjusted';
  data_classification: string;
  monetary_classification: string | null;
  route: string;
}

const ADMIN_RECOMMENDED = [
  'business-alerts-open',
  'invoices-pending-overdue',
  'crm-opportunities-open',
  'releases-pending-review',
  'rights-conflicts-open',
  'income-by-month',
  'streams-by-day',
  'top-tracks-period',
] as const;

const ENGINEER_RECOMMENDED = [
  'tracks-without-audio',
  'job-executions-failed',
  'analytical-tables-refresh',
  'data-quality-failed',
  'releases-status-month',
  'streams-by-day',
] as const;

const GLOBAL_ANALYTICS_IDS = new Set([
  'tracks-without-cover',
  'tracks-incomplete-metadata',
  'tracks-without-audio',
  'analytical-tables-refresh',
  'audio-source-errors',
  'streams-by-day',
  'top-tracks-period',
  'top-artists-period',
  'top-genres-period',
]);

const PLATFORM_IDS = new Set([
  'b2c-subscriptions-active',
  'b2c-subscriptions-past-due',
  'b2b-subscriptions-active',
  'b2b-subscriptions-past-due',
  'payouts-with-error',
  'playlists-empty',
  'data-quality-failed',
  'etl-loads-failed',
  'ops-incidents-open',
  'job-executions-failed',
  'sessions-active',
  'roles-permissions',
  'subscription-growth-month',
]);

const MODULE_ORDER = [
  'organization',
  'catalog_publishing',
  'control_decision',
  'data_engineering',
] as const;

const MODULE_LABELS: Record<string, string> = {
  organization: 'Organización',
  catalog_publishing: 'Catálogo y publicación',
  control_decision: 'Control y decisión',
  data_engineering: 'Ingeniería de datos',
};

function fold(value: string): string {
  return String(value || '')
    .normalize('NFD')
    .replace(/\p{M}/gu, '')
    .toLowerCase()
    .trim();
}

function deriveScope(
  id: string,
  orgScoped: boolean | undefined,
): HubReportItem['scope'] {
  if (GLOBAL_ANALYTICS_IDS.has(id)) return 'global_analytics';
  if (PLATFORM_IDS.has(id)) return 'platform';
  if (orgScoped) return 'organization';
  return 'organization';
}

function deriveReadiness(opts: {
  kind: 'simple' | 'complex';
  implementation?: string;
  available?: boolean;
  data_classification?: string;
  monetary_classification?: string | null;
}): HubReportItem['readiness'] {
  if (opts.kind === 'complex' && opts.available === false) return 'unavailable';
  if (opts.implementation === 'pending') return 'unavailable';
  if (opts.implementation === 'implemented_with_adjustment') return 'adjusted';
  const cls = (opts.data_classification || '').toLowerCase();
  if (cls === 'demo' || opts.monetary_classification === 'simulated') return 'demo';
  return 'available';
}

function fromSimple(r: SimpleReportCatalogItem): HubReportItem {
  return {
    id: r.id,
    kind: 'simple',
    title: r.title,
    description: r.description || r.objective || '',
    business_module: r.business_module || '',
    business_module_label: r.business_module_label || MODULE_LABELS[r.business_module || ''] || r.area,
    category: r.category || '',
    scope: deriveScope(r.id, r.org_scoped),
    readiness: deriveReadiness({
      kind: 'simple',
      implementation: r.implementation,
      data_classification: r.data_classification,
      monetary_classification: r.monetary_classification,
    }),
    data_classification: r.data_classification || 'unknown',
    monetary_classification: r.monetary_classification ?? null,
    route: `/simple-reports?report=${encodeURIComponent(r.id)}`,
  };
}

function fromComplex(r: ComplexCatalogItem): HubReportItem {
  return {
    id: r.id,
    kind: 'complex',
    title: r.title,
    description: r.description || r.question || '',
    business_module: r.business_module || '',
    business_module_label: r.business_module_label || MODULE_LABELS[r.business_module || ''] || r.area,
    category: r.category || '',
    scope: deriveScope(r.id, false),
    readiness: deriveReadiness({
      kind: 'complex',
      available: r.available,
      data_classification: r.data_classification,
      monetary_classification: r.monetary_classification,
    }),
    data_classification: r.data_classification || 'unknown',
    monetary_classification: r.monetary_classification ?? null,
    route: `/complex-reports?report=${encodeURIComponent(r.id)}`,
  };
}

/**
 * Spec 043/044 — single Reports entry. Tabs live in module-context chrome.
 * Legacy `/simple-reports` and `/complex-reports` stay valid deep links.
 */
@Component({
  selector: 'app-reports-hub-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise reports-hub">
      <app-enterprise-page-header
        title="Reportes"
        subtitle="Consulta información operativa y analítica. Los datos de demostración y los alcances globales están identificados."
      />

      <div class="hub-type-links" role="navigation" aria-label="Tipo de informe">
        <a routerLink="/simple-reports" class="hub-type-link">Informes simples</a>
        <a routerLink="/complex-reports" class="hub-type-link">Informes complejos</a>
      </div>

      @if (loading()) {
        <div class="hub-skeleton" aria-busy="true" aria-label="Cargando catálogo">
          @for (_ of [1, 2, 3]; track $index) {
            <div class="hub-skeleton__card"></div>
          }
        </div>
      } @else if (loadError()) {
        <app-enterprise-error-state
          [message]="loadError()!"
          retryLabel="Reintentar"
          (retry)="loadCatalog()"
        />
      } @else {
        <app-enterprise-section-card title="Filtros del catálogo">
          <div class="form-grid">
            <app-enterprise-form-field label="Buscar">
              <div class="hub-search">
                <input
                  class="input"
                  [ngModel]="searchText()"
                  (ngModelChange)="searchText.set($event); onFiltersChanged()"
                  placeholder="Título, módulo, categoría o id"
                  data-testid="hub-catalog-search"
                />
                @if (searchText().trim()) {
                  <button
                    type="button"
                    class="hub-search__clear"
                    data-testid="hub-catalog-search-clear"
                    (click)="clearSearchOnly()"
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
                [ngModel]="selectedModule()"
                (ngModelChange)="selectedModule.set($event); onFiltersChanged()"
                data-testid="hub-catalog-module"
              >
                <option value="">Todos los módulos</option>
                @for (m of modules(); track m.id) {
                  <option [value]="m.id">{{ m.label }}</option>
                }
              </select>
            </app-enterprise-form-field>
            <app-enterprise-form-field label="Categoría">
              <select
                class="select"
                [ngModel]="selectedCategory()"
                (ngModelChange)="selectedCategory.set($event); onFiltersChanged()"
                data-testid="hub-catalog-category"
              >
                <option value="">Todas</option>
                @for (c of categories(); track c) {
                  <option [value]="c">{{ c }}</option>
                }
              </select>
            </app-enterprise-form-field>
            <app-enterprise-form-field label="Alcance">
              <select
                class="select"
                [ngModel]="selectedScope()"
                (ngModelChange)="selectedScope.set($event); onFiltersChanged()"
                data-testid="hub-catalog-scope"
              >
                <option value="">Todos</option>
                <option value="organization">Organización</option>
                <option value="platform">Plataforma</option>
                <option value="global_analytics">Analítica global</option>
              </select>
            </app-enterprise-form-field>
            <app-enterprise-form-field label="Estado">
              <select
                class="select"
                [ngModel]="selectedReadiness()"
                (ngModelChange)="selectedReadiness.set($event); onFiltersChanged()"
                data-testid="hub-catalog-readiness"
              >
                <option value="">Todos</option>
                <option value="available">Disponible</option>
                <option value="empty">Sin registros</option>
                <option value="demo">Datos de demostración</option>
                <option value="unavailable">No disponible</option>
                <option value="adjusted">Aproximación</option>
              </select>
            </app-enterprise-form-field>
          </div>

          <div class="hub-filter-bar">
            <span class="hub-filter-count" data-testid="hub-catalog-count">
              {{ filtered().length }} de {{ master().length }} informes
            </span>
            @if (hasActiveFilters()) {
              <button
                type="button"
                class="btn btn--secondary"
                data-testid="hub-catalog-clear-filters"
                (click)="clearAllFilters()"
              >
                Limpiar filtros
              </button>
            }
          </div>
        </app-enterprise-section-card>

        @if (filtered().length === 0) {
          <app-enterprise-empty-state
            title="Ningún informe coincide con el filtro."
            description="Prueba con otros criterios o limpia los filtros activos."
            ctaLabel="Limpiar filtros"
            (ctaClick)="clearAllFilters()"
          />
        } @else {
          <section class="hub-section" data-testid="hub-recommended">
            <button
              type="button"
              class="hub-section__toggle"
              (click)="toggleSection('recommended')"
              [attr.aria-expanded]="isOpen('recommended')"
            >
              <span>Recomendados</span>
              <span class="hub-section__meta">{{ recommended().length }}</span>
            </button>
            @if (isOpen('recommended')) {
              <div class="hub-cards">
                @for (r of recommended(); track r.kind + ':' + r.id) {
                  <a class="hub-card" [routerLink]="linkPath(r)" [queryParams]="linkQuery(r)">
                    <strong>{{ r.title }}</strong>
                    <span class="hub-card__desc">{{ r.description }}</span>
                    <span class="hub-badges">
                      <span class="hub-badge hub-badge--scope">{{ scopeLabel(r.scope) }}</span>
                      <span class="hub-badge hub-badge--ready">{{ readyLabel(r.readiness) }}</span>
                      @if (r.kind === 'complex') {
                        <span class="hub-badge">Complejo</span>
                      } @else {
                        <span class="hub-badge">Simple</span>
                      }
                    </span>
                  </a>
                }
              </div>
            }
          </section>

          @for (g of moduleGroups(); track g.id) {
            <section class="hub-section" [attr.data-testid]="'hub-module-' + g.id">
              <button
                type="button"
                class="hub-section__toggle"
                (click)="toggleSection(g.id)"
                [attr.aria-expanded]="isOpen(g.id)"
              >
                <span>{{ g.label }}</span>
                <span class="hub-section__meta">{{ g.items.length }}</span>
              </button>
              @if (isOpen(g.id)) {
                <div class="hub-cards">
                  @for (r of g.items; track r.kind + ':' + r.id) {
                    <a class="hub-card" [routerLink]="linkPath(r)" [queryParams]="linkQuery(r)">
                      <strong>{{ r.title }}</strong>
                      <span class="hub-card__desc">{{ r.description }}</span>
                      <span class="hub-badges">
                        <span class="hub-badge hub-badge--scope">{{ scopeLabel(r.scope) }}</span>
                        <span class="hub-badge hub-badge--ready">{{ readyLabel(r.readiness) }}</span>
                        @if (r.category) {
                          <span class="hub-badge">{{ r.category }}</span>
                        }
                      </span>
                    </a>
                  }
                </div>
              }
            </section>
          }
        }
      }
    </div>
  `,
  styles: [
    `
      .hub-type-links {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin: 0 0 1rem;
      }
      .hub-type-link {
        text-decoration: none;
        font-size: 0.8125rem;
        font-weight: 600;
        padding: 0.4rem 0.85rem;
        border-radius: 6px;
        color: var(--color-text-secondary, rgba(255, 255, 255, 0.65));
        background: var(--color-surface-3, rgba(255, 255, 255, 0.04));
        border: 1px solid var(--border-subtle, rgba(255, 255, 255, 0.06));
      }
      .hub-type-link:hover {
        color: var(--color-text, #fff);
        border-color: rgba(30, 216, 150, 0.28);
      }
      .form-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
        gap: 0.75rem;
      }
      .hub-search {
        position: relative;
        display: flex;
        align-items: center;
      }
      .hub-search .input {
        width: 100%;
        padding-right: 2rem;
      }
      .hub-search__clear {
        position: absolute;
        right: 0.35rem;
        border: 0;
        background: transparent;
        color: var(--color-text-muted, rgba(255, 255, 255, 0.45));
        cursor: pointer;
        font-size: 1.1rem;
        line-height: 1;
        padding: 0.25rem 0.4rem;
      }
      .hub-filter-bar {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.75rem;
        margin-top: 0.85rem;
      }
      .hub-filter-count {
        font-size: 0.8125rem;
        color: var(--color-text-muted, rgba(255, 255, 255, 0.45));
      }
      .hub-section {
        margin: 0.85rem 0 1.1rem;
        border: 1px solid var(--border-subtle, rgba(255, 255, 255, 0.06));
        border-radius: 10px;
        background: var(--color-surface, rgba(24, 24, 24, 0.92));
        overflow: hidden;
      }
      .hub-section__toggle {
        width: 100%;
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 0.75rem;
        padding: 0.85rem 1rem;
        border: 0;
        background: transparent;
        color: inherit;
        cursor: pointer;
        font-weight: 600;
        font-size: 0.9375rem;
        text-align: left;
      }
      .hub-section__toggle:hover {
        background: rgba(255, 255, 255, 0.03);
      }
      .hub-section__meta {
        font-size: 0.75rem;
        font-weight: 500;
        color: var(--color-text-muted, rgba(255, 255, 255, 0.45));
      }
      .hub-cards {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
        gap: 0.65rem;
        padding: 0 1rem 1rem;
      }
      .hub-card {
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
        padding: 0.9rem 1rem;
        border-radius: 8px;
        text-decoration: none;
        color: inherit;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid var(--border-subtle, rgba(255, 255, 255, 0.05));
      }
      .hub-card:hover {
        border-color: rgba(30, 216, 150, 0.28);
      }
      .hub-card__desc {
        font-size: 0.75rem;
        color: var(--color-text-muted, rgba(255, 255, 255, 0.45));
        line-height: 1.35;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
      }
      .hub-badges {
        display: flex;
        flex-wrap: wrap;
        gap: 0.3rem;
        margin-top: 0.2rem;
      }
      .hub-badge {
        font-size: 0.6875rem;
        font-weight: 600;
        padding: 0.15rem 0.45rem;
        border-radius: 4px;
        background: rgba(255, 255, 255, 0.06);
        color: var(--color-text-secondary, rgba(255, 255, 255, 0.7));
      }
      .hub-badge--scope {
        border: 1px solid rgba(30, 216, 150, 0.25);
      }
      .hub-badge--ready {
        border: 1px solid rgba(255, 255, 255, 0.12);
      }
      .hub-skeleton {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
        gap: 0.75rem;
      }
      .hub-skeleton__card {
        height: 96px;
        border-radius: 10px;
        background: linear-gradient(
          90deg,
          rgba(255, 255, 255, 0.04),
          rgba(255, 255, 255, 0.08),
          rgba(255, 255, 255, 0.04)
        );
        background-size: 200% 100%;
        animation: hubPulse 1.2s ease-in-out infinite;
      }
      @keyframes hubPulse {
        0% {
          background-position: 100% 0;
        }
        100% {
          background-position: -100% 0;
        }
      }
      @media (max-width: 390px) {
        .hub-cards {
          grid-template-columns: 1fr;
        }
      }
    `,
  ],
})
export class ReportsHubPage implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly auth = inject(AuthService);
  private readonly simpleApi = inject(SimpleReportsApiService);
  private readonly complexApi = inject(ComplexReportsApiService);

  /** Master catalog — never mutated by filters. */
  readonly master = signal<HubReportItem[]>([]);
  readonly loading = signal(true);
  readonly loadError = signal<string | null>(null);
  readonly openSections = signal<Record<string, boolean>>({
    recommended: true,
    organization: true,
    catalog_publishing: true,
    control_decision: true,
    data_engineering: true,
  });

  readonly searchText = signal('');
  readonly selectedModule = signal('');
  readonly selectedCategory = signal('');
  readonly selectedScope = signal('');
  readonly selectedReadiness = signal('');

  readonly filtered = computed(() =>
    this.applyFilters(this.master(), {
      searchText: this.searchText(),
      moduleId: this.selectedModule(),
      category: this.selectedCategory(),
      scope: this.selectedScope(),
      readiness: this.selectedReadiness(),
    }),
  );

  readonly recommended = computed(() => {
    const role = this.auth.role();
    const ids =
      role === 'engineer' ? ENGINEER_RECOMMENDED : ADMIN_RECOMMENDED;
    const max = role === 'engineer' ? 6 : 8;
    const byId = new Map(this.filtered().map((r) => [r.id, r]));
    const out: HubReportItem[] = [];
    for (const id of ids) {
      const hit = byId.get(id);
      if (hit) out.push(hit);
      if (out.length >= max) break;
    }
    return out;
  });

  readonly modules = computed(() => {
    const seen = new Map<string, string>();
    for (const r of this.master()) {
      if (r.business_module && !seen.has(r.business_module)) {
        seen.set(
          r.business_module,
          r.business_module_label || MODULE_LABELS[r.business_module] || r.business_module,
        );
      }
    }
    return MODULE_ORDER.filter((id) => seen.has(id)).map((id) => ({
      id,
      label: seen.get(id)!,
    }));
  });

  readonly categories = computed(() => {
    const set = new Set<string>();
    for (const r of this.master()) {
      if (r.category) set.add(r.category);
    }
    return Array.from(set).sort((a, b) => a.localeCompare(b, 'es'));
  });

  readonly moduleGroups = computed(() => {
    const items = this.filtered();
    return MODULE_ORDER.map((id) => {
      const groupItems = items.filter((r) => r.business_module === id);
      return {
        id,
        label: MODULE_LABELS[id] || id,
        items: groupItems,
      };
    }).filter((g) => g.items.length > 0);
  });

  ngOnInit(): void {
    const type = (this.route.snapshot.queryParamMap.get('type') || '').toLowerCase();
    const rest = { ...this.route.snapshot.queryParams };
    delete rest['type'];
    if (type === 'complex') {
      void this.router.navigate(['/complex-reports'], {
        queryParams: rest,
        replaceUrl: true,
      });
      return;
    }
    if (type === 'simple') {
      void this.router.navigate(['/simple-reports'], {
        queryParams: rest,
        replaceUrl: true,
      });
      return;
    }
    // Preserve deep-link ?report= into the correct engine when present without type
    const report = this.route.snapshot.queryParamMap.get('report');
    if (report) {
      // Stay on hub unless legacy type redirect; report cards deep-link themselves.
    }
    this.loadCatalog();
  }

  loadCatalog(): void {
    this.loading.set(true);
    this.loadError.set(null);
    forkJoin({
      simple: this.simpleApi.catalog().pipe(catchError(() => of({ items: [], total: 0 }))),
      complex: this.complexApi.catalog().pipe(catchError(() => of({ items: [], total: 0 }))),
    }).subscribe({
      next: ({ simple, complex }) => {
        const items: HubReportItem[] = [
          ...(simple.items || []).map(fromSimple),
          ...(complex.items || []).map(fromComplex),
        ];
        this.master.set(items);
        this.loading.set(false);
        if (!items.length) {
          this.loadError.set('El catálogo de informes está vacío o no está disponible.');
        }
      },
      error: () => {
        this.loading.set(false);
        this.loadError.set('Error de red al cargar informes simples y complejos.');
      },
    });
  }

  onFiltersChanged(): void {
    // Filters are applied via computed(filtered) from master — no mutation.
  }

  hasActiveFilters(): boolean {
    return !!(
      this.searchText().trim() ||
      this.selectedModule() ||
      this.selectedCategory() ||
      this.selectedScope() ||
      this.selectedReadiness()
    );
  }

  clearSearchOnly(): void {
    this.searchText.set('');
  }

  clearAllFilters(): void {
    this.searchText.set('');
    this.selectedModule.set('');
    this.selectedCategory.set('');
    this.selectedScope.set('');
    this.selectedReadiness.set('');
  }

  isOpen(key: string): boolean {
    return !!this.openSections()[key];
  }

  toggleSection(key: string): void {
    const cur = { ...this.openSections() };
    cur[key] = !cur[key];
    this.openSections.set(cur);
  }

  scopeLabel(scope: string): string {
    return scopeBadgeLabel(scope) || scope;
  }

  readyLabel(code: string): string {
    return readinessLabelEs(code) || code;
  }

  linkPath(r: HubReportItem): string {
    return r.kind === 'complex' ? '/complex-reports' : '/simple-reports';
  }

  linkQuery(r: HubReportItem): Record<string, string> {
    return { report: r.id };
  }

  private applyFilters(
    all: readonly HubReportItem[],
    state: {
      searchText: string;
      moduleId: string;
      category: string;
      scope: string;
      readiness: string;
    },
  ): HubReportItem[] {
    const q = fold(state.searchText);
    const moduleId = (state.moduleId || '').trim();
    const category = (state.category || '').trim();
    const scope = (state.scope || '').trim();
    const readiness = (state.readiness || '').trim();

    return all.filter((r) => {
      if (moduleId && r.business_module !== moduleId) return false;
      if (category && r.category !== category) return false;
      if (scope && r.scope !== scope) return false;
      if (readiness && r.readiness !== readiness) return false;
      if (q) {
        const blob = fold(
          [
            r.title,
            r.description,
            r.business_module_label,
            r.business_module,
            r.category,
            r.id,
            r.kind,
            r.scope,
            r.readiness,
          ].join(' '),
        );
        if (!blob.includes(q)) return false;
      }
      return true;
    });
  }
}
