import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { HttpErrorResponse } from '@angular/common/http';
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
  styleUrls: ['../../../shared/styles/reports-surface.css'],
  template: `
    <div class="vx-enterprise vx-report-page reports-hub">
      <header class="vx-report-page-header">
        <h1>Reportes</h1>
        <p>Consulta operativa y analítica por módulo. Abre un informe para ver el detalle.</p>
      </header>

      <div class="vx-report-link-row" role="navigation" aria-label="Dirección estratégica">
        <a routerLink="/business-analytics">Dirección estratégica</a>
        <span>Objetivos y KPI conectados</span>
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
        <div class="vx-report-filters" data-testid="hub-catalog-filters">
          <label class="vx-report-field">
            <span>Buscar</span>
            <div class="hub-search">
              <input
                class="input"
                [ngModel]="searchText()"
                (ngModelChange)="searchText.set($event); onFiltersChanged()"
                placeholder="Título o tema…"
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
          </label>
          <label class="vx-report-field">
            <span>Módulo</span>
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
          </label>
          <label class="vx-report-field">
            <span>Categoría</span>
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
          </label>
          <label class="vx-report-field">
            <span>Alcance</span>
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
          </label>
          <label class="vx-report-field">
            <span>Estado</span>
            <select
              class="select"
              [ngModel]="selectedReadiness()"
              (ngModelChange)="selectedReadiness.set($event); onFiltersChanged()"
              data-testid="hub-catalog-readiness"
            >
              <option value="">Todos</option>
              <option value="available">Disponible</option>
              <option value="empty">Sin registros</option>
              <option value="demo">Catálogo de muestra</option>
              <option value="unavailable">No disponible</option>
              <option value="adjusted">Aproximación</option>
            </select>
          </label>
        </div>

        <div class="vx-report-filter-bar">
          <span data-testid="hub-catalog-count">
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

        @if (filtered().length === 0) {
          <app-enterprise-empty-state
            title="Ningún informe coincide con el filtro."
            description="Prueba con otros criterios o limpia los filtros activos."
            ctaLabel="Limpiar filtros"
            (ctaClick)="clearAllFilters()"
          />
        } @else if (searchActive()) {
          <section class="vx-report-section" data-testid="hub-search-results">
            <div class="vx-report-section__toggle" aria-live="polite">
              <span>Resultados</span>
              <span class="vx-report-section__meta">{{ filtered().length }}</span>
            </div>
            <div class="vx-report-cards">
              @for (r of filtered(); track r.kind + ':' + r.id) {
                <a class="vx-report-card" [routerLink]="linkPath(r)" [queryParams]="linkQuery(r)">
                  <strong class="vx-report-card__title">{{ r.title }}</strong>
                  <span class="vx-report-card__meta">{{ r.description }}</span>
                  <span class="vx-report-badges">
                    <span class="vx-report-badge vx-report-badge--subtle">
                      {{ r.kind === 'complex' ? 'Complejo' : 'Simple' }}
                    </span>
                    @if (r.readiness === 'unavailable') {
                      <span class="vx-report-badge vx-report-badge--warn">{{ readyLabel(r.readiness) }}</span>
                    }
                  </span>
                </a>
              }
            </div>
          </section>
        } @else {
          <section class="vx-report-section" data-testid="hub-recommended">
            <button
              type="button"
              class="vx-report-section__toggle"
              (click)="toggleSection('recommended')"
              [attr.aria-expanded]="isOpen('recommended')"
              data-testid="hub-toggle-recommended"
            >
              <span>Recomendados</span>
              <span class="vx-report-section__meta">{{ recommended().length }}</span>
            </button>
            @if (isOpen('recommended')) {
              <div class="vx-report-cards">
                @for (r of recommended(); track r.kind + ':' + r.id) {
                  <a class="vx-report-card" [routerLink]="linkPath(r)" [queryParams]="linkQuery(r)">
                    <strong class="vx-report-card__title">{{ r.title }}</strong>
                    <span class="vx-report-card__meta">{{ r.description }}</span>
                    <span class="vx-report-badges">
                      <span class="vx-report-badge vx-report-badge--subtle">
                        {{ r.kind === 'complex' ? 'Complejo' : 'Simple' }}
                      </span>
@if (r.readiness === 'unavailable') {
                      <span class="vx-report-badge vx-report-badge--warn">{{ readyLabel(r.readiness) }}</span>
                    }
                    </span>
                  </a>
                }
              </div>
            }
          </section>

          @for (g of moduleGroups(); track g.id) {
            <section class="vx-report-section" [attr.data-testid]="'hub-module-' + g.id">
              <button
                type="button"
                class="vx-report-section__toggle"
                (click)="toggleSection(g.id)"
                [attr.aria-expanded]="isOpen(g.id)"
                [attr.data-testid]="'hub-toggle-' + g.id"
              >
                <span>{{ g.label }}</span>
                <span class="vx-report-section__meta">{{ g.items.length }}</span>
              </button>
              @if (isOpen(g.id)) {
                <div class="vx-report-cards">
                  @for (r of g.items; track r.kind + ':' + r.id) {
                    <a class="vx-report-card" [routerLink]="linkPath(r)" [queryParams]="linkQuery(r)">
                      <strong class="vx-report-card__title">{{ r.title }}</strong>
                      <span class="vx-report-card__meta">{{ r.description }}</span>
                      <span class="vx-report-badges">
                        <span class="vx-report-badge vx-report-badge--subtle">
                          {{ r.kind === 'complex' ? 'Complejo' : 'Simple' }}
                        </span>
@if (r.readiness === 'unavailable') {
                      <span class="vx-report-badge vx-report-badge--warn">{{ readyLabel(r.readiness) }}</span>
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
        padding: 0.35rem 0.75rem;
        border-radius: 6px;
        color: var(--color-text-secondary, rgba(255, 255, 255, 0.65));
        border: 1px solid rgba(255, 255, 255, 0.06);
        background: transparent;
      }
      .hub-type-link:hover {
        color: var(--color-text, #fff);
        border-color: rgba(232, 163, 61, 0.28);
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
      .hub-skeleton {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
        gap: 0.75rem;
      }
      .hub-skeleton__card {
        height: 96px;
        border-radius: 8px;
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
    organization: false,
    catalog_publishing: false,
    control_decision: false,
    data_engineering: false,
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

  readonly searchActive = computed(() => this.searchText().trim().length > 0);

  readonly recommended = computed(() => {
    const role = this.auth.role();
    const ids =
      role === 'engineer' ? ENGINEER_RECOMMENDED : ADMIN_RECOMMENDED;
    const mobile =
      typeof window !== 'undefined' && window.matchMedia('(max-width: 520px)').matches;
    const max = mobile ? (role === 'engineer' ? 4 : 6) : role === 'engineer' ? 6 : 8;
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
    let denied = false;
    const emptySimple = { items: [] as SimpleReportCatalogItem[], total: 0 };
    const emptyComplex = { items: [] as ComplexCatalogItem[], total: 0 };
    forkJoin({
      simple: this.simpleApi.catalog().pipe(
        catchError((err: unknown) => {
          if (err instanceof HttpErrorResponse && (err.status === 403 || err.status === 401)) {
            denied = true;
          }
          return of(emptySimple);
        }),
      ),
      complex: this.complexApi.catalog().pipe(
        catchError((err: unknown) => {
          if (err instanceof HttpErrorResponse && (err.status === 403 || err.status === 401)) {
            denied = true;
          }
          return of(emptyComplex);
        }),
      ),
    }).subscribe({
      next: ({ simple, complex }) => {
        const items: HubReportItem[] = [
          ...(simple.items || []).map(fromSimple),
          ...(complex.items || []).map(fromComplex),
        ];
        this.master.set(items);
        this.loading.set(false);
        if (!items.length) {
          this.loadError.set(
            denied
              ? 'No tienes acceso a los informes de esta organización. Pide al propietario que revise tu rol.'
              : 'Todavía no hay informes disponibles para esta organización.',
          );
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
