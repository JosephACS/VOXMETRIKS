import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BillingApiService } from '../services/billing-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { PaymentAttempt } from '../models/billing.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { LocaleDatePipe, LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-payment-attempts',
  standalone: true,
  imports: [
    CommonModule,
    TranslatePipe,
    LocaleMoneyPipe,
    LocaleDatePipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  template: `
    <div class="vx-enterprise payment-attempts-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <app-enterprise-page-header
          [title]="'billing.paymentAttempts.title' | t:lang()"
          [subtitle]="'billing.paymentAttempts.subtitle' | t:lang()"
        />

        @if (error) {
          <app-enterprise-error-state [message]="error" />
        } @else if (!attempts.length) {
          <app-enterprise-empty-state
            [title]="'billing.paymentAttempts.emptyTitle' | t:lang()"
            [description]="'billing.paymentAttempts.emptyBody' | t:lang()"
          />
        } @else {
          <app-enterprise-data-table>
            <table class="data-table">
              <thead>
                <tr>
                  <th>{{ 'common.id' | t:lang() }}</th>
                  <th>{{ 'billing.paymentAttempts.provider' | t:lang() }}</th>
                  <th>{{ 'common.amount' | t:lang() }}</th>
                  <th>{{ 'common.status' | t:lang() }}</th>
                  <th>{{ 'billing.paymentAttempts.created' | t:lang() }}</th>
                </tr>
              </thead>
              <tbody>
                @for (a of attempts; track a.id) {
                  <tr>
                    <td>{{ a.id }}</td>
                    <td>
                      @if (a.is_mock) {
                        <span class="badge badge--mock">{{ 'common.mock' | t:lang() }}</span>
                      }
                      {{ a.provider_code }}
                    </td>
                    <td>{{ a.amount | localeMoney:a.currency }}</td>
                    <td><app-enterprise-status-badge [status]="a.status" /></td>
                    <td>{{ a.created_at | localeDate:true }}</td>
                  </tr>
                }
              </tbody>
            </table>
          </app-enterprise-data-table>
        }
      }
    </div>
  `,
})
export class PaymentAttemptsPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(BillingApiService);
  private orgCtx = inject(OrganizationContextService);
  attempts: PaymentAttempt[] = [];
  error: string | null = null;
  orgId: number | null = null;

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    if (!this.orgId) return;
    this.api.listPaymentAttempts(this.orgId!).subscribe({
      next: (res) => (this.attempts = res.items),
      error: (e) => (this.error = e.error?.message ?? this.i18n.t('common.loadFailed')),
    });
  }
}
