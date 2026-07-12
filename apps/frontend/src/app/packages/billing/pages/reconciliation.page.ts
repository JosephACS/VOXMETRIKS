import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BillingApiService } from '../services/billing-api.service';
import { Payment } from '../models/billing.models';

@Component({
  selector: 'app-reconciliation',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="reconciliation-page">
      <h1>Reconciliation</h1>
      <p class="subtitle">Settle and reconcile payments from bank statements.</p>
      @if (payments.length) {
        <table class="data-table">
          <thead>
            <tr>
              <th>ID</th><th>Provider</th><th>Amount</th><th>Status</th><th>Actions</th>
            </tr>
          </thead>
          <tbody>
            @for (p of payments; track p.id) {
              <tr>
                <td>{{ p.id }}</td>
                <td>{{ p.provider_code }}</td>
                <td>{{ p.amount | number:'1.2-2' }} {{ p.currency }}</td>
                <td><span class="badge" [class]="'badge--' + p.status">{{ p.status }}</span></td>
                <td>
                  @if (p.status === 'recorded') {
                    <button class="btn btn--sm"
                            (click)="settle(p.id)">Settle</button>
                  }
                  @if (p.status === 'settled') {
                    <button class="btn btn--sm btn--success"
                            (click)="reconcile(p.id)">Reconcile</button>
                  }
                </td>
              </tr>
            }
          </tbody>
        </table>
      } @else {
        <p class="empty-state">No payments to reconcile.</p>
      }
      @if (error) {
        <p class="error">{{ error }}</p>
      }
    </div>
  `,
})
export class ReconciliationPage implements OnInit {
  private api = inject(BillingApiService);
  payments: Payment[] = [];
  error: string | null = null;
  orgId = 1;

  ngOnInit(): void {
    this.loadPayments();
  }

  loadPayments(): void {
    this.api.listPayments(this.orgId).subscribe({
      next: (res) => (this.payments = res.items),
      error: (e) => (this.error = e.error?.message ?? 'Error loading payments'),
    });
  }

  settle(id: number): void {
    this.api.settlePayment(this.orgId, id).subscribe({
      next: () => this.loadPayments(),
      error: (e) => (this.error = e.error?.message ?? 'Error settling payment'),
    });
  }

  reconcile(id: number): void {
    this.api.reconcilePayment(this.orgId, id).subscribe({
      next: () => this.loadPayments(),
      error: (e) => (this.error = e.error?.message ?? 'Error reconciling payment'),
    });
  }
}
