import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { BusinessAnalyticsApiService } from '../services/business-analytics-api.service';
import { DashboardOverview } from '../models/business-analytics.models';
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
  template: `
    <div class="vx-enterprise biz-analytics-dashboard vx-enterprise--wide">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <app-enterprise-page-header
          [title]="'businessAnalytics.dashboard.title' | t:lang()"
          [subtitle]="'businessAnalytics.dashboard.subtitle' | t:lang()"
        />

        <nav class="subnav">
          <a routerLink="/business-analytics">{{ 'nav.businessAnalytics.dashboard' | t:lang() }}</a>
          <a routerLink="/business-analytics/kpis">{{ 'businessAnalytics.kpis.title' | t:lang() }}</a>
          <a routerLink="/business-analytics/alerts">{{ 'businessAnalytics.dashboard.alerts' | t:lang() }}</a>
          <a routerLink="/business-analytics/recommendations">{{ 'businessAnalytics.dashboard.recommendations' | t:lang() }}</a>
          <a routerLink="/business-analytics/quality">{{ 'businessAnalytics.quality.title' | t:lang() }}</a>
        </nav>

        @if (loading) {
          <app-enterprise-loading-skeleton [rows]="6" />
        } @else {
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
              <app-enterprise-stat-card
                [label]="'businessAnalytics.dashboard.amountDueSum' | t:lang()"
                [value]="commercial.amountDueSum == null ? ('common.notAvailable' | t:lang()) : (commercial.amountDueSum | number:'1.2-2')"
              />
              <app-enterprise-stat-card
                [label]="'businessAnalytics.dashboard.amountPaidSum' | t:lang()"
                [value]="commercial.amountPaidSum == null ? ('common.notAvailable' | t:lang()) : (commercial.amountPaidSum | number:'1.2-2')"
              />
              <div class="kpi-card">
                <h3>{{ 'businessAnalytics.dashboard.activeMrr' | t:lang() }}</h3>
                @if (overview?.kpis?.['active_mrr']?.value != null) {
                  <p class="kpi-value">
                    {{ overview!.kpis['active_mrr'].value | number:'1.2-2' }}
                    {{ recurring?.primary_currency || '' }}
                  </p>
                  <p class="kpi-source">{{ overview!.kpis['active_mrr'].source_label }}</p>
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
              <div class="kpi-card">
                <h3>{{ 'businessAnalytics.dashboard.pastDueMrr' | t:lang() }}</h3>
                @if (overview?.kpis?.['past_due_mrr']?.value != null) {
                  <p class="kpi-value">{{ overview!.kpis['past_due_mrr'].value | number:'1.2-2' }}</p>
                } @else {
                  <p class="kpi-null">{{ 'common.notAvailable' | t:lang() }}</p>
                }
                <p class="kpi-source muted">{{ 'businessAnalytics.dashboard.pastDueMrrNote' | t:lang() }}</p>
              </div>
              <app-enterprise-stat-card
                [label]="'businessAnalytics.dashboard.openCsRisks' | t:lang()"
                [value]="fmt(commercial.openRisks)"
              />
            </div>
          </app-enterprise-section-card>

          @if (overview) {
            <app-enterprise-section-card [title]="'businessAnalytics.dashboard.warehouseKpi' | t:lang()">
              <p class="muted">
                {{ 'common.period' | t:lang() }}: {{ overview.period || ('common.notAvailable' | t:lang()) }}
              </p>
              <div class="kpi-grid">
                @for (entry of kpiEntries; track entry.code) {
                  <div class="kpi-card">
                    <h3>{{ entry.code }}</h3>
                    @if (entry.data.value != null) {
                      <p class="kpi-value">{{ entry.data.value | number }}</p>
                    } @else {
                      <p class="kpi-null">
                        {{ 'common.notAvailable' | t:lang() }} ({{ entry.data.quality_status || 'null' }})
                      </p>
                    }
                    <p class="kpi-source">{{ entry.data.source_label || ('common.notAvailable' | t:lang()) }}</p>
                    @if (entry.data.is_synthetic) {
                      <span class="badge">{{ 'businessAnalytics.dashboard.synthetic' | t:lang() }}</span>
                    }
                  </div>
                }
              </div>
            </app-enterprise-section-card>
          }
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

  overview: DashboardOverview | null = null;
  recurring: { primary_currency?: string | null } | null = null;
  kpiEntries: { code: string; data: DashboardOverview['kpis'][string] }[] = [];
  commercial: {
    openOpportunities: number | null;
    activeSubscriptions: number | null;
    invoiceCount: number | null;
    pastDueCount: number | null;
    amountDueSum: number | null;
    amountPaidSum: number | null;
    openRisks: number | null;
  } = {
    openOpportunities: null,
    activeSubscriptions: null,
    invoiceCount: null,
    pastDueCount: null,
    amountDueSum: null,
    amountPaidSum: null,
    openRisks: null,
  };
  loading = false;
  error: string | null = null;
  orgId: number | null = null;

  fmt(v: number | null): string {
    return v == null ? this.i18n.t('common.notAvailable') : String(v);
  }

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    if (this.orgId) this.load();
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
      dash: this.api.getDashboard(orgId).pipe(catchError(() => of(null))),
      opps: this.crm.listOpportunities(1, 50).pipe(catchError(() => of(null))),
      invoices: this.billing.listInvoices(orgId, {}).pipe(catchError(() => of(null))),
      subscriptions: this.subs.listSubscriptions(orgId, { page: 1, limit: 50 }).pipe(catchError(() => of(null))),
      risks: this.cs.listRisks(orgId).pipe(catchError(() => of(null))),
    }).subscribe({
      next: (res) => {
        if (res.dash) {
          this.overview = res.dash;
          this.recurring =
            (res.dash as DashboardOverview & { recurring_revenue?: { primary_currency?: string | null } })
              .recurring_revenue ?? null;
          this.kpiEntries = Object.entries(res.dash.kpis || {}).map(([code, data]) => ({ code, data }));
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
            (res.invoices as { items?: Array<{ status: string; amount_due?: number; amount_paid?: number }> }).items ??
            (Array.isArray(res.invoices)
              ? (res.invoices as Array<{ status: string; amount_due?: number; amount_paid?: number }>)
              : []);
          this.commercial.invoiceCount = items.length;
          this.commercial.pastDueCount = items.filter((i) => i.status === 'past_due').length;
          const due = items.map((i) => i.amount_due).filter((n): n is number => n != null);
          const paid = items.map((i) => i.amount_paid).filter((n): n is number => n != null);
          this.commercial.amountDueSum = due.length ? due.reduce((a, b) => a + b, 0) : null;
          this.commercial.amountPaidSum = paid.length ? paid.reduce((a, b) => a + b, 0) : null;
        }
        if (res.risks) {
          this.commercial.openRisks = res.risks.filter((r) =>
            ['open', 'intervention_required', 'monitoring'].includes(String((r as { status?: string }).status)),
          ).length;
        }
        this.loading = false;
      },
      error: () => {
        this.error = this.i18n.t('businessAnalytics.dashboard.loadFailed');
        this.loading = false;
      },
    });
  }
}
