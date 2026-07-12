import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { BillingApiService } from '../services/billing-api.service';
import { Payment } from '../models/billing.models';

@Component({
  selector: 'app-manual-transfer',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="manual-transfer-page">
      <h1>Record Manual Transfer</h1>
      <form [formGroup]="form" (ngSubmit)="submit()">
        <div class="field">
          <label>Invoice ID</label>
          <input type="number" formControlName="invoice_id" class="input" placeholder="Invoice ID">
        </div>
        <div class="field">
          <label>Amount</label>
          <input type="number" formControlName="amount" class="input" placeholder="0.00" step="0.01">
        </div>
        <div class="field">
          <label>Currency</label>
          <input formControlName="currency" class="input" placeholder="USD" maxlength="3">
        </div>
        <div class="field">
          <label>Notes (optional)</label>
          <input formControlName="notes" class="input" placeholder="Bank reference or notes">
        </div>
        <button type="submit" class="btn btn--primary" [disabled]="form.invalid || loading">
          {{ loading ? 'Processing...' : 'Record Transfer' }}
        </button>
      </form>
      @if (result) {
        <div class="success-card">
          <p>Transfer recorded. Payment ID: {{ result.id }} | Status: {{ result.status }}</p>
        </div>
      }
      @if (error) {
        <p class="error">{{ error }}</p>
      }
    </div>
  `,
})
export class ManualTransferPage {
  private api = inject(BillingApiService);
  private fb = inject(FormBuilder);

  orgId = 1;
  loading = false;
  result: Payment | null = null;
  error: string | null = null;

  form = this.fb.group({
    invoice_id: [null, Validators.required],
    amount: [null, [Validators.required, Validators.min(0.01)]],
    currency: ['USD', [Validators.required, Validators.maxLength(3)]],
    notes: [''],
  });

  submit(): void {
    if (this.form.invalid) return;
    this.loading = true;
    this.error = null;
    this.api.createManualTransfer(this.orgId, this.form.value).subscribe({
      next: (p) => { this.result = p; this.loading = false; },
      error: (e) => { this.error = e.error?.message ?? 'Transfer failed'; this.loading = false; },
    });
  }
}
