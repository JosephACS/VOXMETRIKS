import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { RoyaltiesApiService } from '../services/royalties.api';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { RoyaltyMetrics } from '../models/royalties.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';
import { userFacingHttpError } from '../../../core/i18n/user-facing-error';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import { royaltiesAccess } from '../royalties-access';

@Component({
  selector: 'app-royalties-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, TranslatePipe, LocaleMoneyPipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise royalties-dashboard-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <app-enterprise-page-header
          [title]="'royalties.dashboard.title' | t:lang()"
          [subtitle]="'royalties.dashboard.subtitle' | t:lang()"
        />

        <div class="vx-sim-callout" role="note" data-testid="royalties-sim-banner">
          {{ 'royalties.payout.simulatedBanner' | t:lang() }}
        </div>

        @if (readOnly) {
          <div class="alert alert--warn" role="status">
            {{ 'royalties.readOnlyBanner' | t:lang() }}
          </div>
        }

        <div class="vx-quick-access" data-testid="royalties-quick-access">
          <a routerLink="/royalties/pools" class="btn btn--secondary">
            {{ 'royalties.nav.pools' | t:lang() }}
          </a>
          <a routerLink="/royalties/settlements" class="btn btn--secondary">
            {{ 'royalties.nav.settlements' | t:lang() }}
          </a>
          @if (canPayout) {
            <a
              routerLink="/payouts"
              class="btn btn--primary"
              data-testid="royalties-payouts-link"
            >
              {{ 'royalties.nav.payouts' | t:lang() }}
            </a>
          } @else if (canView) {
            <a
              routerLink="/payouts"
              class="btn btn--secondary"
              data-testid="royalties-payouts-link"
            >
              {{ 'royalties.nav.payouts' | t:lang() }}
            </a>
          }
        </div>

        <details class="vx-glossary-help" data-testid="royalties-glossary">
          <summary>{{ 'royalties.glossary.title' | t:lang() }}</summary>
          <div class="vx-glossary-help__body">
            <dl class="meta">
              <dt>{{ 'royalties.term.distributableIncome' | t:lang() }}</dt>
              <dd>{{ 'royalties.term.distributableIncome.help' | t:lang() }}</dd>
              <dt>{{ 'royalties.term.streamShare' | t:lang() }}</dt>
              <dd>{{ 'royalties.term.streamShare.help' | t:lang() }}</dd>
              <dt>{{ 'royalties.term.contractPct' | t:lang() }}</dt>
              <dd>{{ 'royalties.term.contractPct.help' | t:lang() }}</dd>
              <dt>{{ 'royalties.term.settlement' | t:lang() }}</dt>
              <dd>{{ 'royalties.term.settlement.help' | t:lang() }}</dd>
              <dt>{{ 'royalties.term.simulatedPayout' | t:lang() }}</dt>
              <dd>{{ 'royalties.term.simulatedPayout.help' | t:lang() }}</dd>
            </dl>
          </div>
        </details>

        @if (loading) {
          <app-enterprise-loading-skeleton [rows]="4" />
        } @else if (error) {
          <app-enterprise-error-state [message]="error" (retry)="load()" />
        } @else if (!metrics) {
          <app-enterprise-empty-state
            [title]="'royalties.dashboard.empty' | t:lang()"
            [description]="'royalties.dashboard.emptyBody' | t:lang()"
          />
        } @else {
          <div class="vx-kpi-grid" data-testid="royalties-metrics">
            <div class="kpi-card">
              <h3>{{ 'royalties.dashboard.poolApproved' | t:lang() }}</h3>
              <p class="kpi-value">{{ metrics.distributable_pool_approved | localeMoney:'USD' }}</p>
            </div>
            <div class="kpi-card">
              <h3>{{ 'royalties.dashboard.poolClosed' | t:lang() }}</h3>
              <p class="kpi-value">{{ metrics.distributable_pool_allocated_or_closed | localeMoney:'USD' }}</p>
            </div>
            <div class="kpi-card">
              <h3>{{ 'royalties.dashboard.poolCount' | t:lang() }}</h3>
              <p class="kpi-value">{{ metrics.pool_count }}</p>
            </div>
            <div class="kpi-card">
              <h3>{{ 'royalties.dashboard.settlementGross' | t:lang() }}</h3>
              <p class="kpi-value">{{ metrics.settlement_gross_total | localeMoney:'USD' }}</p>
            </div>
            <div class="kpi-card">
              <h3>{{ 'royalties.dashboard.settlementNet' | t:lang() }}</h3>
              <p class="kpi-value">{{ metrics.settlement_net_total | localeMoney:'USD' }}</p>
            </div>
            <div class="kpi-card">
              <h3>{{ 'royalties.dashboard.settlementCount' | t:lang() }}</h3>
              <p class="kpi-value">{{ metrics.settlement_count }}</p>
            </div>
            <div class="kpi-card">
              <h3>{{ 'royalties.dashboard.payoutSimulated' | t:lang() }}</h3>
              <p class="kpi-value">{{ metrics.payout_paid_simulated_total | localeMoney:'USD' }}</p>
              <span class="vx-sim-badge">{{ 'royalties.payouts.academicBadge' | t:lang() }}</span>
            </div>
            <div class="kpi-card">
              <h3>{{ 'royalties.dashboard.payoutBatches' | t:lang() }}</h3>
              <p class="kpi-value">{{ metrics.payout_batch_count }}</p>
            </div>
          </div>
          @if (metrics.income_note) {
            <p class="muted">{{ metrics.income_note }}</p>
          }
          @if (metrics.simulated_only) {
            <p class="muted">{{ 'royalties.payout.simulatedBanner' | t:lang() }}</p>
          }
        }
      }
    </div>
  `,
})
export class RoyaltiesDashboardPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;
  private api = inject(RoyaltiesApiService);
  private orgCtx = inject(OrganizationContextService);
  private access = royaltiesAccess();

  orgId: number | null = null;
  metrics: RoyaltyMetrics | null = null;
  loading = false;
  error: string | null = null;
  readOnly = false;
  canPayout = false;
  /** View-only simulated payouts access when payout action is not granted. */
  canView = false;

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    this.readOnly = this.access.isReadOnly();
    this.canPayout = this.access.canPayout();
    this.canView = this.orgCtx.hasPermission('royalty.view');
    if (!this.orgId) return;
    this.load();
  }

  load(): void {
    if (!this.orgId) return;
    this.loading = true;
    this.error = null;
    this.api.getMetrics(this.orgId).subscribe({
      next: (m) => {
        this.metrics = m;
        this.loading = false;
      },
      error: (e) => {
        this.error = userFacingHttpError(this.i18n, e);
        this.loading = false;
      },
    });
  }
}
