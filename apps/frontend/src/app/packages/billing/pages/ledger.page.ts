import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BillingApiService } from '../services/billing-api.service';
import { LedgerEntry } from '../models/billing.models';

@Component({
  selector: 'app-ledger',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="ledger-page">
      <h1>Billing Ledger</h1>
      <p class="subtitle read-only-notice">Read-only — append-only financial record.</p>
      <div class="filter-bar">
        <select (change)="onTypeFilter($event)" class="select">
          <option value="">All entry types</option>
          <option value="invoice_issued">Invoice Issued</option>
          <option value="payment_received">Payment Received</option>
          <option value="refund_issued">Refund Issued</option>
          <option value="credit_note_applied">Credit Note Applied</option>
          <option value="adjustment">Adjustment</option>
        </select>
      </div>
      @if (entries.length) {
        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th><th>Type</th><th>Ref</th><th>Amount</th><th>Description</th><th>Date</th>
            </tr>
          </thead>
          <tbody>
            @for (e of entries; track e.id) {
              <tr>
                <td>{{ e.id }}</td>
                <td><span class="badge badge--neutral">{{ e.entry_type }}</span></td>
                <td>{{ e.reference_type }} #{{ e.reference_id }}</td>
                <td [class]="e.amount < 0 ? 'amount-negative' : 'amount-positive'">
                  {{ e.amount | number:'1.2-4' }} {{ e.currency }}
                </td>
                <td>{{ e.description }}</td>
                <td>{{ e.created_at | date:'short' }}</td>
              </tr>
            }
          </tbody>
        </table>
      } @else {
        <p class="empty-state">No ledger entries.</p>
      }
      @if (error) {
        <p class="error">{{ error }}</p>
      }
    </div>
  `,
})
export class LedgerPage implements OnInit {
  private api = inject(BillingApiService);
  entries: LedgerEntry[] = [];
  error: string | null = null;
  typeFilter = '';
  orgId = 1;

  ngOnInit(): void {
    this.loadLedger();
  }

  loadLedger(): void {
    this.api.getLedger(this.orgId, { entry_type: this.typeFilter || undefined }).subscribe({
      next: (res) => (this.entries = res.items),
      error: (e) => (this.error = e.error?.message ?? 'Error loading ledger'),
    });
  }

  onTypeFilter(event: Event): void {
    this.typeFilter = (event.target as HTMLSelectElement).value;
    this.loadLedger();
  }
}
