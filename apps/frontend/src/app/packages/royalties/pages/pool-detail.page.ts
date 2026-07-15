import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { RoyaltiesApiService } from '../services/royalties.api';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { RoyaltyPool } from '../models/royalties.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { LocaleDatePipe, LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';
import { userFacingHttpError } from '../../../core/i18n/user-facing-error';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import { royaltiesAccess } from '../royalties-access';

@Component({
  selector: 'app-pool-detail',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    TranslatePipe,
    LocaleMoneyPipe,
    LocaleDatePipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  template: `
    <div class="vx-enterprise pool-detail-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <a routerLink="/royalties/pools" class="back-link">{{ 'royalties.pools.back' | t:lang() }}</a>

        @if (loading) {
          <app-enterprise-loading-skeleton [rows]="5" />
        } @else if (error && !pool) {
          <app-enterprise-error-state [message]="error" (retry)="reload()" />
        } @else if (!pool) {
          <app-enterprise-empty-state [title]="'royalties.pools.notFound' | t:lang()" />
        } @else {
          <app-enterprise-page-header [title]="pool.label || ('#' + pool.id)">
            <app-enterprise-status-badge [status]="pool.status" />
          </app-enterprise-page-header>

          <app-enterprise-section-card [title]="'royalties.term.distributableIncome' | t:lang()">
            <p class="muted">{{ 'royalties.term.distributableIncome.help' | t:lang() }}</p>
            <dl class="meta">
              <dt>{{ 'common.currency' | t:lang() }}</dt>
              <dd>{{ pool.currency }}</dd>
              <dt>{{ 'common.amount' | t:lang() }}</dt>
              <dd>{{ pool.total_amount | localeMoney:pool.currency }}</dd>
              <dt>{{ 'royalties.pools.residual' | t:lang() }}</dt>
              <dd>{{ pool.residual_amount | localeMoney:pool.currency }}</dd>
              <dt>{{ 'royalties.pools.method' | t:lang() }}</dt>
              <dd>{{ pool.attribution_method }}</dd>
              <dt>{{ 'royalties.pools.period' | t:lang() }}</dt>
              <dd>{{ pool.period_start | localeDate }} — {{ pool.period_end | localeDate }}</dd>
              <dt>{{ 'royalties.term.streamShare' | t:lang() }}</dt>
              <dd>{{ 'royalties.term.streamShare.help' | t:lang() }}</dd>
            </dl>
          </app-enterprise-section-card>

          @if (canApprove && pool.status === 'draft') {
            <button type="button" class="btn btn--primary" [disabled]="busy" (click)="approve()">
              {{ 'royalties.pools.approve' | t:lang() }}
            </button>
          }
          @if (canSettle && (pool.status === 'approved' || pool.status === 'allocated')) {
            <button type="button" class="btn btn--secondary" [disabled]="busy" (click)="settle()">
              {{ 'royalties.pools.settle' | t:lang() }}
            </button>
          }

          @if (error) {
            <app-enterprise-error-state [message]="error" />
          }
          @if (info) {
            <p class="success">{{ info }}</p>
          }
        }
      }
    </div>
  `,
})
export class PoolDetailPage implements OnInit {
  private api = inject(RoyaltiesApiService);
  private orgCtx = inject(OrganizationContextService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private i18n = inject(I18nService);
  private access = royaltiesAccess();
  readonly lang = this.i18n.lang;

  orgId: number | null = null;
  poolId = 0;
  pool: RoyaltyPool | null = null;
  loading = false;
  busy = false;
  error: string | null = null;
  info: string | null = null;
  canApprove = false;
  canSettle = false;

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    this.canApprove = this.access.canApprove();
    this.canSettle = this.access.canSettle();
    this.poolId = Number(this.route.snapshot.paramMap.get('id'));
    if (!this.orgId || !this.poolId) {
      this.error = this.i18n.t('royalties.pools.invalidId');
      return;
    }
    this.reload();
  }

  reload(): void {
    if (!this.orgId || !this.poolId) return;
    this.loading = true;
    this.error = null;
    this.api.getPool(this.orgId, this.poolId).subscribe({
      next: (p) => {
        this.pool = p;
        this.loading = false;
      },
      error: (e) => {
        this.error = userFacingHttpError(this.i18n, e);
        this.loading = false;
      },
    });
  }

  approve(): void {
    if (!this.orgId || !this.poolId || !this.canApprove) return;
    this.busy = true;
    this.error = null;
    this.api.approvePool(this.orgId, this.poolId).subscribe({
      next: (p) => {
        this.pool = p;
        this.busy = false;
        this.info = this.i18n.t('royalties.pools.approved');
      },
      error: (e) => {
        this.busy = false;
        this.error = userFacingHttpError(this.i18n, e);
      },
    });
  }

  settle(): void {
    if (!this.orgId || !this.poolId || !this.canSettle) return;
    this.busy = true;
    this.error = null;
    this.api
      .settleProRata(this.orgId, this.poolId, {
        idempotency_key: `settle-${this.poolId}-${Date.now()}`,
      })
      .subscribe({
        next: (run) => {
          this.busy = false;
          this.info = this.i18n.t('royalties.pools.settled');
          void this.router.navigate(['/royalties/settlements', run.id]);
        },
        error: (e) => {
          this.busy = false;
          this.error = userFacingHttpError(this.i18n, e);
        },
      });
  }
}
