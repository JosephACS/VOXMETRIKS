import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { BillingApiService } from '../services/billing-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { Invoice, Payment } from '../models/billing.models';
import { isManualTransferInvoice } from '../billing-option-filters';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-manual-transfer',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    TranslatePipe,
    LocaleMoneyPipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  template: `
    <div class="vx-enterprise manual-transfer-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <app-enterprise-page-header
          [title]="'billing.manualTransfer.title' | t:lang()"
          [subtitle]="'billing.manualTransfer.hint' | t:lang()"
        />

        <app-enterprise-section-card>
          <form [formGroup]="form" (ngSubmit)="submit()" class="form-grid">
            <app-enterprise-form-field
              [label]="'billing.manualTransfer.invoice' | t:lang()"
              [required]="true"
            >
              <select formControlName="invoice_id" class="select" (change)="onInvoicePicked()">
                <option [ngValue]="null">{{ 'billing.manualTransfer.selectInvoice' | t:lang() }}</option>
                @for (inv of invoices; track inv.id) {
                  <option [ngValue]="inv.id">
                    {{ inv.invoice_number }} — {{ inv.amount_due | localeMoney:inv.currency }} ({{ inv.status }})
                  </option>
                }
              </select>
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'common.amount' | t:lang()" [required]="true">
              <input type="number" formControlName="amount" class="input" step="0.01" />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'common.currency' | t:lang()" [required]="true">
              <input formControlName="currency" class="input" maxlength="3" readonly />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'billing.manualTransfer.notes' | t:lang()">
              <input
                formControlName="notes"
                class="input"
                [placeholder]="'billing.manualTransfer.notesPlaceholder' | t:lang()"
              />
            </app-enterprise-form-field>
            <div class="form-grid__actions">
              <button type="submit" class="btn btn--primary" [disabled]="form.invalid || loading">
                {{
                  (loading ? 'billing.manualTransfer.processing' : 'billing.manualTransfer.submit')
                    | t:lang()
                }}
              </button>
            </div>
          </form>
        </app-enterprise-section-card>

        @if (result) {
          <div class="alert alert--success" role="status">
            {{ 'billing.manualTransfer.success' | t:{ id: result.id }:lang() }}
            —
            <app-enterprise-status-badge [status]="result.status" />
          </div>
        }
        @if (error) {
          <app-enterprise-error-state [message]="error" />
        }
      }
    </div>
  `,
})
export class ManualTransferPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(BillingApiService);
  private orgCtx = inject(OrganizationContextService);
  private fb = inject(FormBuilder);

  orgId: number | null = null;
  invoices: Invoice[] = [];
  loading = false;
  result: Payment | null = null;
  error: string | null = null;

  form = this.fb.group({
    invoice_id: [null as number | null, Validators.required],
    amount: [null as number | null, [Validators.required, Validators.min(0.01)]],
    currency: ['USD', [Validators.required, Validators.maxLength(3)]],
    notes: [''],
  });

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    if (!this.orgId) return;
    this.api.listInvoices(this.orgId, { page_size: 100 }).subscribe({
      next: (res) => {
        this.invoices = (res.items || []).filter(isManualTransferInvoice);
      },
      error: (e) => (this.error = e.error?.message ?? this.i18n.t('common.loadFailed')),
    });
  }

  onInvoicePicked(): void {
    const id = this.form.value.invoice_id;
    const inv = this.invoices.find((i) => i.id === id);
    if (!inv) return;
    this.form.patchValue({
      amount: Number(inv.amount_due || inv.total || 0) || null,
      currency: inv.currency || 'USD',
    });
  }

  submit(): void {
    if (this.form.invalid || !this.orgId) return;
    this.loading = true;
    this.error = null;
    this.api.createManualTransfer(this.orgId!, this.form.value).subscribe({
      next: (p) => {
        this.result = p;
        this.loading = false;
      },
      error: (e) => {
        this.error = e.error?.detail?.message ?? e.error?.message ?? this.i18n.t('common.actionFailed');
        this.loading = false;
      },
    });
  }
}
