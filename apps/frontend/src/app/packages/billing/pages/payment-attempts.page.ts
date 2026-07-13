import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BillingApiService } from '../services/billing-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { PaymentAttempt } from '../models/billing.models';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
@Component({
  selector: 'app-payment-attempts',
  standalone: true,
  imports: [CommonModule, TranslatePipe],
  template: `
    <div class="payment-attempts-page">
      <h1>{{ 'billing.paymentAttempts.title' | t:lang() }}</h1>
      @if (attempts.length) {
        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th><th>Provider</th><th>Amount</th><th>Status</th><th>Created</th>
            </tr>
          </thead>
          <tbody>
            @for (a of attempts; track a.id) {
              <tr>
                <td>{{ a.id }}</td>
                <td>
                  @if (a.is_mock) {
                    <span class="badge badge--mock">[MOCK]</span>
                  }
                  {{ a.provider_code }}
                </td>
                <td>{{ a.amount | number:'1.2-2' }} {{ a.currency }}</td>
                <td><span class="badge" [class]="'badge--' + a.status">{{ a.status }}</span></td>
                <td>{{ a.created_at | date:'short' }}</td>
              </tr>
            }
          </tbody>
        </table>
      } @else {
        <p class="empty-state">{{ 'billing.paymentAttempts.empty' | t:lang() }}</p>
      }
      @if (error) {
        <p class="error">{{ error }}</p>
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
    this.orgId = this.orgCtx.activeOrganization()?.id ?? null;
    if (!this.orgId) {
      this.error = this.i18n.t('common.orgRequiredContext');
      return;
    }
    this.api.listPaymentAttempts(this.orgId!).subscribe({
      next: (res) => (this.attempts = res.items),
      error: (e) => (this.error = e.error?.message ?? 'Error loading payment attempts'),
    });
  }
}
