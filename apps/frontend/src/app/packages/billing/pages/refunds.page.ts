import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { BillingApiService } from '../services/billing-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { Refund } from '../models/billing.models';
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

        @if (showForm) {
          <app-enterprise-section-card [title]="'billing.refunds.new' | t:lang()">
            <form [formGroup]="form" (ngSubmit)="submit()" class="form-grid">
              <app-enterprise-form-field [label]="'billing.refunds.paymentId' | t:lang()" [required]="true">
                <input type="number" formControlName="payment_id" class="input" />
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
                <button type="submit" class="btn btn--primary" [disabled]="form.invalid || submitting">
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
                  <th>{{ 'common.id' | t:lang() }}</th>
                  <th>{{ 'billing.refunds.payment' | t:lang() }}</th>
                  <th>{{ 'common.amount' | t:lang() }}</th>
                  <th>{{ 'common.status' | t:lang() }}</th>
                  <th>{{ 'billing.refunds.processed' | t:lang() }}</th>
                </tr>
              </thead>
              <tbody>
                @for (r of refunds; track r.id) {
                  <tr>
                    <td>{{ r.id }}</td>
                    <td>{{ r.payment_id }}</td>
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
  error: string | null = null;
  showForm = false;
  submitting = false;
  orgId: number | null = null;
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
  }

  loadRefunds(): void {
    this.api.listRefunds(this.orgId!).subscribe({
      next: (res) => (this.refunds = res.items),
      error: (e) => (this.error = e.error?.message ?? this.i18n.t('common.loadFailed')),
    });
  }

  toggleForm(force?: boolean): void {
    if (this.submitting) return;
    this.showForm = force ?? !this.showForm;
    if (!this.showForm) {
      this.pendingIdempotencyKey = null;
      this.form.reset({ payment_id: null, amount: null, reason: '' });
    }
  }

  /** Reuse a failed operation's key until it succeeds or is cancelled. */
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
    this.api.createRefund(this.orgId, {
      payment_id: this.form.value.payment_id ?? null,
      amount: this.form.value.amount ?? null,
      reason: this.form.value.reason || null,
      idempotency_key: key,
    }).subscribe({
      next: () => {
        this.submitting = false;
        this.pendingIdempotencyKey = null;
        this.showForm = false;
        this.form.reset({ payment_id: null, amount: null, reason: '' });
        this.loadRefunds();
      },
      error: (e) => {
        this.submitting = false;
        this.error = e.error?.detail?.message ?? e.error?.message ?? this.i18n.t('common.createFailed');
      },
    });
  }
}
