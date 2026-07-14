import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BillingApiService } from '../services/billing-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { LedgerEntry } from '../models/billing.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { LocaleDatePipe, LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-ledger',
  standalone: true,
  imports: [CommonModule, TranslatePipe, LocaleMoneyPipe, LocaleDatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise ledger-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <app-enterprise-page-header
          [title]="'billing.ledger.title' | t:lang()"
          [subtitle]="'billing.ledger.subtitle' | t:lang()"
        />

        @if (error) {
          <app-enterprise-error-state [message]="error" (retry)="loadLedger()" />
        }

        <app-enterprise-data-table
          [empty]="!entries.length && !error"
          [emptyTitle]="'billing.ledger.emptyTitle' | t:lang()"
          [emptyDescription]="'billing.ledger.emptyBody' | t:lang()"
        >
          <div toolbar>
            <select (change)="onTypeFilter($event)" class="select">
              <option value="">{{ 'billing.ledger.allTypes' | t:lang() }}</option>
              <option value="invoice_issued">{{ 'billing.ledger.type.invoice_issued' | t:lang() }}</option>
              <option value="payment_received">{{ 'billing.ledger.type.payment_received' | t:lang() }}</option>
              <option value="refund_issued">{{ 'billing.ledger.type.refund_issued' | t:lang() }}</option>
              <option value="credit_note_applied">{{ 'billing.ledger.type.credit_note_applied' | t:lang() }}</option>
              <option value="adjustment">{{ 'billing.ledger.type.adjustment' | t:lang() }}</option>
            </select>
          </div>
          <table class="data-table">
            <thead>
              <tr>
                <th>{{ 'common.id' | t:lang() }}</th>
                <th>{{ 'common.type' | t:lang() }}</th>
                <th>{{ 'billing.ledger.reference' | t:lang() }}</th>
                <th>{{ 'common.amount' | t:lang() }}</th>
                <th>{{ 'common.description' | t:lang() }}</th>
                <th>{{ 'common.date' | t:lang() }}</th>
              </tr>
            </thead>
            <tbody>
              @for (e of entries; track e.id) {
                <tr>
                  <td>{{ e.id }}</td>
                  <td>
                    <app-enterprise-status-badge
                      status="neutral"
                      [label]="entryTypeLabel(e.entry_type)"
                    />
                  </td>
                  <td>{{ e.reference_type }} #{{ e.reference_id }}</td>
                  <td [class]="e.amount < 0 ? 'amount-negative' : 'amount-positive'">
                    {{ e.amount | localeMoney:e.currency }}
                  </td>
                  <td>{{ e.description }}</td>
                  <td>{{ e.created_at | localeDate:true }}</td>
                </tr>
              }
            </tbody>
          </table>
        </app-enterprise-data-table>
      }
    </div>
  `,
})
export class LedgerPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(BillingApiService);
  private orgCtx = inject(OrganizationContextService);
  entries: LedgerEntry[] = [];
  error: string | null = null;
  typeFilter = '';
  orgId: number | null = null;

  ngOnInit(): void {
    this.orgId = this.orgCtx.activeOrganization()?.id ?? null;
    if (!this.orgId) return;
    this.loadLedger();
  }

  entryTypeLabel(type: string): string {
    const key = `billing.ledger.type.${type}`;
    const t = this.i18n.t(key);
    return t === key ? type : t;
  }

  loadLedger(): void {
    this.api.getLedger(this.orgId!, { entry_type: this.typeFilter || undefined }).subscribe({
      next: (res) => (this.entries = res.items),
      error: (e) => (this.error = e.error?.message ?? 'Error loading ledger'),
    });
  }

  onTypeFilter(event: Event): void {
    this.typeFilter = (event.target as HTMLSelectElement).value;
    this.loadLedger();
  }
}
