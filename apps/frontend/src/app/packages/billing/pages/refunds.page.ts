import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { BillingApiService } from '../services/billing-api.service';
import { Refund } from '../models/billing.models';

@Component({
  selector: 'app-refunds',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="refunds-page">
      <h1>Refunds</h1>
      <button class="btn btn--secondary mb-3" (click)="showForm = !showForm">
        {{ showForm ? 'Cancel' : 'New Refund' }}
      </button>
      @if (showForm) {
        <form [formGroup]="form" (ngSubmit)="submit()" class="form-card">
          <input type="number" formControlName="payment_id" placeholder="Payment ID" class="input">
          <input type="number" formControlName="amount" placeholder="Amount" step="0.01" class="input">
          <input formControlName="reason" placeholder="Reason (optional)" class="input">
          <button type="submit" class="btn btn--primary" [disabled]="form.invalid">Issue Refund</button>
        </form>
      }
      @if (refunds.length) {
        <table class="data-table">
          <thead>
            <tr><th>ID</th><th>Payment</th><th>Amount</th><th>Status</th><th>Processed</th></tr>
          </thead>
          <tbody>
            @for (r of refunds; track r.id) {
              <tr>
                <td>{{ r.id }}</td><td>{{ r.payment_id }}</td>
                <td>{{ r.amount | number:'1.2-2' }} {{ r.currency }}</td>
                <td><span class="badge" [class]="'badge--' + r.status">{{ r.status }}</span></td>
                <td>{{ r.processed_at | date:'short' }}</td>
              </tr>
            }
          </tbody>
        </table>
      } @else {
        <p class="empty-state">No refunds issued.</p>
      }
      @if (error) {
        <p class="error">{{ error }}</p>
      }
    </div>
  `,
})
export class RefundsPage implements OnInit {
  private api = inject(BillingApiService);
  private fb = inject(FormBuilder);

  refunds: Refund[] = [];
  error: string | null = null;
  showForm = false;
  orgId = 1;

  form = this.fb.group({
    payment_id: [null, Validators.required],
    amount: [null, [Validators.required, Validators.min(0.01)]],
    reason: [''],
  });

  ngOnInit(): void {
    this.loadRefunds();
  }

  loadRefunds(): void {
    this.api.listRefunds(this.orgId).subscribe({
      next: (res) => (this.refunds = res.items),
      error: (e) => (this.error = e.error?.message ?? 'Error loading refunds'),
    });
  }

  submit(): void {
    if (this.form.invalid) return;
    this.api.createRefund(this.orgId, this.form.value).subscribe({
      next: () => { this.showForm = false; this.loadRefunds(); },
      error: (e) => (this.error = e.error?.message ?? 'Error creating refund'),
    });
  }
}
