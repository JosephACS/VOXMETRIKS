import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { BillingApiService } from '../services/billing-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { Payment } from '../models/billing.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-manual-transfer',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    TranslatePipe,
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
              [label]="'billing.manualTransfer.invoiceId' | t:lang()"
              [required]="true"
            >
              <input type="number" formControlName="invoice_id" class="input" />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'common.amount' | t:lang()" [required]="true">
              <input type="number" formControlName="amount" class="input" step="0.01" />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'common.currency' | t:lang()" [required]="true">
              <input formControlName="currency" class="input" maxlength="3" />
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
    this.orgId = this.orgCtx.activeOrganization()?.id ?? null;
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
        this.error = e.error?.detail?.message ?? e.error?.message ?? 'Transfer failed';
        this.loading = false;
      },
    });
  }
}
