import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { BillingApiService } from '../services/billing-api.service';
import { PaymentAttempt } from '../models/billing.models';

@Component({
  selector: 'app-payment-attempts',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="payment-attempts-page">
      <h1>Payment Attempts</h1>
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
        <p class="empty-state">No payment attempts found.</p>
      }
      @if (error) {
        <p class="error">{{ error }}</p>
      }
    </div>
  `,
})
export class PaymentAttemptsPage implements OnInit {
  private api = inject(BillingApiService);
  attempts: PaymentAttempt[] = [];
  error: string | null = null;
  orgId = 1;

  ngOnInit(): void {
    this.api.listPaymentAttempts(this.orgId).subscribe({
      next: (res) => (this.attempts = res.items),
      error: (e) => (this.error = e.error?.message ?? 'Error loading payment attempts'),
    });
  }
}
