import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { BillingApiService } from '../services/billing-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { CreditNote } from '../models/billing.models';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { StatusLabelPipe } from '../../../shared/pipes/status-label.pipe';
import { LocaleDatePipe, LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';

@Component({
  selector: 'app-credit-notes',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, TranslatePipe, StatusLabelPipe, LocaleMoneyPipe, LocaleDatePipe],
  template: `
    <div class="credit-notes-page">
      <h1>{{ 'billing.creditNotes.title' | t:lang() }}</h1>
      <button class="btn btn--secondary mb-3" (click)="showForm = !showForm">
        {{ showForm ? 'Cancel' : 'New Credit Note' }}
      </button>
      @if (showForm) {
        <form [formGroup]="form" (ngSubmit)="submit()" class="form-card">
          <input type="number" formControlName="invoice_id" placeholder="Invoice ID" class="input">
          <input type="number" formControlName="amount" placeholder="Amount" step="0.01" class="input">
          <input formControlName="reason" placeholder="Reason" class="input">
          <button type="submit" class="btn btn--primary" [disabled]="form.invalid">{{ 'billing.creditNotes.create' | t:lang() }}</button>
        </form>
      }
      @if (creditNotes.length) {
        <table class="data-table">
          <thead>
            <tr><th>Number</th><th>Invoice</th><th>Amount</th><th>Status</th><th>Actions</th></tr>
          </thead>
          <tbody>
            @for (cn of creditNotes; track cn.id) {
              <tr>
                <td>{{ cn.credit_note_number }}</td>
                <td>{{ cn.invoice_id }}</td>
                <td>{{ cn.amount | number:'1.2-2' }} {{ cn.currency }}</td>
                <td><span class="badge" [class]="'badge--' + cn.status">{{ cn.status }}</span></td>
                <td>
                  @if (cn.status === 'issued') {
                    <button class="btn btn--sm"
                            (click)="apply(cn.id)">Apply</button>
                  }
                </td>
              </tr>
            }
          </tbody>
        </table>
      } @else {
        <p class="empty-state">No credit notes.</p>
      }
      @if (error) {
        <p class="error">{{ error }}</p>
      }
    </div>
  `,
})
export class CreditNotesPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(BillingApiService);
  private orgCtx = inject(OrganizationContextService);
  private fb = inject(FormBuilder);

  creditNotes: CreditNote[] = [];
  error: string | null = null;
  showForm = false;
  orgId: number | null = null;

  form = this.fb.group({
    invoice_id: [null, Validators.required],
    amount: [null, [Validators.required, Validators.min(0.01)]],
    reason: [''],
  });

  ngOnInit(): void {
    this.orgId = this.orgCtx.activeOrganization()?.id ?? null;
    if (!this.orgId) {
      this.error = this.i18n.t('common.orgRequiredContext');
      return;
    }
    this.loadCreditNotes();
  }

  loadCreditNotes(): void {
    this.api.listCreditNotes(this.orgId!).subscribe({
      next: (res) => (this.creditNotes = res.items),
      error: (e) => (this.error = e.error?.message ?? 'Error loading credit notes'),
    });
  }

  submit(): void {
    if (this.form.invalid) return;
    this.api.createCreditNote(this.orgId!, this.form.value).subscribe({
      next: () => { this.showForm = false; this.loadCreditNotes(); },
      error: (e) => (this.error = e.error?.message ?? 'Error creating credit note'),
    });
  }

  apply(id: number): void {
    this.api.applyCreditNote(this.orgId!, id).subscribe({
      next: () => this.loadCreditNotes(),
      error: (e) => (this.error = e.error?.message ?? 'Error applying credit note'),
    });
  }
}
