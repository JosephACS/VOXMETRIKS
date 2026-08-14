import { Component, OnInit, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import {
  WorkpanelApiService,
  WorkpanelMetric,
  WorkpanelResponse,
} from '../services/workpanel-api.service';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import { RelatedReportsPanelComponent } from '../../reporting/components/related-reports-panel.component';
import { userFacingHttpError } from '../../../core/i18n/user-facing-error';
import { I18nService } from '../../../core/services/i18n.service';
import { AuthService } from '../../../core/services/auth.service';

interface PriorityRow {
  id: string;
  severity: 'high' | 'medium' | 'ok';
  title: string;
  reason: string;
  ctaLabel: string | null;
  path: string | null;
  queryParams: Record<string, string>;
}

interface ShortcutItem {
  label: string;
  hint: string;
  path: string;
  queryParams?: Record<string, string>;
  primary?: boolean;
}

@Component({
  selector: 'app-workpanel-page',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink,
    RelatedReportsPanelComponent,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  template: `
    <div class="vx-enterprise vx-enterprise--wide workpanel-page" [class.workpanel-page--engineer]="isEngineerView()">
      <header class="wp-head">
        <div class="wp-head__copy">
          <p class="wp-kicker">{{ pageKicker }}</p>
          <h1 class="wp-title">{{ pageTitle }}</h1>
          <p class="wp-sub">{{ pageSubtitle }}</p>
        </div>
        <div class="wp-head-actions" role="toolbar" [attr.aria-label]="pageTitle">
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
        <p class="wp-notice" role="status" [attr.title]="dataNoticeDetail || dataNotice">
          {{ dataNotice }}
        </p>
      }

      @if (loading) {
        <app-enterprise-loading-skeleton [rows]="5" />
      } @else if (error) {
        <app-enterprise-error-state [message]="error" (retry)="load()" />
      } @else if (data) {
        <p class="wp-freshness">
          Periodo: {{ formatPeriodLabel(data.period || period) }}
          @if (updatedRelative) {
            <span>· Actualizado {{ updatedRelative }}</span>
          }
        </p>

        @if (isEngineerView()) {
          <!-- ENGINEER: Estado técnico -->
          <section class="wp-hero" [class.wp-hero--ok]="!engineerNeedsAttention" [class.wp-hero--alert]="engineerNeedsAttention">
            <p class="wp-hero__label">Estado general</p>
            <p class="wp-hero__value">{{ engineerHeroTitle }}</p>
            <p class="wp-hero__why">{{ engineerHeroWhy }}</p>
          </section>

          <section class="wp-kpis" aria-label="Indicadores técnicos">
            @for (m of engineerPrimaryMetrics; track m.id) {
              <a
                class="wp-kpi"
                [class.wp-kpi--healthy]="m.status === 'healthy_zero'"
                [class.wp-kpi--empty]="!m.available"
                [routerLink]="m.available ? detailRoute(m.detail_path).path : null"
                [queryParams]="m.available ? detailRoute(m.detail_path).queryParams : null"
              >
                <span class="wp-kpi__label">{{ metricLabel(m) }}</span>
                <span class="wp-kpi__value">{{ formatMetric(m) }}</span>
                @if (m.available && m.variation_pct != null) {
                  <span class="wp-kpi__delta" [class.up]="m.variation_pct >= 0" [class.down]="m.variation_pct < 0">
                    {{ m.variation_pct >= 0 ? '+' : '' }}{{ m.variation_pct }}%
                  </span>
                }
              </a>
            }
          </section>

          <div class="wp-split">
            <section class="wp-panel" aria-label="Calidad y almacén">
              <h2 class="wp-panel__title">Calidad / frescura / almacén</h2>
              <ul class="wp-signal-list">
                @for (m of engineerWarehouseSignals; track m.id) {
                  <li>
                    <div>
                      <strong>{{ metricLabel(m) }}</strong>
                      <span>{{ formatMetric(m) }}@if (m.available && m.variation_pct != null) {
                        · {{ m.variation_pct >= 0 ? '+' : '' }}{{ m.variation_pct }}%
                      }</span>
                    </div>
                    @if (m.available && m.detail_path) {
                      <a
                        class="wp-cta wp-cta--ghost"
                        [routerLink]="detailRoute(m.detail_path).path"
                        [queryParams]="detailRoute(m.detail_path).queryParams"
                      >Ver</a>
                    }
                  </li>
                }
              </ul>
              @if (data.analytics_updated_at) {
                <p class="wp-panel__meta">Frescura de datos hasta {{ formatTimestamp(data.analytics_updated_at) }}</p>
              }
            </section>

            <section class="wp-panel" aria-label="Accesos directos">
              <h2 class="wp-panel__title">Accesos directos</h2>
              <div class="wp-shortcuts">
                @for (s of engineerShortcuts; track s.path + s.label) {
                  <a
                    class="wp-shortcut"
                    [class.wp-shortcut--primary]="s.primary"
                    [routerLink]="s.path"
                    [queryParams]="s.queryParams || {}"
                  >
                    <strong>{{ s.label }}</strong>
                    <span>{{ s.hint }}</span>
                  </a>
                }
              </div>
            </section>
          </div>
        } @else {
          <!-- ADMIN: Workpanel táctico -->
          <section class="wp-hero" [class.wp-hero--ok]="!adminHasPriorities" [class.wp-hero--alert]="adminHasPriorities">
            <p class="wp-hero__label">Atención ahora</p>
            <p class="wp-hero__value">{{ adminHeroTitle }}</p>
            <p class="wp-hero__why">{{ adminHeroWhy }}</p>
          </section>

          <section class="wp-kpis" aria-label="Indicadores principales">
            @for (m of adminPrimaryMetrics; track m.id) {
              <a
                class="wp-kpi"
                [class.wp-kpi--healthy]="m.status === 'healthy_zero'"
                [class.wp-kpi--empty]="!m.available"
                [routerLink]="m.available ? detailRoute(m.detail_path).path : null"
                [queryParams]="m.available ? detailRoute(m.detail_path).queryParams : null"
              >
                <span class="wp-kpi__label">{{ metricLabel(m) }}</span>
                <span class="wp-kpi__value">{{ formatMetric(m) }}</span>
                @if (m.available && m.variation_pct != null) {
                  <span class="wp-kpi__delta" [class.up]="m.variation_pct >= 0" [class.down]="m.variation_pct < 0">
                    {{ m.variation_pct >= 0 ? '+' : '' }}{{ m.variation_pct }}%
                  </span>
                }
              </a>
            }
          </section>

          <div class="wp-split">
            <section class="wp-panel" aria-label="Prioridades">
              <h2 class="wp-panel__title">Prioridades</h2>
              @if (!adminHasPriorities) {
                <p class="wp-empty">Sin prioridades críticas en este periodo.</p>
              } @else {
                <ul class="wp-priority">
                  @for (p of adminPriorities; track p.id) {
                    <li>
                      <span class="sev" [attr.data-sev]="p.severity"></span>
                      <div class="wp-priority__body">
                        <strong>{{ p.title }}</strong>
                        <span>{{ p.reason }}</span>
                      </div>
                      @if (p.path && p.ctaLabel) {
                        <a
                          class="wp-cta"
                          [class.wp-cta--primary]="p.severity === 'high'"
                          [routerLink]="p.path"
                          [queryParams]="p.queryParams"
                        >{{ p.ctaLabel }}</a>
                      }
                    </li>
                  }
                </ul>
              }
            </section>

            <section class="wp-panel" aria-label="Actividad y catálogo">
              <h2 class="wp-panel__title">Actividad / catálogo</h2>
              <div class="wp-activity">
                @for (m of adminActivityMetrics; track m.id) {
                  <div class="wp-activity__item">
                    <span class="wp-activity__label">{{ metricLabel(m) }}</span>
                    <span class="wp-activity__value">{{ formatMetric(m) }}</span>
                  </div>
                }
              </div>
              @if (data.analytics_updated_at) {
                <p class="wp-panel__meta">Frescura de datos hasta {{ formatTimestamp(data.analytics_updated_at) }}</p>
              }
            </section>
          </div>
        }

        <app-related-reports-panel
          moduleId="control_decision"
          moduleLabel="Control y decisión"
          [limit]="5"
        />
      }
    </div>
  `,
  styles: [
    `
      .workpanel-page {
        padding-bottom: 0.5rem;
      }
      .wp-head {
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        gap: 1rem;
        margin-bottom: 0.65rem;
        align-items: flex-end;
      }
      .wp-kicker {
        margin: 0 0 0.25rem;
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--vx-accent, var(--accent, #1ed896));
      }
      .wp-title {
        margin: 0;
        font-size: 1.5rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: var(--vx-text, var(--color-text, #fff));
      }
      .wp-sub {
        margin: 0.35rem 0 0;
        max-width: 36rem;
        font-size: 0.875rem;
        color: var(--vx-text-secondary, var(--color-text-muted, rgba(255, 255, 255, 0.55)));
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
        color: var(--vx-text-secondary, var(--color-text-muted, rgba(255, 255, 255, 0.45)));
      }
      .wp-period .input {
        min-width: 10rem;
      }
      .wp-notice {
        margin: 0 0 0.75rem;
        font-size: 0.75rem;
        color: var(--vx-text-secondary, var(--color-text-muted, rgba(255, 255, 255, 0.5)));
        cursor: help;
      }
      .wp-freshness {
        margin: 0 0 0.85rem;
        font-size: 0.75rem;
        color: var(--vx-text-secondary, var(--color-text-muted, rgba(255, 255, 255, 0.45)));
      }
      .wp-hero {
        margin-bottom: 0.9rem;
        padding: 1.1rem 1.2rem;
        border-radius: var(--vx-radius-md, 10px);
        background: var(--vx-surface, var(--color-surface, #121212));
        border: 1px solid var(--vx-border-subtle, rgba(255, 255, 255, 0.08));
      }
      .wp-hero--ok {
        background: color-mix(in srgb, var(--vx-accent, #1ed896) 8%, var(--vx-surface, #121212));
        border-color: color-mix(in srgb, var(--vx-accent, #1ed896) 28%, transparent);
      }
      .wp-hero--alert {
        border-color: color-mix(in srgb, var(--vx-warning, #fbbf24) 35%, transparent);
      }
      .wp-hero__label {
        margin: 0;
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: var(--vx-text-secondary, rgba(255, 255, 255, 0.5));
      }
      .wp-hero__value {
        margin: 0.45rem 0 0;
        font-size: 1.75rem;
        font-weight: 700;
        letter-spacing: -0.03em;
        line-height: 1.15;
        color: var(--vx-text, #fff);
      }
      .wp-hero--ok .wp-hero__value {
        color: var(--vx-accent, #1ed896);
      }
      .wp-hero__why {
        margin: 0.45rem 0 0;
        font-size: 0.85rem;
        color: var(--vx-text-secondary, rgba(255, 255, 255, 0.55));
        line-height: 1.4;
        max-width: 40rem;
      }
      .wp-kpis {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.75rem;
        margin-bottom: 1rem;
      }
      @media (max-width: 900px) {
        .wp-kpis {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
      }
      @media (max-width: 560px) {
        .wp-kpis {
          grid-template-columns: 1fr;
        }
        .wp-head {
          align-items: flex-start;
        }
        .wp-title {
          font-size: 1.35rem;
        }
      }
      .wp-kpi {
        display: flex;
        flex-direction: column;
        gap: 0.25rem;
        padding: 1rem 1.05rem;
        border-radius: var(--vx-radius-md, 10px);
        text-decoration: none;
        color: inherit;
        background: var(--vx-surface, var(--color-surface, #121212));
        border: 1px solid var(--vx-border-subtle, rgba(255, 255, 255, 0.08));
      }
      .wp-kpi:hover {
        border-color: color-mix(in srgb, var(--vx-accent, #1ed896) 30%, transparent);
      }
      .wp-kpi__label {
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--vx-text-secondary, rgba(255, 255, 255, 0.5));
      }
      .wp-kpi__value {
        font-size: 1.45rem;
        font-weight: 700;
        letter-spacing: -0.03em;
        line-height: 1.15;
        color: var(--vx-text, #fff);
      }
      .wp-kpi__delta {
        font-size: 0.78rem;
        font-weight: 600;
      }
      .wp-kpi__delta.up {
        color: var(--vx-accent, #1ed896);
      }
      .wp-kpi__delta.down {
        color: var(--vx-error, #ef4444);
      }
      .wp-kpi--healthy .wp-kpi__value {
        color: var(--vx-accent, #1ed896);
      }
      .wp-kpi--empty {
        opacity: 0.72;
        pointer-events: none;
      }
      .wp-split {
        display: grid;
        grid-template-columns: 1.15fr 0.85fr;
        gap: 0.9rem;
      }
      @media (max-width: 900px) {
        .wp-split {
          grid-template-columns: 1fr;
        }
      }
      .wp-panel {
        padding: 1rem 1.1rem;
        border-radius: var(--vx-radius-md, 10px);
        background: var(--vx-surface, var(--color-surface, #121212));
        border: 1px solid var(--vx-border-subtle, rgba(255, 255, 255, 0.08));
      }
      .wp-panel__title {
        margin: 0 0 0.75rem;
        font-size: 0.8125rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        color: var(--vx-text-secondary, rgba(255, 255, 255, 0.5));
      }
      .wp-panel__meta {
        margin: 0.85rem 0 0;
        font-size: 0.72rem;
        color: var(--vx-text-secondary, rgba(255, 255, 255, 0.42));
      }
      .wp-empty {
        margin: 0;
        font-size: 0.875rem;
        color: var(--vx-text-secondary, rgba(255, 255, 255, 0.55));
      }
      .wp-priority,
      .wp-signal-list {
        list-style: none;
        margin: 0;
        padding: 0;
        display: flex;
        flex-direction: column;
      }
      .wp-priority li,
      .wp-signal-list li {
        display: flex;
        align-items: center;
        gap: 0.7rem;
        padding: 0.7rem 0;
        border-top: 1px solid var(--vx-border-subtle, rgba(255, 255, 255, 0.06));
      }
      .wp-priority li:first-child,
      .wp-signal-list li:first-child {
        border-top: 0;
        padding-top: 0;
      }
      .sev {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--vx-warning, #fbbf24);
        flex-shrink: 0;
      }
      .sev[data-sev='high'] {
        background: var(--vx-error, #ef4444);
      }
      .sev[data-sev='ok'] {
        background: var(--vx-accent, #1ed896);
      }
      .wp-priority__body,
      .wp-signal-list li > div {
        flex: 1;
        min-width: 0;
        display: flex;
        flex-direction: column;
        gap: 0.15rem;
      }
      .wp-priority__body strong,
      .wp-signal-list strong {
        font-size: 0.9rem;
        color: var(--vx-text, #fff);
      }
      .wp-priority__body span,
      .wp-signal-list span {
        font-size: 0.78rem;
        color: var(--vx-text-secondary, rgba(255, 255, 255, 0.5));
        line-height: 1.35;
      }
      .wp-cta {
        flex-shrink: 0;
        text-decoration: none;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 0.4rem 0.7rem;
        border-radius: 8px;
        border: 1px solid var(--vx-border-subtle, rgba(255, 255, 255, 0.12));
        color: var(--vx-text, #fff);
        background: transparent;
      }
      .wp-cta--primary {
        background: var(--vx-accent, #1ed896);
        color: #04140e;
        border-color: transparent;
      }
      .wp-cta--ghost {
        color: var(--vx-accent, #1ed896);
        border-color: transparent;
      }
      .wp-activity {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.55rem;
      }
      @media (max-width: 560px) {
        .wp-activity {
          grid-template-columns: 1fr;
        }
      }
      .wp-activity__item {
        padding: 0.75rem 0.8rem;
        border-radius: 8px;
        background: var(--vx-surface-elevated, rgba(255, 255, 255, 0.03));
      }
      .wp-activity__label {
        display: block;
        font-size: 0.7rem;
        color: var(--vx-text-secondary, rgba(255, 255, 255, 0.5));
      }
      .wp-activity__value {
        display: block;
        margin-top: 0.25rem;
        font-size: 1rem;
        font-weight: 700;
        color: var(--vx-text, #fff);
      }
      .wp-shortcuts {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 0.55rem;
      }
      @media (max-width: 560px) {
        .wp-shortcuts {
          grid-template-columns: 1fr;
        }
      }
      .wp-shortcut {
        display: flex;
        flex-direction: column;
        gap: 0.2rem;
        padding: 0.8rem 0.85rem;
        border-radius: 8px;
        text-decoration: none;
        color: inherit;
        background: var(--vx-surface-elevated, rgba(255, 255, 255, 0.03));
        border: 1px solid var(--vx-border-subtle, rgba(255, 255, 255, 0.08));
      }
      .wp-shortcut strong {
        font-size: 0.85rem;
        color: var(--vx-text, #fff);
      }
      .wp-shortcut span {
        font-size: 0.72rem;
        color: var(--vx-text-secondary, rgba(255, 255, 255, 0.5));
        line-height: 1.35;
      }
      .wp-shortcut--primary {
        border-color: color-mix(in srgb, var(--vx-accent, #1ed896) 35%, transparent);
        background: color-mix(in srgb, var(--vx-accent, #1ed896) 10%, transparent);
      }
    `,
  ],
})
export class WorkpanelPage implements OnInit {
  private readonly api = inject(WorkpanelApiService);
  private readonly i18n = inject(I18nService);
  private readonly auth = inject(AuthService);

  period = '';
  periodOptions: string[] = [];
  loading = false;
  error = '';
  data: WorkpanelResponse | null = null;

  /** Engineer identity (not admin-with-engineer-access). */
  readonly isEngineerView = computed(() => this.auth.role() === 'engineer');

  get pageKicker(): string {
    return this.isEngineerView() ? 'Control técnico' : 'Control';
  }

  get pageTitle(): string {
    return this.isEngineerView() ? 'Estado técnico' : 'Workpanel';
  }

  get pageSubtitle(): string {
    return this.isEngineerView()
      ? 'Salud de la plataforma, procesamiento y señales que requieren atención.'
      : 'Resumen del periodo, prioridades y acciones de la organización.';
  }

  /**
   * Honest data disclosure: says exactly which classifications apply, and never
   * repeats a disclosure the backend note already carries.
   */
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

  get dataNoticeDetail(): string | null {
    if (!this.dataNotice) return null;
    const note = (this.data?.classification_note || '').trim();
    return note || this.dataNotice;
  }

  get updatedRelative(): string | null {
    const raw = this.data?.updated_at;
    if (!raw) return null;
    const ts = Date.parse(raw);
    if (Number.isNaN(ts)) return null;
    const mins = Math.max(0, Math.round((Date.now() - ts) / 60_000));
    if (mins < 1) return 'hace un momento';
    if (mins === 1) return 'hace 1 min';
    if (mins < 60) return `hace ${mins} min`;
    const hours = Math.round(mins / 60);
    if (hours === 1) return 'hace 1 h';
    if (hours < 48) return `hace ${hours} h`;
    return this.formatTimestamp(raw);
  }

  getMetric(id: string): WorkpanelMetric | undefined {
    return (this.data?.metrics || []).find((m) => m.id === id);
  }

  // —— Admin ——
  get adminHasPriorities(): boolean {
    return this.adminPriorities.some((p) => p.severity !== 'ok');
  }

  get adminHeroTitle(): string {
    const actionable = this.adminPriorities.filter((p) => p.severity !== 'ok');
    if (!actionable.length) return 'Sin prioridades críticas';
    if (actionable.length === 1) return '1 prioridad';
    return `${actionable.length} prioridades`;
  }

  get adminHeroWhy(): string {
    const actionable = this.adminPriorities.filter((p) => p.severity !== 'ok');
    if (!actionable.length) {
      return 'La organización no requiere acciones inmediatas.';
    }
    return actionable
      .slice(0, 2)
      .map((p) => p.title)
      .join('. ');
  }

  get adminPrimaryMetrics(): WorkpanelMetric[] {
    const order = ['income_collected', 'open_opportunities', 'streams_period', 'open_alerts'];
    return order.map((id) => this.getMetric(id)).filter((m): m is WorkpanelMetric => !!m).slice(0, 4);
  }

  get adminActivityMetrics(): WorkpanelMetric[] {
    // Streams already lives in primary KPIs; keep this block compact.
    const order = ['catalog_tracks', 'playback_availability'];
    return order.map((id) => this.getMetric(id)).filter((m): m is WorkpanelMetric => !!m);
  }

  get adminPriorities(): PriorityRow[] {
    const rows: PriorityRow[] = [];
    const pendings = this.data?.pendings || [];

    for (const p of pendings) {
      const route = this.detailRoute(p.detail_path);
      rows.push({
        id: `pending:${p.id}`,
        severity: p.severity === 'high' || p.severity === 'critical' ? 'high' : 'medium',
        title: this.humanPendingTitle(p.id, p.label, p.value),
        reason: this.humanPendingReason(p.id, p.label),
        ctaLabel: this.ctaForPending(p.id, p.detail_path),
        path: route.path,
        queryParams: route.queryParams,
      });
    }

    const income = this.getMetric('income_collected');
    if (
      income?.available &&
      income.variation_pct != null &&
      income.variation_pct < 0 &&
      !rows.some((r) => r.id.startsWith('pending:income'))
    ) {
      const route = this.detailRoute(income.detail_path || '/complex-reports?report=income-by-month');
      rows.push({
        id: 'signal:income_down',
        severity: 'medium',
        title: 'Ingresos por debajo del periodo anterior',
        reason: `Variación ${income.variation_pct}%. Revisar tendencia en Reportes.`,
        ctaLabel: 'Abrir Reportes',
        path: route.path,
        queryParams: route.queryParams,
      });
    }

    const alerts = this.getMetric('open_alerts');
    if (
      alerts?.available &&
      alerts.value != null &&
      alerts.value > 0 &&
      !rows.some((r) => r.id.includes('open_alerts') || r.id.includes('alert'))
    ) {
      const route = this.detailRoute(alerts.detail_path);
      rows.push({
        id: 'signal:open_alerts',
        severity: 'high',
        title: alerts.value === 1 ? '1 alerta abierta' : `${alerts.value} alertas abiertas`,
        reason: 'Situaciones de negocio que requieren revisión.',
        ctaLabel: 'Ver alertas',
        path: route.path,
        queryParams: route.queryParams,
      });
    }

    if (!rows.length) {
      rows.push({
        id: 'ok',
        severity: 'ok',
        title: 'Sin alertas críticas',
        reason: 'No hay pendientes abiertos en este periodo.',
        ctaLabel: null,
        path: null,
        queryParams: {},
      });
    }

    return rows;
  }

  // —— Engineer ——
  get engineerFailedJobs(): WorkpanelMetric | undefined {
    return this.getMetric('failed_jobs');
  }

  get engineerNeedsAttention(): boolean {
    const m = this.engineerFailedJobs;
    return !!(m?.available && m.value != null && m.value > 0);
  }

  get engineerHeroTitle(): string {
    return this.engineerNeedsAttention ? 'Requiere atención' : 'Operativo';
  }

  get engineerHeroWhy(): string {
    const m = this.engineerFailedJobs;
    if (this.engineerNeedsAttention && m?.value != null) {
      return m.value === 1 ? '1 trabajo fallido.' : `${m.value} trabajos fallidos.`;
    }
    return 'Sin trabajos fallidos.';
  }

  get engineerPrimaryMetrics(): WorkpanelMetric[] {
    const order = ['failed_jobs', 'active_subscriptions'];
    return order.map((id) => this.getMetric(id)).filter((m): m is WorkpanelMetric => !!m);
  }

  get engineerWarehouseSignals(): WorkpanelMetric[] {
    const order = ['streams_period', 'catalog_tracks', 'playback_availability'];
    return order.map((id) => this.getMetric(id)).filter((m): m is WorkpanelMetric => !!m);
  }

  get engineerShortcuts(): ShortcutItem[] {
    const failed = this.engineerFailedJobs;
    const items: ShortcutItem[] = [
      {
        label: 'Ingeniería de datos',
        hint: 'Pipeline ELT',
        path: '/elt-pipeline',
        primary: true,
      },
      {
        label: 'Explorador',
        hint: 'Almacén de datos',
        path: '/explorer',
      },
      {
        label: 'Reportes',
        hint: 'Centro de informes',
        path: '/reports',
        queryParams: { from: 'workpanel' },
      },
    ];
    if (failed?.detail_path) {
      const route = this.detailRoute(failed.detail_path);
      items.push({
        label: 'Trabajos fallidos',
        hint: 'Detalle de ejecuciones',
        path: route.path,
        queryParams: route.queryParams,
      });
    }
    return items;
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

  metricLabel(m: WorkpanelMetric): string {
    switch (m.id) {
      case 'income_collected':
        return 'Ingresos cobrados';
      case 'invoices_pending':
        return 'Facturas pendientes';
      case 'open_opportunities':
        return 'Oportunidades abiertas';
      case 'open_alerts':
        return 'Alertas abiertas';
      case 'failed_jobs':
        return 'Trabajos fallidos';
      case 'active_subscriptions':
        return 'Suscripciones activas';
      case 'streams_period':
        return 'Streams del periodo';
      case 'catalog_tracks':
        return 'Catálogo';
      case 'playback_availability':
        return 'Reproducción';
      default:
        return m.label;
    }
  }

  private humanPendingTitle(id: string, label: string, value: number): string {
    if (id.includes('invoice') || /factura/i.test(label)) {
      return value === 1 ? '1 factura pendiente' : `${value} facturas pendientes`;
    }
    if (id.includes('alert') || /alerta/i.test(label)) {
      return value === 1 ? '1 alerta abierta' : `${value} alertas abiertas`;
    }
    if (id.includes('failed') || /fallo|job/i.test(label)) {
      return value === 1 ? '1 trabajo fallido' : `${value} trabajos fallidos`;
    }
    return label;
  }

  private humanPendingReason(id: string, label: string): string {
    if (id.includes('invoice') || /factura/i.test(label)) {
      return 'Requiere seguimiento de cobro en la organización activa.';
    }
    if (id.includes('alert') || /alerta/i.test(label)) {
      return 'Situaciones de negocio que requieren revisión.';
    }
    if (id.includes('failed') || /fallo|job/i.test(label)) {
      return 'Hay ejecuciones fallidas que conviene revisar.';
    }
    return label;
  }

  private ctaForPending(id: string, detailPath: string): string {
    if (id.includes('invoice') || /factura|invoice/i.test(detailPath + id)) return 'Ver facturación';
    if (id.includes('alert') || /alerta|alert/i.test(detailPath + id)) return 'Ver alertas';
    if (id.includes('failed') || /job/i.test(detailPath + id)) return 'Ver trabajos';
    return 'Abrir';
  }

  formatPeriodLabel(ym: string): string {
    const m = String(ym || '').match(/^(\d{4})-(\d{2})/);
    if (!m) return ym || '—';
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
    return `${months[idx] || m[2]} ${m[1]}`;
  }

  formatTimestamp(raw: string): string {
    const ts = Date.parse(raw);
    if (Number.isNaN(ts)) return raw;
    try {
      return new Date(ts).toLocaleString(undefined, {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return raw;
    }
  }

  formatMetric(m: WorkpanelMetric): string {
    if (!m.available || m.value == null) return 'Sin datos';
    if (m.id === 'playback_availability') {
      return 'Bajo demanda';
    }
    if (m.status === 'healthy_zero') {
      if (m.id === 'failed_jobs') return 'Sin fallos';
      if (m.id === 'open_alerts') return 'Sin alertas';
      if (m.id === 'open_opportunities') return 'Sin oportunidades';
      if (m.id === 'invoices_pending') return 'Sin pendientes';
      return m.display_caption || '0';
    }
    if (m.unit === 'moneda') {
      return Number(m.value).toLocaleString(undefined, {
        style: 'currency',
        currency: 'USD',
        maximumFractionDigits: 0,
      });
    }
    if (m.id === 'streams_period' && Number(m.value) >= 1000) {
      const k = Number(m.value) / 1000;
      return `${k >= 100 ? Math.round(k) : k.toFixed(k >= 10 ? 0 : 1)}k`;
    }
    return Number(m.value).toLocaleString();
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
