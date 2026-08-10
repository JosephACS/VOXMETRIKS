import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { BusinessAnalyticsApiService } from '../services/business-analytics-api.service';
import {
  DashboardOverview,
  StrategicClassification,
  StrategicObjective,
  StrategicOverview,
} from '../models/business-analytics.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { BillingApiService } from '../../billing/services/billing-api.service';
import { CrmApiService } from '../../crm/services/crm-api.service';
import { SubscriptionsApiService } from '../../subscriptions/services/subscriptions-api.service';
import { CustomerSuccessApiService } from '../../customer-success/services/customer-success-api.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-biz-analytics-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  styleUrls: ['./biz-analytics-dashboard.page.css'],
  template: `
    <div class="vx-enterprise biz-analytics-dashboard vx-enterprise--wide" data-testid="strategic-direction">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <app-enterprise-page-header
          [title]="'businessAnalytics.strategic.title' | t:lang()"
          [subtitle]="'businessAnalytics.strategic.subtitle' | t:lang()"
        />

        <nav class="subnav" aria-label="Business analytics">
          <a routerLink="/business-analytics">{{ 'nav.businessAnalytics.dashboard' | t:lang() }}</a>
          <a routerLink="/business-analytics/kpis">{{ 'businessAnalytics.kpis.title' | t:lang() }}</a>
          <a routerLink="/business-analytics/alerts">{{ 'businessAnalytics.dashboard.alerts' | t:lang() }}</a>
          <a routerLink="/business-analytics/recommendations">{{ 'businessAnalytics.dashboard.recommendations' | t:lang() }}</a>
          <a routerLink="/business-analytics/quality">{{ 'businessAnalytics.quality.title' | t:lang() }}</a>
          <a routerLink="/reports">{{ 'businessAnalytics.strategic.reports' | t:lang() }}</a>
          <a routerLink="/business-decisions">{{ 'businessAnalytics.strategic.decisions' | t:lang() }}</a>
        </nav>

        @if (loading) {
          <app-enterprise-loading-skeleton [rows]="8" />
        } @else {
          <section class="period-summary" aria-label="Period">
            <p class="period-line">
              {{ 'common.period' | t:lang() }}:
              <strong>{{ strategic?.period_start || ('common.notAvailable' | t:lang()) }}</strong>
              →
              <strong>{{ strategic?.period_end || ('common.notAvailable' | t:lang()) }}</strong>
            </p>
            <p class="muted">
              {{ 'businessAnalytics.strategic.chain' | t:lang() }}
            </p>
            <div class="period-actions">
              @if (strategic?.decision_capability?.can_refresh_strategic) {
                <button type="button" class="btn btn-secondary" (click)="refreshStrategic()" [disabled]="refreshing">
                  {{ 'businessAnalytics.strategic.refresh' | t:lang() }}
                </button>
              }
              @if (strategic?.decision_capability?.can_draft_report) {
                <a class="btn btn-primary" routerLink="/reports">
                  {{ 'businessAnalytics.strategic.draftReport' | t:lang() }}
                </a>
              }
              @if (strategic?.decision_capability?.can_create_decision) {
                <a class="btn btn-secondary" routerLink="/business-decisions">
                  {{ 'businessAnalytics.strategic.openDecision' | t:lang() }}
                </a>
              }
            </div>
            <p class="muted rule-note">
              {{ 'businessAnalytics.strategic.noAi' | t:lang() }}
            </p>
          </section>

          <section class="oe-grid" aria-label="Strategic objectives">
            @if (!strategic || strategic.objectives.length === 0) {
              <app-enterprise-empty-state
                [title]="'businessAnalytics.strategic.emptyTitle' | t:lang()"
                [description]="'businessAnalytics.strategic.emptyBody' | t:lang()"
              />
            } @else {
              @for (obj of strategic.objectives; track obj.objective_code) {
                <article class="oe-card" [attr.data-objective]="obj.objective_code">
                  <header class="oe-card__head">
                    <span class="oe-code">{{ obj.objective_code }}</span>
                    <h3>{{ obj.title }}</h3>
                    <span class="badge" [class]="badgeClass(obj)">{{ badgeLabel(obj) }}</span>
                  </header>

                  @if (obj.empty || !obj.kpi) {
                    <p class="kpi-null">{{ 'businessAnalytics.strategic.unavailableHonest' | t:lang() }}</p>
                  } @else if (obj.kpi.value == null) {
                    <p class="kpi-null">
                      {{ 'common.notAvailable' | t:lang() }}
                      @if (obj.kpi.unavailable_reason) {
                        <span class="reason"> — {{ obj.kpi.unavailable_reason }}</span>
                      }
                    </p>
                    <p class="kpi-meta">{{ obj.kpi.kpi_code }} · {{ obj.kpi.source_label }}</p>
                  } @else {
                    <p class="kpi-value">
                      {{ obj.kpi.value | number:'1.0-4' }}
                      <span class="unit">{{ obj.kpi.unit }}</span>
                    </p>
                    <p class="kpi-meta">
                      {{ obj.kpi.kpi_code }} · {{ obj.kpi.source_label }} · {{ obj.kpi.quality_status }}
                    </p>
                    <p class="kpi-meta">
                      {{ obj.period_start }} → {{ obj.period_end }}
                    </p>
                  }

                  @if (obj.trend && (strategic.comparable_periods || 0) >= 2) {
                    <p class="trend">
                      {{ 'businessAnalytics.strategic.trend' | t:lang() }}:
                      {{ obj.trend.delta | number:'1.0-2' }}
                    </p>
                  } @else {
                    <p class="trend muted">{{ 'businessAnalytics.strategic.noTrend' | t:lang() }}</p>
                  }

                  <footer class="oe-card__links">
                    @if (obj.evidence_path) {
                      <a [routerLink]="obj.evidence_path">{{ 'businessAnalytics.strategic.evidence' | t:lang() }}</a>
                    }
                    <a routerLink="/reports">{{ 'businessAnalytics.strategic.report' | t:lang() }}</a>
                    <a routerLink="/business-decisions">{{ 'businessAnalytics.strategic.decision' | t:lang() }}</a>
                  </footer>
                </article>
              }
            }
          </section>

          <app-enterprise-section-card [title]="'businessAnalytics.dashboard.snapshot' | t:lang()">
            <p class="muted">{{ 'businessAnalytics.dashboard.commercialHint' | t:lang() }}</p>
            <div class="kpi-grid">
              <app-enterprise-stat-card
                [label]="'businessAnalytics.dashboard.openOpps' | t:lang()"
                [value]="fmt(commercial.openOpportunities)"
              />
              <app-enterprise-stat-card
                [label]="'businessAnalytics.dashboard.activeSubscriptions' | t:lang()"
                [value]="fmt(commercial.activeSubscriptions)"
              />
              <app-enterprise-stat-card
                [label]="'businessAnalytics.dashboard.invoiceCount' | t:lang()"
                [value]="fmt(commercial.invoiceCount)"
              />
              <app-enterprise-stat-card
                [label]="'businessAnalytics.dashboard.pastDueInvoices' | t:lang()"
                [value]="fmt(commercial.pastDueCount)"
              />
              <div class="kpi-card">
                <h3>{{ 'businessAnalytics.dashboard.activeMrr' | t:lang() }}</h3>
                @if (overview?.kpis?.['active_mrr']?.value != null) {
                  <p class="kpi-value">
                    {{ overview!.kpis['active_mrr'].value | number:'1.2-2' }}
                    {{ recurring?.primary_currency || '' }}
                  </p>
                } @else {
                  <p class="kpi-null">{{ 'common.notAvailable' | t:lang() }}</p>
                }
              </div>
              <div class="kpi-card">
                <h3>{{ 'businessAnalytics.dashboard.activeArr' | t:lang() }}</h3>
                @if (overview?.kpis?.['active_arr']?.value != null) {
                  <p class="kpi-value">
                    {{ overview!.kpis['active_arr'].value | number:'1.2-2' }}
                    {{ recurring?.primary_currency || '' }}
                  </p>
                } @else {
                  <p class="kpi-null">{{ 'common.notAvailable' | t:lang() }}</p>
                }
              </div>
            </div>
          </app-enterprise-section-card>
        }

        @if (error) {
          <app-enterprise-error-state [message]="error" (retry)="load()" />
        }
      }
    </div>
  `,
})
export class BizAnalyticsDashboardPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(BusinessAnalyticsApiService);
  private billing = inject(BillingApiService);
  private crm = inject(CrmApiService);
  private subs = inject(SubscriptionsApiService);
  private cs = inject(CustomerSuccessApiService);
  private orgCtx = inject(OrganizationContextService);

  strategic: StrategicOverview | null = null;
  overview: DashboardOverview | null = null;
  recurring: { primary_currency?: string | null } | null = null;
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

  fmt(v: number | null): string {
    return v == null ? this.i18n.t('common.notAvailable') : String(v);
  }

  classificationOf(obj: StrategicObjective): StrategicClassification {
    const raw = (obj.kpi?.classification || '').toLowerCase();
    if (raw === 'real' || raw === 'synthetic' || raw === 'proxy' || raw === 'simulated' || raw === 'unavailable') {
      return raw;
    }
    if (!obj.kpi || obj.kpi.value == null) return 'unavailable';
    if (obj.kpi.is_synthetic) return 'synthetic';
    if (obj.kpi.is_proxy) return 'proxy';
    return 'real';
  }

  badgeClass(obj: StrategicObjective): string {
    return `badge badge--${this.classificationOf(obj)}`;
  }

  badgeLabel(obj: StrategicObjective): string {
    const key = `businessAnalytics.strategic.badge.${this.classificationOf(obj)}`;
    return this.i18n.t(key);
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

    forkJoin({
      strategic: this.api.getStrategicOverview(orgId).pipe(catchError(() => of(null))),
      dash: this.api.getDashboard(orgId).pipe(catchError(() => of(null))),
      opps: this.crm.listOpportunities(1, 50).pipe(catchError(() => of(null))),
      invoices: this.billing.listInvoices(orgId, {}).pipe(catchError(() => of(null))),
      subscriptions: this.subs.listSubscriptions(orgId, { page: 1, limit: 50 }).pipe(catchError(() => of(null))),
      risks: this.cs.listRisks(orgId).pipe(catchError(() => of(null))),
    }).subscribe({
      next: (res) => {
        this.strategic = res.strategic;
        if (res.dash) {
          this.overview = res.dash;
          this.recurring =
            (res.dash as DashboardOverview & { recurring_revenue?: { primary_currency?: string | null } })
              .recurring_revenue ?? null;
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
