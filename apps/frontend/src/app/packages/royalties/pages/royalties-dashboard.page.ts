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
        >
          <a routerLink="/royalties/pools" class="btn btn--secondary">
            {{ 'royalties.nav.pools' | t:lang() }}
          </a>
          <a routerLink="/royalties/settlements" class="btn btn--secondary">
            {{ 'royalties.nav.settlements' | t:lang() }}
          </a>
        </app-enterprise-page-header>

        @if (readOnly) {
          <div class="alert alert--warn" role="status">
            {{ 'royalties.readOnlyBanner' | t:lang() }}
          </div>
        }

        <app-enterprise-section-card [title]="'royalties.glossary.title' | t:lang()">
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
        </app-enterprise-section-card>

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
          <app-enterprise-section-card [title]="'royalties.dashboard.metrics' | t:lang()">
            <p class="muted">{{ metrics.income_note }}</p>
            <dl class="meta">
              <dt>{{ 'royalties.dashboard.poolApproved' | t:lang() }}</dt>
              <dd>{{ metrics.distributable_pool_approved | localeMoney:'USD' }}</dd>
              <dt>{{ 'royalties.dashboard.poolClosed' | t:lang() }}</dt>
              <dd>{{ metrics.distributable_pool_allocated_or_closed | localeMoney:'USD' }}</dd>
              <dt>{{ 'royalties.dashboard.poolCount' | t:lang() }}</dt>
              <dd>{{ metrics.pool_count }}</dd>
              <dt>{{ 'royalties.dashboard.settlementGross' | t:lang() }}</dt>
              <dd>{{ metrics.settlement_gross_total | localeMoney:'USD' }}</dd>
              <dt>{{ 'royalties.dashboard.settlementNet' | t:lang() }}</dt>
              <dd>{{ metrics.settlement_net_total | localeMoney:'USD' }}</dd>
              <dt>{{ 'royalties.dashboard.settlementCount' | t:lang() }}</dt>
              <dd>{{ metrics.settlement_count }}</dd>
              <dt>{{ 'royalties.dashboard.payoutSimulated' | t:lang() }}</dt>
              <dd>{{ metrics.payout_paid_simulated_total | localeMoney:'USD' }}</dd>
              <dt>{{ 'royalties.dashboard.payoutBatches' | t:lang() }}</dt>
              <dd>{{ metrics.payout_batch_count }}</dd>
            </dl>
            @if (metrics.simulated_only) {
              <p class="muted">{{ 'royalties.payout.simulatedBanner' | t:lang() }}</p>
            }
          </app-enterprise-section-card>
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

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    this.readOnly = this.access.isReadOnly();
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
