import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { BusinessAnalyticsApiService } from '../services/business-analytics-api.service';
import {
  DashboardOverview,
  StrategicObjective,
  StrategicOverview,
} from '../models/business-analytics.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { BillingApiService } from '../../billing/services/billing-api.service';
import { CrmApiService } from '../../crm/services/crm-api.service';
import { CrmContextService } from '../../crm/services/crm-context.service';
import { SubscriptionsApiService } from '../../subscriptions/services/subscriptions-api.service';
import { CustomerSuccessApiService } from '../../customer-success/services/customer-success-api.service';
import { I18nService } from '../../../core/services/i18n.service';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

type ObjStatus = 'on_track' | 'attention' | 'no_data';

interface AttentionItem {
  id: string;
  title: string;
  reason: string;
  path: string;
  cta: string;
}

@Component({
  selector: 'app-biz-analytics-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, ...ENTERPRISE_UI_IMPORTS],
  styleUrls: ['./biz-analytics-dashboard.page.css'],
  template: `
    <div class="vx-enterprise strategic-page vx-enterprise--wide" data-testid="strategic-direction">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <header class="st-head">
          <div>
            <p class="st-kicker">Dirección</p>
            <h1 class="st-title">Dirección estratégica</h1>
            <p class="st-sub">Seguimiento de objetivos, metas e indicadores clave.</p>
          </div>
          <div class="st-head-actions">
            @if (strategic?.decision_capability?.can_refresh_strategic) {
              <button type="button" class="btn btn--ghost" (click)="refreshStrategic()" [disabled]="refreshing">
                Actualizar
              </button>
            }
            <a class="btn btn--primary" routerLink="/reports">Abrir Reportes</a>
          </div>
        </header>

        @if (periodLabel) {
          <p class="st-period">Periodo: {{ periodLabel }}</p>
        }

        @if (loading) {
          <app-enterprise-loading-skeleton [rows]="6" />
        } @else if (error) {
          <app-enterprise-error-state [message]="error" (retry)="load()" />
        } @else {
          <section
            class="st-hero"
            [class.st-hero--ok]="attentionCount === 0 && withDataCount > 0"
            [class.st-hero--alert]="attentionCount > 0"
            aria-label="Estado estratégico"
          >
            <p class="st-hero__label">Estado estratégico</p>
            <p class="st-hero__value">{{ strategicHeadline }}</p>
            <p class="st-hero__why">{{ strategicSummary }}</p>
          </section>

          @if (attentionItems.length) {
            <section class="st-panel" aria-label="Requieren atención">
              <h2 class="st-panel__title">Requieren atención</h2>
              <ul class="st-attention">
                @for (a of attentionItems; track a.id) {
                  <li>
                    <span class="sev sev--high"></span>
                    <div>
                      <strong>{{ a.title }}</strong>
                      <span>{{ a.reason }}</span>
                    </div>
                    <a class="st-cta st-cta--primary" [routerLink]="a.path">{{ a.cta }}</a>
                  </li>
                }
              </ul>
            </section>
          }

          <section class="st-panel" aria-label="Objetivos">
            <h2 class="st-panel__title">Objetivos</h2>
            @if (!objectives.length) {
              <app-enterprise-empty-state
                title="Sin objetivos disponibles"
                description="No hay datos estratégicos para el periodo. Actualiza o verifica el contexto de organización."
              />
            } @else {
              <ul class="st-objectives">
                @for (obj of sortedObjectives; track obj.objective_code) {
                  <li [attr.data-objective]="obj.objective_code" [attr.data-status]="statusOf(obj)">
                    <div class="st-obj__main">
                      <div class="st-obj__top">
                        <h3>{{ obj.title }}</h3>
                        <span class="st-status" [attr.data-status]="statusOf(obj)">{{ statusLabel(obj) }}</span>
                      </div>
                      @if (hasValue(obj)) {
                        <p class="st-obj__kpi">
                          <span class="st-obj__kpi-name">{{ kpiLabel(obj) }}</span>
                          <span class="st-obj__kpi-value">{{ formatKpiValue(obj) }}</span>
                        </p>
                        @if (trendText(obj); as t) {
                          <p class="st-obj__trend" [class.down]="t.down" [class.up]="!t.down">{{ t.text }}</p>
                        }
                      } @else {
                        <p class="st-obj__nodata">Sin datos</p>
                      }
                    </div>
                    <div class="st-obj__actions">
                      <a class="st-cta" [routerLink]="drillPath(obj)">Ver análisis</a>
                    </div>
                  </li>
                }
              </ul>
            }
          </section>

          <section class="st-panel" aria-label="KPI clave">
            <h2 class="st-panel__title">KPI clave</h2>
            <div class="st-kpis">
              @for (card of keyKpiCards; track card.id) {
                <article class="st-kpi" [attr.data-status]="card.status">
                  <p class="st-kpi__label">{{ card.label }}</p>
                  <p class="st-kpi__value">{{ card.value }}</p>
                  <p class="st-kpi__status">{{ card.statusLabel }}</p>
                  @if (card.trend) {
                    <p class="st-kpi__trend" [class.down]="card.trendDown" [class.up]="!card.trendDown">{{ card.trend }}</p>
                  }
                </article>
              }
            </div>
          </section>

          <section class="st-panel st-links" aria-label="Profundizar">
            <h2 class="st-panel__title">Profundizar</h2>
            <div class="st-link-row">
              <a routerLink="/reports">Centro de Reportes</a>
              <a routerLink="/workpanel">Workpanel</a>
              <a routerLink="/business-analytics/alerts">Alertas</a>
              <a routerLink="/business-analytics/kpis">Explorar KPI</a>
            </div>
          </section>
        }
      }
    </div>
  `,
})
export class BizAnalyticsDashboardPage implements OnInit {
  private i18n = inject(I18nService);
  private api = inject(BusinessAnalyticsApiService);
  private billing = inject(BillingApiService);
  private crm = inject(CrmApiService);
  private crmCtx = inject(CrmContextService);
  private subs = inject(SubscriptionsApiService);
  private cs = inject(CustomerSuccessApiService);
  private orgCtx = inject(OrganizationContextService);

  private static readonly RISK_KPI = new Set([
    'past_due_mrr',
    'open_cs_risks',
    'open_business_alerts',
    'skip_rate',
  ]);

  strategic: StrategicOverview | null = null;
  overview: DashboardOverview | null = null;
  commercial: {
    openOpportunities: number | null;
    activeSubscriptions: number | null;
    invoiceCount: number | null;
    pastDueCount: number | null;
  } = {
    openOpportunities: null,
    activeSubscriptions: null,
    invoiceCount: null,
    pastDueCount: null,
  };
  loading = false;
  refreshing = false;
  error: string | null = null;
  orgId: number | null = null;

  get objectives(): StrategicObjective[] {
    return this.strategic?.objectives ?? [];
  }

  get sortedObjectives(): StrategicObjective[] {
    const rank = (o: StrategicObjective) => {
      const s = this.statusOf(o);
      if (s === 'attention') return 0;
      if (s === 'on_track') return 1;
      return 2;
    };
    return [...this.objectives].sort((a, b) => rank(a) - rank(b) || a.title.localeCompare(b.title));
  }

  get withDataCount(): number {
    return this.objectives.filter((o) => this.hasValue(o)).length;
  }

  get noDataCount(): number {
    return this.objectives.filter((o) => !this.hasValue(o)).length;
  }

  get attentionCount(): number {
    return this.objectives.filter((o) => this.statusOf(o) === 'attention').length;
  }

  get strategicHeadline(): string {
    if (!this.objectives.length) return 'Sin datos';
    if (this.attentionCount > 0) return 'Requiere atención';
    if (this.withDataCount > 0) return 'En curso';
    return 'Sin datos';
  }

  get strategicSummary(): string {
    if (!this.objectives.length) {
      return 'No hay objetivos con datos para este periodo.';
    }
    const parts: string[] = [];
    if (this.withDataCount) {
      parts.push(
        this.withDataCount === 1
          ? '1 objetivo con señal'
          : `${this.withDataCount} objetivos con señal`,
      );
    }
    if (this.attentionCount) {
      parts.push(
        this.attentionCount === 1
          ? '1 requiere atención'
          : `${this.attentionCount} requieren atención`,
      );
    }
    if (this.noDataCount) {
      parts.push(
        this.noDataCount === 1 ? '1 sin datos' : `${this.noDataCount} sin datos`,
      );
    }
    return parts.join(' · ');
  }

  get periodLabel(): string {
    const start = this.strategic?.period_start;
    const end = this.strategic?.period_end;
    if (!start || !end) return '';
    return `${this.shortDate(start)} – ${this.shortDate(end)}`;
  }

  get attentionItems(): AttentionItem[] {
    const items: AttentionItem[] = [];
    for (const obj of this.objectives) {
      if (this.statusOf(obj) !== 'attention') continue;
      items.push({
        id: obj.objective_code,
        title: obj.title,
        reason: this.attentionReason(obj),
        path: this.drillPath(obj),
        cta: 'Ver análisis',
      });
    }
    if (this.commercial.pastDueCount != null && this.commercial.pastDueCount > 0) {
      items.push({
        id: 'commercial-past-due',
        title: 'Facturas vencidas',
        reason:
          this.commercial.pastDueCount === 1
            ? '1 factura past due en la organización.'
            : `${this.commercial.pastDueCount} facturas past due en la organización.`,
        path: '/reports',
        cta: 'Abrir Reportes',
      });
    }
    return items;
  }

  get keyKpiCards(): Array<{
    id: string;
    label: string;
    value: string;
    status: ObjStatus;
    statusLabel: string;
    trend: string | null;
    trendDown: boolean;
  }> {
    const cards: Array<{
      id: string;
      label: string;
      value: string;
      status: ObjStatus;
      statusLabel: string;
      trend: string | null;
      trendDown: boolean;
    }> = [];

    // Prefer strategic KPIs with values (max 4)
    for (const obj of this.sortedObjectives) {
      if (!this.hasValue(obj) || cards.length >= 4) continue;
      const t = this.trendText(obj);
      cards.push({
        id: obj.objective_code,
        label: this.kpiLabel(obj),
        value: this.formatKpiValue(obj),
        status: this.statusOf(obj),
        statusLabel: this.statusLabel(obj),
        trend: t?.text ?? null,
        trendDown: t?.down ?? false,
      });
    }

    // Fill with commercial signals if still room
    if (cards.length < 4 && this.commercial.openOpportunities != null) {
      cards.push({
        id: 'open-opps',
        label: 'Oportunidades abiertas',
        value: String(this.commercial.openOpportunities),
        status: 'on_track',
        statusLabel: 'En seguimiento',
        trend: null,
        trendDown: false,
      });
    }
    if (cards.length < 4 && this.commercial.activeSubscriptions != null) {
      cards.push({
        id: 'active-subs',
        label: 'Suscripciones activas',
        value: String(this.commercial.activeSubscriptions),
        status: 'on_track',
        statusLabel: 'En seguimiento',
        trend: null,
        trendDown: false,
      });
    }
    if (cards.length < 4 && this.overview?.kpis?.['active_mrr']?.value != null) {
      const v = this.overview.kpis['active_mrr'].value!;
      cards.push({
        id: 'dash-mrr',
        label: 'Ingresos recurrentes',
        value: v.toLocaleString(undefined, { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }),
        status: 'on_track',
        statusLabel: 'En seguimiento',
        trend: null,
        trendDown: false,
      });
    }

    if (!cards.length) {
      cards.push({
        id: 'empty',
        label: 'Indicadores',
        value: 'Sin datos',
        status: 'no_data',
        statusLabel: 'Sin datos',
        trend: null,
        trendDown: false,
      });
    }
    return cards.slice(0, 4);
  }

  hasValue(obj: StrategicObjective): boolean {
    return !obj.empty && obj.kpi != null && obj.kpi.value != null;
  }

  statusOf(obj: StrategicObjective): ObjStatus {
    if (!this.hasValue(obj)) return 'no_data';
    const code = (obj.kpi?.kpi_code || '').toLowerCase();
    const risk = this.isRiskKpi(code);
    const value = Number(obj.kpi!.value);
    if (risk && value > 0) return 'attention';
    const trend = obj.trend;
    const comparable = (this.strategic?.comparable_periods || 0) >= 2;
    if (trend && comparable) {
      if (risk && trend.delta > 0) return 'attention';
      if (!risk && trend.delta < 0) return 'attention';
    }
    return 'on_track';
  }

  statusLabel(obj: StrategicObjective): string {
    const s = this.statusOf(obj);
    if (s === 'attention') return 'Requiere atención';
    if (s === 'no_data') return 'Sin datos';
    return 'En seguimiento';
  }

  kpiLabel(obj: StrategicObjective): string {
    const code = obj.kpi?.kpi_code || '';
    return this.humanKpiName(code) || 'Indicador';
  }

  formatKpiValue(obj: StrategicObjective): string {
    if (!this.hasValue(obj)) return 'Sin datos';
    const v = Number(obj.kpi!.value);
    const kind = this.unitKind(obj.kpi!.unit);
    if (kind === 'currency') {
      return v.toLocaleString('es-ES', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 });
    }
    if (kind === 'percent') {
      return `${v.toLocaleString('es-ES', { maximumFractionDigits: 1 })}%`;
    }
    if (kind === 'count' || Math.abs(v) >= 1000) {
      return v.toLocaleString('es-ES', { maximumFractionDigits: 0 });
    }
    return v.toLocaleString('es-ES', { maximumFractionDigits: 2 });
  }

  trendText(obj: StrategicObjective): { text: string; down: boolean } | null {
    const trend = obj.trend;
    if (!trend || (this.strategic?.comparable_periods || 0) < 2) return null;
    const delta = trend.delta;
    const down = delta < 0;
    const kind = this.unitKind(obj.kpi?.unit);
    const verb = delta === 0 ? 'Se mantuvo' : down ? 'Disminuyó' : 'Aumentó';
    const abs = Math.abs(delta);
    let amount: string | null = null;
    if (kind === 'currency') {
      amount = this.formatCompactMoney(abs);
    } else if (kind === 'percent') {
      amount = `${abs.toLocaleString('es-ES', { maximumFractionDigits: 1 })}%`;
    } else if (kind === 'count') {
      amount = abs.toLocaleString('es-ES', { maximumFractionDigits: 0 });
    }

    if (delta === 0) {
      return { text: 'Se mantuvo frente al periodo anterior.', down: false };
    }
    if (!amount) {
      return {
        text: down
          ? 'El indicador asociado presenta una tendencia desfavorable.'
          : 'El indicador asociado presenta una tendencia favorable.',
        down,
      };
    }
    if (kind === 'count') {
      return { text: `${verb} en ${amount} frente al periodo anterior.`, down };
    }
    return { text: `${verb} ${amount} frente al periodo anterior.`, down };
  }

  drillPath(obj: StrategicObjective): string {
    return obj.evidence_path || obj.report_path || '/reports';
  }

  attentionReason(obj: StrategicObjective): string {
    const code = (obj.kpi?.kpi_code || '').toLowerCase();
    const name = this.kpiLabel(obj);
    if (this.isRiskKpi(code) && this.hasValue(obj) && Number(obj.kpi!.value) > 0) {
      return `${name}: ${this.formatKpiValue(obj)}.`;
    }
    const t = this.trendText(obj);
    if (t) {
      if (t.text.startsWith('El indicador asociado')) {
        return name && name !== 'Indicador' ? `${name}: ${t.text}` : t.text;
      }
      return `${name}: ${t.text}`;
    }
    return 'La señal del objetivo está fuera de lo esperado.';
  }

  private unitKind(unit: string | null | undefined): 'currency' | 'percent' | 'count' | 'unknown' {
    const u = (unit || '').trim().toLowerCase();
    if (!u) return 'unknown';
    if (
      u === 'currency' ||
      u === 'money' ||
      u === 'moneda' ||
      u.includes('currency') ||
      u === 'usd' ||
      ['eur', 'mxn', 'cop', 'pen', 'clp', 'ars', 'brl', 'gbp', 'cad', 'aud'].includes(u)
    ) {
      return 'currency';
    }
    if (u.includes('percent') || u.includes('pct') || u.includes('%') || u === 'percentage') {
      return 'percent';
    }
    if (u === 'count' || u === 'counts' || u === 'conteo') return 'count';
    return 'unknown';
  }

  private formatCompactMoney(abs: number): string {
    if (abs >= 1_000_000) {
      const n = abs / 1_000_000;
      return `$${n.toLocaleString('es-ES', { maximumFractionDigits: 1 })}M`;
    }
    if (abs >= 1_000) {
      const n = abs / 1_000;
      return `$${n.toLocaleString('es-ES', { maximumFractionDigits: 1 })}K`;
    }
    return `$${abs.toLocaleString('es-ES', { maximumFractionDigits: 0 })}`;
  }

  private isRiskKpi(code: string): boolean {
    if (BizAnalyticsDashboardPage.RISK_KPI.has(code)) return true;
    return code.startsWith('past_due_mrr');
  }

  private humanKpiName(code: string): string {
    const map: Record<string, string> = {
      active_members: 'Miembros activos',
      org_active_subscriptions: 'Suscripciones activas',
      platform_active_organizations: 'Organizaciones activas',
      active_mrr: 'Ingresos recurrentes',
      active_arr: 'Ingresos anuales',
      past_due_mrr: 'Ingresos vencidos',
      open_cs_risks: 'Riesgos abiertos',
      renewal_rate: 'Tasa de renovación',
      campaign_roi: 'Retorno de campañas',
      total_streams: 'Streams',
      daily_streams: 'Streams diarios',
      skip_rate: 'Tasa de omisión',
      latest_quality_check: 'Calidad de datos',
      ctl_ok_stages: 'Etapas OK',
      audit_events: 'Eventos de auditoría',
      security_coverage_pct: 'Cobertura de seguridad',
      open_business_alerts: 'Alertas abiertas',
      platform_health_probe: 'Salud de plataforma',
      sla_compliance: 'Cumplimiento SLA',
    };
    if (map[code]) return map[code];
    if (code.startsWith('active_mrr_')) return 'Ingresos recurrentes';
    if (code.startsWith('past_due_mrr_')) return 'Ingresos vencidos';
    return code.replace(/_/g, ' ');
  }

  private shortDate(iso: string): string {
    const d = Date.parse(iso);
    if (Number.isNaN(d)) return iso.slice(0, 10);
    return new Date(d)
      .toLocaleDateString('es-ES', { year: 'numeric', month: 'short', day: 'numeric' })
      .replace(/\./g, '')
      .replace(/\s+/g, ' ')
      .trim();
  }

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    if (this.orgId) this.load();
  }

  refreshStrategic(): void {
    const orgId = this.orgId;
    if (!orgId) return;
    this.refreshing = true;
    this.api.refreshStrategic(orgId).pipe(catchError(() => of(null))).subscribe({
      next: () => {
        this.refreshing = false;
        this.load();
      },
      error: () => {
        this.refreshing = false;
      },
    });
  }

  load(): void {
    const orgId = this.orgId;
    if (!orgId) {
      this.error = this.i18n.t('common.orgRequired');
      return;
    }
    this.loading = true;
    this.error = null;

    const canInvoice = this.orgCtx.hasPermission('invoice.view');
    const canSubs = this.orgCtx.hasPermission('subscription.view');
    const canCs = this.orgCtx.hasPermission('customer_success.view');
    const canCrm = this.crmCtx.hasCrmAccess();

    forkJoin({
      strategic: this.api.getStrategicOverview(orgId).pipe(catchError(() => of(null))),
      dash: this.api.getDashboard(orgId).pipe(catchError(() => of(null))),
      opps: canCrm
        ? this.crm.listOpportunities(1, 50).pipe(catchError(() => of(null)))
        : of(null),
      invoices: canInvoice
        ? this.billing.listInvoices(orgId, {}).pipe(catchError(() => of(null)))
        : of(null),
      subscriptions: canSubs
        ? this.subs.listSubscriptions(orgId, { page: 1, limit: 50 }).pipe(catchError(() => of(null)))
        : of(null),
      risks: canCs
        ? this.cs.listRisks(orgId).pipe(catchError(() => of(null)))
        : of(null),
    }).subscribe({
      next: (res) => {
        this.strategic = res.strategic;
        if (res.dash) {
          this.overview = res.dash;
        }
        if (res.opps?.items) {
          this.commercial.openOpportunities = res.opps.items.filter(
            (o) => !['won', 'lost', 'canceled', 'closed_won', 'closed_lost'].includes(o.stage),
          ).length;
        }
        if (res.subscriptions?.items) {
          this.commercial.activeSubscriptions = res.subscriptions.items.filter((s) =>
            ['active', 'trialing', 'past_due'].includes(s.status),
          ).length;
        }
        if (res.invoices) {
          const items =
            (res.invoices as { items?: Array<{ status: string }> }).items ??
            (Array.isArray(res.invoices) ? (res.invoices as Array<{ status: string }>) : []);
          this.commercial.invoiceCount = items.length;
          this.commercial.pastDueCount = items.filter((i) => i.status === 'past_due').length;
        }
        void res.risks;
        this.loading = false;
      },
      error: () => {
        this.error = this.i18n.t('businessAnalytics.dashboard.loadFailed');
        this.loading = false;
      },
    });
  }
}
