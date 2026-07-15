import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { RoyaltiesApiService } from '../services/royalties.api';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { PayoutBatch } from '../models/royalties.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';
import { userFacingHttpError } from '../../../core/i18n/user-facing-error';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import { royaltiesAccess } from '../royalties-access';

@Component({
  selector: 'app-payout-detail',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    FormsModule,
    TranslatePipe,
    LocaleMoneyPipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  template: `
    <div class="vx-enterprise payout-detail-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <div class="alert alert--warn" role="status">
          {{ 'royalties.payout.simulatedBanner' | t:lang() }}
        </div>

        <a routerLink="/payouts" class="back-link">{{ 'royalties.payouts.back' | t:lang() }}</a>

        @if (loading) {
          <app-enterprise-loading-skeleton [rows]="5" />
        } @else if (error && !batch) {
          <app-enterprise-error-state [message]="error" (retry)="reload()" />
        } @else if (!batch) {
          <app-enterprise-empty-state [title]="'royalties.payouts.notFound' | t:lang()" />
        } @else {
          <app-enterprise-page-header [title]="('royalties.payouts.detail' | t:lang()) + ' #' + batch.id">
            <app-enterprise-status-badge [status]="batch.status" />
          </app-enterprise-page-header>

          <app-enterprise-section-card [title]="'royalties.term.simulatedPayout' | t:lang()">
            <p class="muted">{{ 'royalties.term.simulatedPayout.help' | t:lang() }}</p>
            <dl class="meta">
              <dt>{{ 'royalties.statements.settlement' | t:lang() }}</dt>
              <dd>
                <a [routerLink]="['/royalties/settlements', batch.settlement_run_id]">
                  #{{ batch.settlement_run_id }}
                </a>
              </dd>
              <dt>{{ 'common.amount' | t:lang() }}</dt>
              <dd>{{ batch.total_amount | localeMoney:batch.currency }}</dd>
              <dt>{{ 'royalties.payouts.simulatedOnly' | t:lang() }}</dt>
              <dd>{{ batch.simulated_only ? ('common.yes' | t:lang()) : ('common.no' | t:lang()) }}</dd>
            </dl>
          </app-enterprise-section-card>

          @if (batch.instructions?.length) {
            <app-enterprise-section-card [title]="'royalties.payouts.instructions' | t:lang()">
              <app-enterprise-data-table>
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>{{ 'common.id' | t:lang() }}</th>
                      <th>{{ 'common.amount' | t:lang() }}</th>
                      <th>{{ 'common.status' | t:lang() }}</th>
                      <th>{{ 'common.actions' | t:lang() }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    @for (ins of batch.instructions; track $index) {
                      <tr>
                        <td>#{{ ins['id'] }}</td>
                        <td>{{ ins['amount'] | localeMoney:batch.currency }}</td>
                        <td><app-enterprise-status-badge [status]="'' + ins['status']" /></td>
                        <td>
                          @if (canPayout && ins['status'] === 'failed') {
                            <button
                              type="button"
                              class="btn btn--secondary"
                              [disabled]="busy"
                              (click)="retry(+(ins['id'] || 0))"
                            >
                              {{ 'royalties.payouts.retry' | t:lang() }}
                            </button>
                          }
                        </td>
                      </tr>
                    }
                  </tbody>
                </table>
              </app-enterprise-data-table>
            </app-enterprise-section-card>
          }

          @if (canPayout) {
            <div class="form-grid" style="margin-top:1rem">
              <app-enterprise-form-field [label]="'royalties.payouts.scenario' | t:lang()">
                <select class="select" [(ngModel)]="scenario">
                  <option value="succeed">succeed</option>
                  <option value="processing">processing</option>
                  <option value="failed">failed</option>
                  <option value="invalid_destination">invalid_destination</option>
                  <option value="duplicate_request">duplicate_request</option>
                  <option value="reversed">reversed</option>
                </select>
              </app-enterprise-form-field>
            </div>
            <div class="actions" style="display:flex;flex-wrap:wrap;gap:.5rem">
              @if (batch.status === 'created' || batch.status === 'processing') {
                <button type="button" class="btn btn--primary" [disabled]="busy" (click)="simulate()">
                  {{ 'royalties.payouts.simulate' | t:lang() }}
                </button>
              }
              @if (batch.status === 'paid' || batch.status === 'partial' || batch.status === 'failed') {
                <button type="button" class="btn btn--danger" [disabled]="busy" (click)="reverse()">
                  {{ 'royalties.payouts.reverse' | t:lang() }}
                </button>
              }
            </div>
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
export class PayoutDetailPage implements OnInit {
  private api = inject(RoyaltiesApiService);
  private orgCtx = inject(OrganizationContextService);
  private route = inject(ActivatedRoute);
  private i18n = inject(I18nService);
  private access = royaltiesAccess();
  readonly lang = this.i18n.lang;

  orgId: number | null = null;
  batchId = 0;
  batch: PayoutBatch | null = null;
  loading = false;
  busy = false;
  error: string | null = null;
  info: string | null = null;
  canPayout = false;
  scenario = 'succeed';

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    this.canPayout = this.access.canPayout();
    this.batchId = Number(this.route.snapshot.paramMap.get('id'));
    if (!this.orgId || !this.batchId) {
      this.error = this.i18n.t('royalties.payouts.invalidId');
      return;
    }
    this.reload();
  }

  reload(): void {
    if (!this.orgId || !this.batchId) return;
    this.loading = true;
    this.error = null;
    this.api.getPayoutBatch(this.orgId, this.batchId).subscribe({
      next: (b) => {
        this.batch = b;
        this.loading = false;
      },
      error: (e) => {
        this.error = userFacingHttpError(this.i18n, e);
        this.loading = false;
      },
    });
  }

  simulate(): void {
    if (!this.orgId || !this.canPayout) return;
    this.busy = true;
    this.error = null;
    this.api.simulatePayouts(this.orgId, this.batchId, this.scenario).subscribe({
      next: (b) => {
        this.batch = b;
        this.busy = false;
        this.info = this.i18n.t('royalties.payouts.simulated');
      },
      error: (e) => {
        this.busy = false;
        this.error = userFacingHttpError(this.i18n, e);
      },
    });
  }

  retry(instructionId: number): void {
    if (!this.orgId || !this.canPayout) return;
    this.busy = true;
    this.error = null;
    this.api.retryPayout(this.orgId, instructionId, this.scenario).subscribe({
      next: (b) => {
        this.batch = b;
        this.busy = false;
        this.info = this.i18n.t('royalties.payouts.retried');
      },
      error: (e) => {
        this.busy = false;
        this.error = userFacingHttpError(this.i18n, e);
      },
    });
  }

  reverse(): void {
    if (!this.orgId || !this.canPayout) return;
    this.busy = true;
    this.error = null;
    this.api.reversePayout(this.orgId, this.batchId).subscribe({
      next: (b) => {
        this.batch = b;
        this.busy = false;
        this.info = this.i18n.t('royalties.payouts.reversed');
      },
      error: (e) => {
        this.busy = false;
        this.error = userFacingHttpError(this.i18n, e);
      },
    });
  }
}
