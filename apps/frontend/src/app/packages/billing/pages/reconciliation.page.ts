import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BillingApiService } from '../services/billing-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { Payment } from '../models/billing.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-reconciliation',
  standalone: true,
  imports: [
    CommonModule,
    TranslatePipe,
    LocaleMoneyPipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  template: `
    <div class="vx-enterprise reconciliation-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <app-enterprise-page-header
          [title]="'billing.reconciliation.title' | t:lang()"
          [subtitle]="'billing.reconciliation.subtitle' | t:lang()"
        />

        @if (error) {
          <app-enterprise-error-state [message]="error" (retry)="loadPayments()" />
        } @else if (!payments.length) {
          <app-enterprise-empty-state
            [title]="'billing.reconciliation.emptyTitle' | t:lang()"
            [description]="'billing.reconciliation.emptyBody' | t:lang()"
          />
        } @else {
          <app-enterprise-data-table>
            <table class="data-table">
              <thead>
                <tr>
                  <th>{{ 'common.id' | t:lang() }}</th>
                  <th>{{ 'billing.reconciliation.provider' | t:lang() }}</th>
                  <th>{{ 'common.amount' | t:lang() }}</th>
                  <th>{{ 'common.status' | t:lang() }}</th>
                  <th>{{ 'common.actions' | t:lang() }}</th>
                </tr>
              </thead>
              <tbody>
                @for (p of payments; track p.id) {
                  <tr>
                    <td>{{ p.id }}</td>
                    <td>{{ p.provider_code }}</td>
                    <td>{{ p.amount | localeMoney:p.currency }}</td>
                    <td><app-enterprise-status-badge [status]="p.status" /></td>
                    <td>
                      @if (p.status === 'recorded') {
                        <button type="button" class="btn btn--sm" (click)="settle(p.id)">
                          {{ 'billing.reconciliation.settle' | t:lang() }}
                        </button>
                      }
                      @if (p.status === 'settled') {
                        <button type="button" class="btn btn--sm btn--success" (click)="reconcile(p.id)">
                          {{ 'billing.reconciliation.reconcile' | t:lang() }}
                        </button>
                      }
                    </td>
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
export class ReconciliationPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(BillingApiService);
  private orgCtx = inject(OrganizationContextService);
  payments: Payment[] = [];
  error: string | null = null;
  orgId: number | null = null;

  ngOnInit(): void {
    this.orgId = this.orgCtx.activeOrganization()?.id ?? null;
    if (!this.orgId) return;
    this.loadPayments();
  }

  loadPayments(): void {
    this.api.listPayments(this.orgId!).subscribe({
      next: (res) => (this.payments = res.items),
      error: (e) => (this.error = e.error?.message ?? 'Error loading payments'),
    });
  }

  settle(id: number): void {
    this.api.settlePayment(this.orgId!, id).subscribe({
      next: () => this.loadPayments(),
      error: (e) => (this.error = e.error?.message ?? 'Error settling payment'),
    });
  }

  reconcile(id: number): void {
    this.api.reconcilePayment(this.orgId!, id).subscribe({
      next: () => this.loadPayments(),
      error: (e) => (this.error = e.error?.message ?? 'Error reconciling payment'),
    });
  }
}
