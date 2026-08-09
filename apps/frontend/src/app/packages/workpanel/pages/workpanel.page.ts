import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { WorkpanelApiService, WorkpanelResponse, WorkpanelSection } from '../services/workpanel-api.service';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import { userFacingHttpError } from '../../../core/i18n/user-facing-error';
import { I18nService } from '../../../core/services/i18n.service';
import { RelatedReportsPanelComponent } from '../../reporting/components/related-reports-panel.component';
import { scopeBadgeLabel } from '../../../shared/reports/report-presentation';

@Component({
  selector: 'app-workpanel-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, ...ENTERPRISE_UI_IMPORTS, RelatedReportsPanelComponent],
  template: `
    <div class="vx-enterprise vx-enterprise--wide workpanel-page">
      <header class="wp-head">
        <div>
          <p class="wp-kicker">Control</p>
          <h1 class="wp-title">Workpanel</h1>
          <p class="wp-sub">Resumen táctico del periodo. Indicadores esenciales y pendientes prioritarios.</p>
        </div>
        <div class="wp-head-actions" role="toolbar" aria-label="Controles del workpanel">
          <label class="wp-period">
            <span>Periodo</span>
            <select class="input" [(ngModel)]="period" (ngModelChange)="load()">
              @if (!periodOptions.length) {
                <option value="">Sin periodos disponibles</option>
              }
              @for (p of periodOptions; track p) {
                <option [value]="p">{{ formatPeriodLabel(p) }}</option>
              }
            </select>
          </label>
          <button type="button" class="btn btn--primary" (click)="load()" [disabled]="loading">
            Actualizar
          </button>
        </div>
      </header>

      @if (dataNotice) {
        <p class="wp-chip wp-chip--warn" role="status">{{ dataNotice }}</p>
      }

      @if (loading) {
        <app-enterprise-loading-skeleton [rows]="6" />
      } @else if (error) {
        <app-enterprise-error-state [message]="error" (retry)="load()" />
      } @else if (data) {
        @for (sec of displaySections; track sec.id) {
          <section class="wp-section" [attr.aria-label]="sec.title">
            <div class="wp-section__head">
              <div>
                <h2 class="wp-section__title">{{ sec.title }}</h2>
                <p class="wp-section__desc">{{ sec.description }}</p>
              </div>
              <span class="wp-badge">{{ sec.badge }}</span>
            </div>
            <div class="wp-kpis">
              @for (m of metricsForSection(sec); track m.id) {
                <a
                  class="wp-kpi"
                  [class.wp-kpi--healthy]="m.status === 'healthy_zero'"
                  [class.wp-kpi--empty]="!m.available"
                  [routerLink]="m.available ? detailRoute(m.detail_path).path : null"
                  [queryParams]="m.available ? detailRoute(m.detail_path).queryParams : null"
                >
                  <span class="wp-kpi__label">{{ m.label }}</span>
                  <span class="wp-kpi__value" [attr.title]="metricTitle(m)">{{ formatMetric(m) }}</span>
                  @if (m.available && m.variation_pct != null) {
                    <span class="wp-kpi__delta" [class.up]="m.variation_pct >= 0" [class.down]="m.variation_pct < 0">
                      {{ m.variation_pct >= 0 ? '+' : '' }}{{ m.variation_pct }}%
                    </span>
                  }
                  <span class="wp-kpi__hint">{{ m.available ? m.explanation : 'Sin datos para este periodo.' }}</span>
                  @if (m.display_caption) {
                    <span class="wp-kpi__scope">{{ m.display_caption }}</span>
                  } @else if (m.scope) {
                    <span class="wp-kpi__scope">{{ scopeLabel(m.scope) }}</span>
                  }
                </a>
              }
            </div>
            @if (sec.quick_links?.length) {
              <div class="wp-links">
                @for (ql of sec.quick_links; track ql.path) {
                  <a class="wp-link" [routerLink]="ql.path">{{ ql.label }}</a>
                }
              </div>
            }
          </section>
        }

        <div class="wp-split">
          <section class="wp-panel" aria-label="Pendientes">
            <h2 class="wp-panel__title">Pendientes</h2>
            @if (!data.pendings.length) {
              <p class="wp-empty">Sin pendientes críticos en este periodo.</p>
            } @else {
              <ul class="wp-pending">
                @for (p of data.pendings; track p.id) {
                  <li>
                    <span class="sev" [attr.data-sev]="p.severity || 'medium'"></span>
                    <div class="wp-pending__body">
                      <strong>{{ p.label }}</strong>
                      <span class="qty">{{ p.value }}</span>
                    </div>
                    <a
                      class="wp-pending__action"
                      [routerLink]="detailRoute(p.detail_path).path"
                      [queryParams]="detailRoute(p.detail_path).queryParams"
                    >Abrir</a>
                  </li>
                }
              </ul>
            }
          </section>

          <div class="wp-panel wp-panel--related">
            <app-related-reports-panel
              moduleId="control_decision"
              moduleLabel="Control y decisión"
              [limit]="5"
            />
          </div>
        </div>

        @if (data.links.length) {
          <section class="wp-panel" aria-label="Accesos rápidos">
            <h2 class="wp-panel__title">Accesos rápidos</h2>
            <div class="wp-links">
              @for (l of data.links; track l.path) {
                <a
                  class="wp-link"
                  [routerLink]="detailRoute(l.path).path"
                  [queryParams]="detailRoute(l.path).queryParams"
                >{{ l.label }}</a>
              }
            </div>
          </section>
        }

        <p class="wp-meta">
          Periodo analizado: {{ data.period || '—' }}
          · Última actualización: {{ data.updated_at || '—' }}
          · Datos analíticos disponibles hasta: {{ data.analytics_updated_at || 'sin marca' }}
        </p>
      }
    </div>
  `,
  styles: [
    `
      .wp-head {
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        gap: 1rem;
        margin-bottom: 1rem;
        align-items: flex-end;
      }
      .wp-kicker {
        margin: 0 0 0.25rem;
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--accent, #1ed896);
      }
      .wp-title {
        margin: 0;
        font-size: 1.5rem;
        font-weight: 700;
        letter-spacing: -0.02em;
      }
      .wp-sub {
        margin: 0.35rem 0 0;
        max-width: 36rem;
        font-size: 0.875rem;
        color: var(--color-text-muted, rgba(255, 255, 255, 0.5));
        line-height: 1.4;
      }
      .wp-head-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 0.65rem;
        align-items: flex-end;
      }
      .wp-period {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: var(--color-text-muted, rgba(255, 255, 255, 0.45));
      }
      .wp-period .input {
        min-width: 10rem;
      }
      .wp-chip {
        display: inline-block;
        margin: 0 0 0.85rem;
        padding: 0.35rem 0.65rem;
        border-radius: 6px;
        font-size: 0.78rem;
        background: var(--accent-dim, rgba(30, 216, 150, 0.12));
        color: var(--accent, #1ed896);
      }
      .wp-chip--warn {
        background: rgba(251, 191, 36, 0.12);
        color: #fbbf24;
      }
      .wp-kpis {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.75rem;
        margin-bottom: 1.25rem;
      }
      @media (max-width: 1100px) {
        .wp-kpis {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
      }
      @media (max-width: 560px) {
        .wp-kpis {
          grid-template-columns: 1fr;
        }
      }
      .wp-kpi {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
        padding: 1rem 1.1rem;
        border-radius: 12px;
        text-decoration: none;
        color: inherit;
        background: var(--color-surface, rgba(24, 24, 24, 0.92));
        border: 1px solid transparent;
        transition: border-color 120ms ease, background 120ms ease;
      }
      .wp-kpi:hover {
        border-color: rgba(30, 216, 150, 0.28);
        background: var(--color-surface-2, rgba(32, 32, 32, 0.98));
      }
      .wp-kpi__label {
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--color-text-muted, rgba(255, 255, 255, 0.5));
      }
      .wp-kpi__value {
        font-size: 1.65rem;
        font-weight: 700;
        letter-spacing: -0.03em;
        line-height: 1.15;
      }
      .wp-kpi__delta {
        font-size: 0.78rem;
        font-weight: 600;
      }
      .wp-kpi__delta.up {
        color: var(--accent, #1ed896);
      }
      .wp-kpi__delta.down {
        color: #ef4444;
      }
      .wp-kpi__hint {
        font-size: 0.75rem;
        color: var(--color-text-muted, rgba(255, 255, 255, 0.45));
        line-height: 1.35;
        margin-top: 0.15rem;
      }
      .wp-kpi__scope {
        font-size: 0.68rem;
        font-weight: 600;
        letter-spacing: 0.02em;
        color: rgba(255, 255, 255, 0.4);
        margin-top: 0.2rem;
      }
      .wp-kpi--healthy .wp-kpi__value {
        color: var(--accent, #1ed896);
      }
      .wp-split {
        display: grid;
        grid-template-columns: 1.1fr 0.9fr;
        gap: 1rem;
        margin-bottom: 1rem;
      }
      @media (max-width: 900px) {
        .wp-split {
          grid-template-columns: 1fr;
        }
      }
      .wp-panel {
        padding: 1rem 1.1rem;
        border-radius: 12px;
        background: var(--color-surface, rgba(24, 24, 24, 0.92));
      }
      .wp-panel--related {
        padding: 0;
        background: transparent;
      }
      .wp-panel--related ::ng-deep .related {
        margin: 0;
      }
      .wp-empty {
        margin: 0;
        font-size: 0.875rem;
        color: var(--color-text-muted, rgba(255, 255, 255, 0.55));
      }
      .wp-panel__title {
        margin: 0 0 0.75rem;
        font-size: 0.8125rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: var(--color-text-muted, rgba(255, 255, 255, 0.5));
      }
      .wp-pending {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
        gap: 0.35rem;
      }
      .wp-pending li {
        display: flex;
        align-items: center;
        gap: 0.65rem;
        padding: 0.55rem 0.35rem;
        border-radius: 8px;
      }
      .wp-pending li:hover {
        background: rgba(255, 255, 255, 0.03);
      }
      .sev {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #fbbf24;
        flex-shrink: 0;
      }
      .sev[data-sev='high'],
      .sev[data-sev='critical'] {
        background: #ef4444;
      }
      .sev[data-sev='low'] {
        background: #38bdf8;
      }
      .wp-pending__body {
        flex: 1;
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: 0.1rem;
      }
      .wp-pending__body strong {
        font-size: 0.875rem;
      }
      .qty {
        font-size: 0.75rem;
        color: var(--color-text-muted, rgba(255, 255, 255, 0.45));
      }
      .wp-pending__action {
        font-size: 0.78rem;
        font-weight: 600;
        color: var(--accent, #1ed896);
        text-decoration: none;
      }
      .wp-links {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
      }
      .wp-link {
        text-decoration: none;
        font-size: 0.8125rem;
        font-weight: 600;
        padding: 0.45rem 0.75rem;
        border-radius: 8px;
        color: var(--color-text, #fff);
        background: rgba(255, 255, 255, 0.05);
      }
      .wp-link:hover {
        background: rgba(30, 216, 150, 0.14);
        color: var(--accent, #1ed896);
      }
      .wp-meta {
        margin: 0.75rem 0 0;
        font-size: 0.75rem;
        color: var(--color-text-muted, rgba(255, 255, 255, 0.4));
      }
      .wp-section {
        margin-bottom: 1.25rem;
        padding: 1rem 1.1rem 1.15rem;
        border-radius: 12px;
        background: var(--color-surface, rgba(24, 24, 24, 0.92));
      }
      .wp-section__head {
        display: flex;
        justify-content: space-between;
        gap: 0.75rem;
        align-items: flex-start;
        margin-bottom: 0.75rem;
      }
      .wp-section__title {
        margin: 0;
        font-size: 1.05rem;
        font-weight: 700;
      }
      .wp-section__desc {
        margin: 0.3rem 0 0;
        font-size: 0.8rem;
        color: var(--color-text-muted, rgba(255, 255, 255, 0.5));
        max-width: 40rem;
        line-height: 1.4;
      }
      .wp-badge {
        flex-shrink: 0;
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        padding: 0.3rem 0.55rem;
        border-radius: 999px;
        background: rgba(255, 255, 255, 0.06);
        color: rgba(255, 255, 255, 0.65);
      }
      .wp-kpi--empty {
        opacity: 0.72;
        pointer-events: none;
      }
    `,
  ],
})
export class WorkpanelPage implements OnInit {
  private readonly api = inject(WorkpanelApiService);
  private readonly i18n = inject(I18nService);

  period = '';
  periodOptions: string[] = [];
  loading = false;
  error = '';
  data: WorkpanelResponse | null = null;

  /** Single honest notice when synthetic and/or simulated monetary data is present. */
  get dataNotice(): string | null {
    if (!this.data) return null;
    const synthetic =
      this.data.includes_synthetic_events ||
      this.data.data_classification === 'synthetic' ||
      this.data.data_classification === 'mixed';
    const simulated = this.data.monetary_classification === 'simulated';
    if (!synthetic && !simulated) return null;

    const note = (this.data.classification_note || '').trim();
    const syntheticFallback = this.i18n.t('workpanel.notice.syntheticFallback');
    const simulatedAmounts = this.i18n.t('workpanel.notice.simulatedAmounts');

    if (synthetic && simulated) {
      if (!note) {
        return this.i18n.t('workpanel.notice.combinedCompact');
      }
      const hasSynthetic = WorkpanelPage.mentionsSynthetic(note);
      const hasSimulated = WorkpanelPage.mentionsSimulated(note);
      if (hasSynthetic && hasSimulated) {
        return note;
      }
      let text = note;
      if (!hasSynthetic) {
        text = WorkpanelPage.appendUniqueNotice(text, syntheticFallback);
      }
      if (!hasSimulated) {
        text = WorkpanelPage.appendUniqueNotice(text, simulatedAmounts);
      }
      return text;
    }

    if (synthetic) {
      return note || syntheticFallback;
    }
    return simulatedAmounts;
  }

  /** Detects synthetic / warehouse disclosure already present in a note. */
  private static mentionsSynthetic(text: string): boolean {
    return /sintét|synthetic/i.test(text);
  }

  /** Detects academic / simulated monetary disclosure already present in a note. */
  private static mentionsSimulated(text: string): boolean {
    return /simulad|académic|academic/i.test(text);
  }

  private static appendUniqueNotice(base: string, extra: string): string {
    const b = base.trim();
    const e = extra.trim();
    if (!e) return b;
    if (!b) return e;
    if (b.toLowerCase().includes(e.toLowerCase())) return b;
    return `${b} ${e}`;
  }

  get displaySections(): WorkpanelSection[] {
    if (this.data?.sections?.length) return this.data.sections;
    return [
      {
        id: 'all',
        title: 'Indicadores',
        description: '',
        badge: '',
        scope: 'organization',
        metric_ids: (this.data?.metrics || []).map((m) => m.id),
      },
    ];
  }

  ngOnInit(): void {
    this.period = '';
    this.load();
  }

  load(): void {
    this.loading = true;
    this.error = '';
    this.api.get(this.period || undefined).subscribe({
      next: (res) => {
        this.data = res;
        this.periodOptions = [...(res.available_periods || [])];
        if (res.period && /^\d{4}-\d{2}/.test(res.period)) {
          this.period = res.period.slice(0, 7);
        } else if (res.default_period) {
          this.period = res.default_period;
        }
        if (this.period && !this.periodOptions.includes(this.period)) {
          this.periodOptions = [...this.periodOptions, this.period].sort();
        }
        this.loading = false;
      },
      error: (err) => {
        this.error = userFacingHttpError(this.i18n, err);
        this.loading = false;
      },
    });
  }

  metricsForSection(sec: WorkpanelSection) {
    const ids = new Set(sec.metric_ids || []);
    return (this.data?.metrics || []).filter((m) => ids.has(m.id));
  }

  scopeLabel(scope: string): string {
    return scopeBadgeLabel(scope);
  }

  formatPeriodLabel(ym: string): string {
    const m = String(ym || '').match(/^(\d{4})-(\d{2})/);
    if (!m) return ym;
    const months = [
      'Enero',
      'Febrero',
      'Marzo',
      'Abril',
      'Mayo',
      'Junio',
      'Julio',
      'Agosto',
      'Septiembre',
      'Octubre',
      'Noviembre',
      'Diciembre',
    ];
    const idx = Number(m[2]) - 1;
    return `${months[idx] || m[2]} de ${m[1]}`;
  }

  formatMetric(m: WorkpanelResponse['metrics'][number]): string {
    if (!m.available || m.value == null) return 'Sin datos';
    if (m.status === 'healthy_zero' && m.display_caption) {
      return m.display_caption;
    }
    if (m.unit === 'moneda') {
      return Number(m.value).toLocaleString(undefined, {
        style: 'currency',
        currency: 'USD',
        maximumFractionDigits: 2,
      });
    }
    return Number(m.value).toLocaleString();
  }

  metricTitle(m: WorkpanelResponse['metrics'][number]): string {
    if (!m.available || m.value == null) return 'Sin datos';
    if (m.status === 'healthy_zero') {
      return `${m.display_caption || 'OK'} (valor: ${m.value})`;
    }
    return String(m.value);
  }

  detailRoute(raw: string): { path: string; queryParams: Record<string, string> } {
    const value = (raw || '/').trim() || '/';
    const qIdx = value.indexOf('?');
    let path = value;
    const queryParams: Record<string, string> = {};
    if (qIdx >= 0) {
      path = value.slice(0, qIdx) || '/';
      const params = new URLSearchParams(value.slice(qIdx + 1));
      params.forEach((v, k) => {
        queryParams[k] = v;
      });
    }
    if (path.startsWith('/simple-reports') || path.startsWith('/complex-reports') || path === '/reports') {
      queryParams['from'] = 'workpanel';
    }
    return { path, queryParams };
  }
}
