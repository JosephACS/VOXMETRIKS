import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { BillingApiService } from '../services/billing-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { Refund } from '../models/billing.models';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
@Component({
  selector: 'app-refunds',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, TranslatePipe],
  template: `
    <div class="vx-enterprise refunds-page">
      <h1>{{ 'billing.refunds.title' | t:lang() }}</h1>
      <button class="btn btn--secondary mb-3" (click)="showForm = !showForm">
        {{ showForm ? 'Cancel' : 'New Refund' }}
      </button>
      @if (showForm) {
        <form [formGroup]="form" (ngSubmit)="submit()" class="form-card">
          <input type="number" formControlName="payment_id" placeholder="Payment ID" class="input">
          <input type="number" formControlName="amount" placeholder="Amount" step="0.01" class="input">
          <input formControlName="reason" placeholder="Reason (optional)" class="input">
          <button type="submit" class="btn btn--primary" [disabled]="form.invalid">{{ 'billing.refunds.issue' | t:lang() }}</button>
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
        <p class="empty-state">{{ 'billing.refunds.empty' | t:lang() }}</p>
      }
      @if (error) {
        <p class="error">{{ error }}</p>
      }
    </div>
  `,
})
export class RefundsPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(BillingApiService);
  private orgCtx = inject(OrganizationContextService);
  private fb = inject(FormBuilder);

  refunds: Refund[] = [];
  error: string | null = null;
  showForm = false;
  orgId: number | null = null;

  form = this.fb.group({
    payment_id: [null, Validators.required],
    amount: [null, [Validators.required, Validators.min(0.01)]],
    reason: [''],
  });

  ngOnInit(): void {
    this.orgId = this.orgCtx.activeOrganization()?.id ?? null;
    if (!this.orgId) {
      this.error = this.i18n.t('common.orgRequiredContext');
      return;
    }
    this.loadRefunds();
  }

  loadRefunds(): void {
    this.api.listRefunds(this.orgId!).subscribe({
      next: (res) => (this.refunds = res.items),
      error: (e) => (this.error = e.error?.message ?? 'Error loading refunds'),
    });
  }

  submit(): void {
    if (this.form.invalid) return;
    this.api.createRefund(this.orgId!, this.form.value).subscribe({
      next: () => { this.showForm = false; this.loadRefunds(); },
      error: (e) => (this.error = e.error?.message ?? 'Error creating refund'),
    });
  }
}
