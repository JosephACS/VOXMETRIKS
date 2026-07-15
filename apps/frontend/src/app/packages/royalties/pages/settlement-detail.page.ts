import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { RoyaltiesApiService } from '../services/royalties.api';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { RoyaltySettlement } from '../models/royalties.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';
import { userFacingHttpError } from '../../../core/i18n/user-facing-error';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import { royaltiesAccess } from '../royalties-access';

@Component({
  selector: 'app-settlement-detail',
  standalone: true,
  imports: [CommonModule, RouterModule, TranslatePipe, LocaleMoneyPipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise settlement-detail-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <a routerLink="/royalties/settlements" class="back-link">
          {{ 'royalties.settlements.back' | t:lang() }}
        </a>

        @if (loading) {
          <app-enterprise-loading-skeleton [rows]="5" />
        } @else if (error && !run) {
          <app-enterprise-error-state [message]="error" (retry)="reload()" />
        } @else if (!run) {
          <app-enterprise-empty-state [title]="'royalties.settlements.notFound' | t:lang()" />
        } @else {
          <app-enterprise-page-header [title]="('royalties.settlements.detail' | t:lang()) + ' #' + run.id">
            <app-enterprise-status-badge [status]="run.status" />
          </app-enterprise-page-header>

          <app-enterprise-section-card [title]="'royalties.term.settlement' | t:lang()">
            <p class="muted">{{ 'royalties.term.settlement.help' | t:lang() }}</p>
            <p class="muted">{{ 'royalties.term.contractPct.help' | t:lang() }}</p>
            <dl class="meta">
              <dt>{{ 'royalties.settlements.pool' | t:lang() }}</dt>
              <dd>
                <a [routerLink]="['/royalties/pools', run.pool_id]">#{{ run.pool_id }}</a>
              </dd>
              <dt>{{ 'royalties.settlements.gross' | t:lang() }}</dt>
              <dd>{{ run.gross_total | localeMoney:run.currency }}</dd>
              <dt>{{ 'royalties.settlements.adjustments' | t:lang() }}</dt>
              <dd>{{ run.adjustment_total | localeMoney:run.currency }}</dd>
              <dt>{{ 'royalties.settlements.net' | t:lang() }}</dt>
              <dd>{{ run.net_total | localeMoney:run.currency }}</dd>
            </dl>
          </app-enterprise-section-card>

          @if (run.party_allocations?.length) {
            <app-enterprise-section-card [title]="'royalties.settlements.parties' | t:lang()">
              <app-enterprise-data-table>
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>{{ 'common.name' | t:lang() }}</th>
                      <th>{{ 'common.amount' | t:lang() }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    @for (p of run.party_allocations; track $index) {
                      <tr>
                        <td>{{ p['party_name'] || p['party_id'] }}</td>
                        <td>{{ (p['net_amount'] ?? p['gross_amount']) | localeMoney:run.currency }}</td>
                      </tr>
                    }
                  </tbody>
                </table>
              </app-enterprise-data-table>
            </app-enterprise-section-card>
          }

          <div class="actions" style="display:flex;flex-wrap:wrap;gap:.5rem;margin-top:1rem">
            @if (canSettle && run.status === 'calculated') {
              <button type="button" class="btn btn--secondary" [disabled]="busy" (click)="splits()">
                {{ 'royalties.settlements.contractSplits' | t:lang() }}
              </button>
              <button type="button" class="btn btn--secondary" [disabled]="busy" (click)="statements()">
                {{ 'royalties.settlements.genStatements' | t:lang() }}
              </button>
              <button type="button" class="btn btn--secondary" [disabled]="busy" (click)="submit()">
                {{ 'royalties.settlements.submit' | t:lang() }}
              </button>
            }
            @if (canApprove && run.status === 'submitted') {
              <button type="button" class="btn btn--primary" [disabled]="busy" (click)="approve()">
                {{ 'royalties.settlements.approve' | t:lang() }}
              </button>
              <button type="button" class="btn btn--danger" [disabled]="busy" (click)="reject()">
                {{ 'royalties.settlements.reject' | t:lang() }}
              </button>
            }
            @if (canApprove && run.status === 'approved') {
              <button type="button" class="btn btn--primary" [disabled]="busy" (click)="finalize()">
                {{ 'royalties.settlements.finalize' | t:lang() }}
              </button>
            }
            @if (canPayout && (run.status === 'finalized' || run.status === 'approved')) {
              <button type="button" class="btn btn--secondary" [disabled]="busy" (click)="createPayout()">
                {{ 'royalties.settlements.createPayout' | t:lang() }}
              </button>
            }
          </div>

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
export class SettlementDetailPage implements OnInit {
  private api = inject(RoyaltiesApiService);
  private orgCtx = inject(OrganizationContextService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private i18n = inject(I18nService);
  private access = royaltiesAccess();
  readonly lang = this.i18n.lang;

  orgId: number | null = null;
  settlementId = 0;
  run: RoyaltySettlement | null = null;
  loading = false;
  busy = false;
  error: string | null = null;
  info: string | null = null;
  canApprove = false;
  canSettle = false;
  canPayout = false;

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    this.canApprove = this.access.canApprove();
    this.canSettle = this.access.canSettle();
    this.canPayout = this.access.canPayout();
    this.settlementId = Number(this.route.snapshot.paramMap.get('id'));
    if (!this.orgId || !this.settlementId) {
      this.error = this.i18n.t('royalties.settlements.invalidId');
      return;
    }
    this.reload();
  }

  reload(): void {
    if (!this.orgId || !this.settlementId) return;
    this.loading = true;
    this.error = null;
    this.api.getSettlement(this.orgId, this.settlementId).subscribe({
      next: (r) => {
        this.run = r;
        this.loading = false;
      },
      error: (e) => {
        this.error = userFacingHttpError(this.i18n, e);
        this.loading = false;
      },
    });
  }

  private act(fn: () => void): void {
    this.busy = true;
    this.error = null;
    fn();
  }

  splits(): void {
    if (!this.orgId || !this.canSettle) return;
    this.act(() =>
      this.api.contractSplits(this.orgId!, this.settlementId).subscribe({
        next: (r) => {
          this.run = r;
          this.busy = false;
          this.info = this.i18n.t('royalties.settlements.splitsDone');
        },
        error: (e) => {
          this.busy = false;
          this.error = userFacingHttpError(this.i18n, e);
        },
      }),
    );
  }

  statements(): void {
    if (!this.orgId || !this.canSettle) return;
    this.act(() =>
      this.api.generateStatements(this.orgId!, this.settlementId).subscribe({
        next: () => {
          this.busy = false;
          this.info = this.i18n.t('royalties.settlements.statementsDone');
        },
        error: (e) => {
          this.busy = false;
          this.error = userFacingHttpError(this.i18n, e);
        },
      }),
    );
  }

  submit(): void {
    if (!this.orgId || !this.canSettle) return;
    this.act(() =>
      this.api.submitSettlement(this.orgId!, this.settlementId).subscribe({
        next: (r) => {
          this.run = r;
          this.busy = false;
          this.info = this.i18n.t('royalties.settlements.submitted');
        },
        error: (e) => {
          this.busy = false;
          this.error = userFacingHttpError(this.i18n, e);
        },
      }),
    );
  }

  approve(): void {
    if (!this.orgId || !this.canApprove) return;
    this.act(() =>
      this.api.approveSettlement(this.orgId!, this.settlementId).subscribe({
        next: (r) => {
          this.run = r;
          this.busy = false;
          this.info = this.i18n.t('royalties.settlements.approved');
        },
        error: (e) => {
          this.busy = false;
          this.error = userFacingHttpError(this.i18n, e);
        },
      }),
    );
  }

  reject(): void {
    if (!this.orgId || !this.canApprove) return;
    this.act(() =>
      this.api.rejectSettlement(this.orgId!, this.settlementId).subscribe({
        next: (r) => {
          this.run = r;
          this.busy = false;
          this.info = this.i18n.t('royalties.settlements.rejected');
        },
        error: (e) => {
          this.busy = false;
          this.error = userFacingHttpError(this.i18n, e);
        },
      }),
    );
  }

  finalize(): void {
    if (!this.orgId || !this.canApprove) return;
    this.act(() =>
      this.api.finalizeSettlement(this.orgId!, this.settlementId).subscribe({
        next: (r) => {
          this.run = r;
          this.busy = false;
          this.info = this.i18n.t('royalties.settlements.finalized');
        },
        error: (e) => {
          this.busy = false;
          this.error = userFacingHttpError(this.i18n, e);
        },
      }),
    );
  }

  createPayout(): void {
    if (!this.orgId || !this.canPayout) return;
    this.act(() =>
      this.api
        .createPayoutBatch(this.orgId!, this.settlementId, {
          idempotency_key: `payout-${this.settlementId}-${Date.now()}`,
        })
        .subscribe({
          next: (batch) => {
            this.busy = false;
            void this.router.navigate(['/payouts', batch.id]);
          },
          error: (e) => {
            this.busy = false;
            this.error = userFacingHttpError(this.i18n, e);
          },
        }),
    );
  }
}
