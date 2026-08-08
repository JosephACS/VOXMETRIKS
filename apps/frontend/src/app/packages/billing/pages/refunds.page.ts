import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { BillingApiService } from '../services/billing-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { Payment, Refund } from '../models/billing.models';
import { isRefundablePayment } from '../billing-option-filters';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { LocaleDatePipe, LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-refunds',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    TranslatePipe,
    LocaleMoneyPipe,
    LocaleDatePipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  template: `
    <div class="vx-enterprise refunds-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <app-enterprise-page-header [title]="'billing.refunds.title' | t:lang()">
          <button type="button" class="btn btn--secondary" (click)="toggleForm()" [disabled]="submitting">
            {{ (showForm ? 'billing.refunds.cancel' : 'billing.refunds.new') | t:lang() }}
          </button>
        </app-enterprise-page-header>

        <p class="muted page-hint">{{ 'billing.refunds.hint' | t:lang() }}</p>

        @if (showForm) {
          <app-enterprise-section-card [title]="'billing.refunds.new' | t:lang()">
            <form [formGroup]="form" (ngSubmit)="submit()" class="form-grid">
              <app-enterprise-form-field [label]="'billing.refunds.payment' | t:lang()" [required]="true">
                <select formControlName="payment_id" class="select" (change)="onPaymentPicked()">
                  <option [ngValue]="null">{{ 'billing.refunds.selectPayment' | t:lang() }}</option>
                  @for (p of payments; track p.id) {
                    <option [ngValue]="p.id">
                      {{ paymentLabel(p) }}
                    </option>
                  }
                </select>
              </app-enterprise-form-field>
              <app-enterprise-form-field [label]="'billing.refunds.amount' | t:lang()" [required]="true">
                <input type="number" formControlName="amount" step="0.01" class="input" />
              </app-enterprise-form-field>
              <app-enterprise-form-field [label]="'common.reason' | t:lang()">
                <input
                  formControlName="reason"
                  class="input"
                  [placeholder]="'billing.refunds.reasonPlaceholder' | t:lang()"
                />
              </app-enterprise-form-field>
              <div class="form-grid__actions">
                <button
                  type="submit"
                  class="btn btn--primary"
                  [disabled]="form.invalid || submitting"
                >
                  {{ 'billing.refunds.issue' | t:lang() }}
                </button>
              </div>
            </form>
          </app-enterprise-section-card>
        }

        @if (error) {
          <app-enterprise-error-state [message]="error" (retry)="loadRefunds()" />
        }

        @if (!refunds.length && !error) {
          <app-enterprise-empty-state
            [title]="'billing.refunds.emptyTitle' | t:lang()"
            [description]="'billing.refunds.emptyBody' | t:lang()"
            [ctaLabel]="'billing.refunds.new' | t:lang()"
            (ctaClick)="toggleForm(true)"
          />
        } @else if (refunds.length) {
          <app-enterprise-data-table>
            <table class="data-table">
              <thead>
                <tr>
                  <th>{{ 'billing.refunds.payment' | t:lang() }}</th>
                  <th>{{ 'common.amount' | t:lang() }}</th>
                  <th>{{ 'common.status' | t:lang() }}</th>
                  <th>{{ 'billing.refunds.processed' | t:lang() }}</th>
                </tr>
              </thead>
              <tbody>
                @for (r of refunds; track r.id) {
                  <tr>
                    <td>{{ paymentLabelById(r.payment_id) }}</td>
                    <td>{{ r.amount | localeMoney:r.currency }}</td>
                    <td><app-enterprise-status-badge [status]="r.status" /></td>
                    <td>{{ r.processed_at | localeDate:true }}</td>
                  </tr>
                }
              </tbody>
            </table>
          </app-enterprise-data-table>
        }
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
  payments: Payment[] = [];
  paymentById = new Map<number, Payment>();
  error: string | null = null;
  showForm = false;
  submitting = false;
  orgId: number | null = null;

  /** Stable key for the in-flight refund operation; reused on retry. */
  private pendingIdempotencyKey: string | null = null;

  form = this.fb.group({
    payment_id: [null as number | null, Validators.required],
    amount: [null as number | null, [Validators.required, Validators.min(0.01)]],
    reason: [''],
  });

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    if (!this.orgId) return;
    this.loadRefunds();
    this.loadPayments();
  }

  toggleForm(force?: boolean): void {
    if (this.submitting) return;
    this.showForm = force ?? !this.showForm;
    if (!this.showForm) {
      this.pendingIdempotencyKey = null;
      this.form.reset({ payment_id: null, amount: null, reason: '' });
    } else if (!this.payments.length) {
      this.loadPayments();
    }
  }

  loadPayments(): void {
    this.api.listPayments(this.orgId!, { page_size: 100 }).subscribe({
      next: (res) => {
        const items = res.items || [];
        this.payments = items.filter(isRefundablePayment);
        this.paymentById = new Map(items.map((p) => [p.id, p]));
      },
      error: () => {
        this.payments = [];
      },
    });
  }

  loadRefunds(): void {
    this.api.listRefunds(this.orgId!).subscribe({
      next: (res) => (this.refunds = res.items),
      error: (e) => (this.error = e.error?.message ?? this.i18n.t('common.loadFailed')),
    });
  }

  paymentLabel(p: Payment): string {
    const amt = `${p.amount} ${p.currency}`;
    const ref = p.provider_payment_id || `#${p.id}`;
    return `${ref} — ${amt} (${p.status})`;
  }

  paymentLabelById(id: number): string {
    const p = this.paymentById.get(id);
    return p ? this.paymentLabel(p) : String(id);
  }

  onPaymentPicked(): void {
    const id = this.form.value.payment_id;
    if (id == null) return;
    const p = this.paymentById.get(id);
    if (p && this.form.value.amount == null) {
      this.form.patchValue({ amount: Number(p.amount) });
    }
  }

  /** Exposed for unit tests — same key until success or cancel. */
  ensureIdempotencyKey(): string {
    if (!this.pendingIdempotencyKey) {
      this.pendingIdempotencyKey =
        typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
          ? crypto.randomUUID()
          : `refund-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
    }
    return this.pendingIdempotencyKey;
  }

  submit(): void {
    if (this.form.invalid || this.submitting || !this.orgId) return;
    this.submitting = true;
    this.error = null;
    const key = this.ensureIdempotencyKey();
    const body = {
      payment_id: this.form.value.payment_id ?? null,
      amount: this.form.value.amount ?? null,
      reason: this.form.value.reason || null,
      idempotency_key: key,
    };
    this.api.createRefund(this.orgId, body).subscribe({
      next: () => {
        this.submitting = false;
        this.pendingIdempotencyKey = null;
        this.showForm = false;
        this.form.reset({ payment_id: null, amount: null, reason: '' });
        this.loadRefunds();
      },
      error: (e) => {
        this.submitting = false;
        // Keep pendingIdempotencyKey so retries reuse the same operation key.
        this.error = e.error?.detail?.message ?? e.error?.message ?? this.i18n.t('common.createFailed');
      },
    });
  }
}
