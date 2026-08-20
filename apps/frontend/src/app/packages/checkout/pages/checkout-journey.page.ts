import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Subscription } from 'rxjs';
import { I18nService } from '../../../core/services/i18n.service';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import { LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import {
  CheckoutScope,
  CheckoutSession,
  SafePaymentMethodPayload,
} from '../models/checkout.models';
import { CheckoutApiService } from '../services/checkout-api.service';
import {
  CheckoutAction,
  CheckoutUiState,
  checkoutReducer,
  initialCheckoutState,
} from '../state/checkout.reducer';
import {
  CardBrand,
  DEMO_PAN_BY_BRAND,
  clearSensitive,
  cvvMaxDigits,
  digitsOnly,
  formatPanDisplay,
  mapToSafeMethod,
  panMaxDigits,
  validateCardInput,
} from '../utils/simulated-card';

function newIdempotencyKey(prefix: string): string {
  const id =
    typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  return `${prefix}-${id}`;
}

@Component({
  selector: 'app-checkout-journey-page',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink,
    TranslatePipe,
    LocaleMoneyPipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  template: `
    <div class="vx-enterprise checkout-journey-page">
      <app-enterprise-page-header
        [title]="'checkout.title' | t:lang()"
        [subtitle]="'checkout.subtitle' | t:lang()"
      >
        <a [routerLink]="backLink()" class="btn btn--secondary">{{
          'checkout.back' | t:lang()
        }}</a>
      </app-enterprise-page-header>

      @if (scope() === 'organization' && !orgId()) {
        <app-enterprise-org-required />
      } @else if (bootLoading()) {
        <app-enterprise-loading-skeleton [rows]="4" />
      } @else if (fatalError()) {
        <app-enterprise-error-state [message]="fatalError()!" (retry)="bootstrap()" />
      } @else {
        @if (ui().disclosureSeen) {
          <p class="alert alert--info" role="status" data-testid="checkout-simulated-notice">
            {{ 'checkout.simulatedNotice' | t:lang() }}
          </p>
        }

        <nav class="checkout-steps" aria-label="Checkout steps">
          <span [class.active]="ui().step === 'review'">{{ 'checkout.step.review' | t:lang() }}</span>
          <span [class.active]="ui().step === 'payment'">{{ 'checkout.step.payment' | t:lang() }}</span>
          <span [class.active]="ui().step === 'processing'">{{
            'checkout.step.processing' | t:lang()
          }}</span>
          <span [class.active]="ui().step === 'result'">{{ 'checkout.step.result' | t:lang() }}</span>
        </nav>

        @if (ui().errorCode) {
          <div class="alert alert--danger" role="alert">
            {{ errorMessage(ui().errorCode!) }}
          </div>
        }

        @switch (ui().step) {
          @case ('review') {
            <section class="vx-card" data-testid="checkout-review">
              <h2>{{ 'checkout.review.heading' | t:lang() }}</h2>
              @if (ui().session; as s) {
                <dl class="checkout-summary">
                  <div>
                    <dt>{{ 'checkout.review.plan' | t:lang() }}</dt>
                    <dd>{{ s.plan_code || s.plan_id }}</dd>
                  </div>
                  <div>
                    <dt>{{ 'checkout.review.period' | t:lang() }}</dt>
                    <dd>{{ s.billing_period }}</dd>
                  </div>
                  <div>
                    <dt>{{ 'checkout.review.amount' | t:lang() }}</dt>
                    <dd>{{ s.amount | localeMoney: s.currency }}</dd>
                  </div>
                </dl>
              }
              <div class="actions">
                <button
                  type="button"
                  class="btn btn--primary"
                  [disabled]="ui().submitting"
                  (click)="continueToPayment()"
                >
                  {{ 'checkout.continuePayment' | t:lang() }}
                </button>
              </div>
            </section>
          }
          @case ('billing') {
            <section class="vx-card">
              <p class="muted">{{ 'checkout.billing.skipped' | t:lang() }}</p>
              <button type="button" class="btn btn--primary" (click)="dispatch({ type: 'GO_STEP', step: 'payment' })">
                {{ 'checkout.continuePayment' | t:lang() }}
              </button>
            </section>
          }
          @case ('payment') {
            <section class="vx-card pay-panel" data-testid="checkout-payment">
              <h2>{{ 'checkout.payment.heading' | t:lang() }}</h2>
              @if (ui().attachedMethod; as m) {
                <p class="muted">
                  {{ m.display_label || (m.brand + ' ···· ' + m.last4) }}
                </p>
              }

              <div class="brand-picker" role="radiogroup" [attr.aria-label]="'checkout.payment.brand' | t:lang()">
                @for (b of brands; track b.id) {
                  <button
                    type="button"
                    class="brand-chip"
                    role="radio"
                    [attr.aria-checked]="cardBrand === b.id"
                    [class.active]="cardBrand === b.id"
                    [attr.data-testid]="'checkout-brand-' + b.id"
                    (click)="selectBrand(b.id)"
                  >
                    <span class="brand-chip__mark" [attr.data-brand]="b.id" aria-hidden="true"></span>
                    <span>{{ b.labelKey | t:lang() }}</span>
                  </button>
                }
              </div>

              <div class="pay-preview" [attr.data-brand]="cardBrand" aria-hidden="true">
                <div class="pay-preview__top">
                  <span class="pay-preview__chip"></span>
                  <span class="pay-preview__brand">{{ brandLabelKey() | t:lang() }}</span>
                </div>
                <div class="pay-preview__pan">{{ panPreview() }}</div>
                <div class="pay-preview__bottom">
                  <span>{{ expMonthDisplay() }} / {{ expYearDisplay() }}</span>
                  <span>•••</span>
                </div>
              </div>

              <p class="pay-hint" data-testid="checkout-demo-hint">
                {{ 'checkout.payment.demoHint' | t:lang() }}
                <button type="button" class="pay-hint__fill" (click)="fillDemoCard()">
                  {{ formatPanDisplay(demoPan(), cardBrand) }}
                </button>
              </p>

              <form class="vx-form pay-form" (ngSubmit)="submitPayment()" novalidate>
                <div class="form-field">
                  <label for="checkout-pan">{{ 'checkout.payment.pan' | t:lang() }}</label>
                  <input
                    id="checkout-pan"
                    name="pan"
                    class="input"
                    autocomplete="cc-number"
                    inputmode="numeric"
                    [attr.maxlength]="panInputMax()"
                    data-testid="checkout-card-pan"
                    [ngModel]="panDisplay"
                    (ngModelChange)="onPanChange($event)"
                  />
                </div>
                <div class="form-field">
                  <label for="checkout-cvv">{{ 'checkout.payment.cvv' | t:lang() }}</label>
                  <input
                    id="checkout-cvv"
                    name="cvv"
                    class="input"
                    autocomplete="cc-csc"
                    inputmode="numeric"
                    [attr.maxlength]="cvvInputMax()"
                    data-testid="checkout-card-cvv"
                    [ngModel]="cvv"
                    (ngModelChange)="onCvvChange($event)"
                  />
                </div>
                <div class="form-row">
                  <div class="form-field">
                    <label for="checkout-exp-month">{{ 'checkout.payment.expMonth' | t:lang() }}</label>
                    <input
                      id="checkout-exp-month"
                      name="expMonth"
                      class="input"
                      inputmode="numeric"
                      maxlength="2"
                      placeholder="MM"
                      data-testid="checkout-exp-month"
                      [ngModel]="expMonthText"
                      (ngModelChange)="onMonthChange($event)"
                    />
                  </div>
                  <div class="form-field">
                    <label for="checkout-exp-year">{{ 'checkout.payment.expYear' | t:lang() }}</label>
                    <input
                      id="checkout-exp-year"
                      name="expYear"
                      class="input"
                      inputmode="numeric"
                      maxlength="4"
                      placeholder="AAAA"
                      data-testid="checkout-exp-year"
                      [ngModel]="expYearText"
                      (ngModelChange)="onYearChange($event)"
                    />
                  </div>
                </div>
                <div class="actions">
                  <button
                    type="submit"
                    class="btn btn--primary"
                    data-testid="checkout-confirm"
                    [disabled]="ui().submitting"
                  >
                    {{
                      ui().submitting
                        ? ('checkout.processing' | t:lang())
                        : ('checkout.confirmPay' | t:lang())
                    }}
                  </button>
                  @if (canRetry()) {
                    <button
                      type="button"
                      class="btn btn--secondary"
                      data-testid="checkout-retry"
                      [disabled]="ui().submitting"
                      (click)="retryPayment()"
                    >
                      {{ 'checkout.retry' | t:lang() }}
                    </button>
                  }
                </div>
              </form>
            </section>
          }
          @case ('processing') {
            <section class="vx-card" aria-busy="true">
              <app-enterprise-loading-skeleton [rows]="2" />
              <p>{{ 'checkout.processingMessage' | t:lang() }}</p>
              <button type="button" class="btn btn--secondary" (click)="pollSession()">
                {{ 'checkout.refreshStatus' | t:lang() }}
              </button>
            </section>
          }
          @case ('result') {
            <section class="vx-card" data-testid="checkout-result">
              <h2>{{ resultTitle() }}</h2>
              <p>{{ resultBody() }}</p>
              @if (ui().session; as s) {
                <dl class="checkout-summary">
                  @if (s.invoice_id) {
                    <div>
                      <dt>{{ 'checkout.result.invoice' | t:lang() }}</dt>
                      <dd>#{{ s.invoice_id }}</dd>
                    </div>
                  }
                  @if (s.subscription_id) {
                    <div>
                      <dt>{{ 'checkout.result.subscription' | t:lang() }}</dt>
                      <dd>#{{ s.subscription_id }}</dd>
                    </div>
                  }
                </dl>
              }
              <div class="actions">
                <a [routerLink]="resultLink()" class="btn btn--primary">{{
                  'checkout.result.continue' | t:lang()
                }}</a>
                @if (canRetry()) {
                  <button
                    type="button"
                    class="btn btn--secondary"
                    data-testid="checkout-retry"
                    (click)="retryPayment()"
                  >
                    {{ 'checkout.retry' | t:lang() }}
                  </button>
                }
              </div>
            </section>
          }
        }
      }
    </div>
  `,
  styles: [
    `
      .checkout-steps {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        margin-bottom: 1rem;
        font-size: 0.875rem;
      }
      .checkout-steps .active {
        font-weight: 600;
        text-decoration: underline;
        color: var(--accent, #0d9f70);
      }
      .checkout-summary {
        display: grid;
        gap: 0.5rem;
        margin: 1rem 0;
      }
      .checkout-summary div {
        display: flex;
        gap: 0.75rem;
      }
      .checkout-summary dt {
        font-weight: 600;
        min-width: 6rem;
      }
      .pay-panel h2 {
        margin-bottom: 0.85rem;
      }
      .brand-picker {
        display: flex;
        flex-wrap: wrap;
        gap: 0.55rem;
        margin: 0 0 1rem;
      }
      .brand-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.45rem 0.75rem;
        border-radius: 999px;
        border: 1px solid var(--border, rgba(18, 28, 24, 0.16));
        background: var(--vx-surface, #e3eae6);
        color: var(--color-text, #121916);
        font: inherit;
        font-size: 0.8125rem;
        font-weight: 600;
        cursor: pointer;
        transition: border-color 0.15s, box-shadow 0.15s, background 0.15s;
      }
      .brand-chip:hover {
        border-color: color-mix(in srgb, var(--accent, #0d9f70) 45%, transparent);
      }
      .brand-chip.active {
        border-color: var(--accent, #0d9f70);
        background: var(--accent-dim, rgba(13, 159, 112, 0.12));
        box-shadow: 0 0 0 2px color-mix(in srgb, var(--accent, #0d9f70) 22%, transparent);
      }
      .brand-chip__mark {
        width: 1.35rem;
        height: 0.9rem;
        border-radius: 0.2rem;
        background: linear-gradient(135deg, #1a1f71, #3b82f6);
      }
      .brand-chip__mark[data-brand='mastercard'] {
        background: linear-gradient(90deg, #eb001b 0 50%, #f79e1b 50% 100%);
      }
      .brand-chip__mark[data-brand='amex'] {
        background: linear-gradient(135deg, #016fd0, #00a3e0);
      }
      .pay-preview {
        position: relative;
        margin: 0 0 1rem;
        padding: 1.1rem 1.15rem 1rem;
        border-radius: 1rem;
        min-height: 8.5rem;
        color: #f4f8f6;
        background:
          radial-gradient(ellipse 70% 80% at 100% 0%, rgba(30, 216, 150, 0.28), transparent 55%),
          linear-gradient(145deg, #121916 0%, #1c2a24 52%, #0f1714 100%);
        box-shadow: 0 14px 32px rgba(18, 28, 24, 0.18);
        overflow: hidden;
      }
      .pay-preview[data-brand='mastercard'] {
        background:
          radial-gradient(ellipse 55% 70% at 85% 15%, rgba(247, 158, 27, 0.35), transparent 50%),
          radial-gradient(ellipse 45% 60% at 70% 20%, rgba(235, 0, 27, 0.28), transparent 48%),
          linear-gradient(145deg, #1a1214 0%, #2a1c1e 55%, #120e10 100%);
      }
      .pay-preview[data-brand='amex'] {
        background:
          radial-gradient(ellipse 60% 70% at 90% 10%, rgba(0, 163, 224, 0.35), transparent 55%),
          linear-gradient(145deg, #061525 0%, #0b2f4a 55%, #05101c 100%);
      }
      .pay-preview__top,
      .pay-preview__bottom {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.75rem;
        font-size: 0.75rem;
        letter-spacing: 0.04em;
        text-transform: uppercase;
        opacity: 0.9;
      }
      .pay-preview__chip {
        width: 2.4rem;
        height: 1.7rem;
        border-radius: 0.35rem;
        background: linear-gradient(145deg, #d4af37, #f5e6a3 45%, #b8860b);
        box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.25);
      }
      .pay-preview__pan {
        margin: 1.15rem 0 0.95rem;
        font-size: 1.15rem;
        font-weight: 600;
        letter-spacing: 0.12em;
        font-variant-numeric: tabular-nums;
      }
      .pay-hint {
        margin: 0 0 0.85rem;
        font-size: 0.8125rem;
        color: var(--color-text-secondary, rgba(18, 25, 22, 0.72));
        line-height: 1.45;
      }
      .pay-hint__fill {
        display: inline;
        margin-left: 0.25rem;
        padding: 0;
        border: 0;
        background: none;
        color: var(--accent, #0d9f70);
        font: inherit;
        font-weight: 700;
        cursor: pointer;
        text-decoration: underline;
        text-underline-offset: 2px;
      }
      .pay-form .input {
        font-variant-numeric: tabular-nums;
      }
      .form-row {
        display: flex;
        gap: 1rem;
      }
      .form-row .form-field {
        flex: 1;
      }
      .actions {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        margin-top: 1rem;
      }
    `,
  ],
})
export class CheckoutJourneyPage implements OnInit, OnDestroy {
  private readonly api = inject(CheckoutApiService);
  private readonly i18n = inject(I18nService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly orgCtx = inject(OrganizationContextService);

  readonly lang = this.i18n.lang;

  readonly scope = signal<CheckoutScope>('personal');
  readonly orgId = signal<number | null>(null);
  readonly bootLoading = signal(true);
  readonly fatalError = signal<string | null>(null);
  readonly ui = signal<CheckoutUiState>({ ...initialCheckoutState });

  /** In-memory only — never copied into reducer state. */
  pan = '';
  panDisplay = '';
  cvv = '';
  expMonth = 12;
  expYear = new Date().getFullYear() + 2;
  expMonthText = '12';
  expYearText = String(new Date().getFullYear() + 2);
  cardBrand: CardBrand = 'visa';

  readonly brands: Array<{ id: CardBrand; labelKey: string }> = [
    { id: 'visa', labelKey: 'checkout.payment.brand.visa' },
    { id: 'mastercard', labelKey: 'checkout.payment.brand.mastercard' },
    { id: 'amex', labelKey: 'checkout.payment.brand.amex' },
  ];

  private createKey: string | null = null;
  private confirmKey: string | null = null;
  private pollSub: Subscription | null = null;
  private pollTimer: ReturnType<typeof setInterval> | null = null;
  private conflictRetried = false;

  ngOnInit(): void {
    const dataScope = this.route.snapshot.data['checkoutScope'] as CheckoutScope | undefined;
    this.scope.set(dataScope === 'organization' ? 'organization' : 'personal');
    void this.bootstrapWithContext();
  }

  private async bootstrapWithContext(): Promise<void> {
    const qOrg = Number(this.route.snapshot.queryParamMap.get('organization_id') || 0);
    if (this.scope() === 'organization') {
      if (qOrg > 0) {
        try {
          await this.orgCtx.activate(qOrg);
        } catch {
          this.orgId.set(null);
          this.fatalError.set(this.i18n.t('checkout.error.orgRequired'));
          this.bootLoading.set(false);
          return;
        }
        const org = this.orgCtx.activeOrganization();
        if (!org || org.id !== qOrg) {
          this.orgId.set(null);
          this.fatalError.set(this.i18n.t('checkout.error.orgRequired'));
          this.bootLoading.set(false);
          return;
        }
        this.orgId.set(org.id);
      } else {
        this.orgId.set(this.orgCtx.organizationId());
      }
    } else {
      this.orgId.set(null);
    }
    this.bootstrap();
  }

  ngOnDestroy(): void {
    this.stopPolling();
    this.clearCardFields();
  }

  dispatch(action: CheckoutAction): void {
    this.ui.update((s) => checkoutReducer(s, action));
  }

  backLink(): string {
    return this.scope() === 'organization' ? '/subscriptions/select-plan' : '/account/plans';
  }

  resultLink(): string {
    return this.scope() === 'organization' ? '/subscriptions/overview' : '/account/subscription';
  }

  continueToPayment(): void {
    if (!this.ui().disclosureSeen) {
      this.dispatch({ type: 'SET_DISCLOSURE_SEEN', seen: true });
    }
    this.dispatch({ type: 'GO_STEP', step: 'payment' });
  }

  canRetry(): boolean {
    const s = this.ui().session;
    if (!s) return false;
    return s.status === 'failed' || s.next_action === 'retry_or_change_method';
  }

  errorMessage(code: string): string {
    const key = `checkout.error.${code}`;
    const t = this.i18n.t(key);
    if (t && t !== key && t !== this.i18n.t('common.missingTranslation')) return t;
    return this.i18n.t('checkout.error.generic');
  }

  resultTitle(): string {
    const status = this.ui().session?.status;
    if (status === 'succeeded') return this.i18n.t('checkout.result.successTitle');
    if (status === 'canceled' || status === 'expired') {
      return this.i18n.t('checkout.result.canceledTitle');
    }
    return this.i18n.t('checkout.result.failedTitle');
  }

  resultBody(): string {
    const status = this.ui().session?.status;
    if (status === 'succeeded') return this.i18n.t('checkout.result.successBody');
    if (status === 'canceled' || status === 'expired') {
      return this.i18n.t('checkout.result.canceledBody');
    }
    return this.i18n.t('checkout.result.failedBody');
  }

  bootstrap(): void {
    this.bootLoading.set(true);
    this.fatalError.set(null);
    this.dispatch({ type: 'RESET' });

    const q = this.route.snapshot.queryParamMap;
    const checkoutId = Number(q.get('checkout_id') || 0) || null;

    if (this.scope() === 'organization' && !this.orgId()) {
      this.fatalError.set(this.i18n.t('checkout.error.orgRequired'));
      this.bootLoading.set(false);
      return;
    }

    if (checkoutId) {
      this.loadSession(checkoutId, true);
      return;
    }

    // New attempt from plans: always mint a fresh create key.
    this.createKey = null;
    this.conflictRetried = false;
    this.createSessionFromQuery();
  }

  private createSessionFromQuery(): void {
    const q = this.route.snapshot.queryParamMap;
    this.createKey = this.createKey ?? newIdempotencyKey('checkout-create');

    if (this.scope() === 'personal') {
      const planCode = q.get('plan_code');
      const billingPeriod = q.get('billing_period') || 'monthly';
      if (!planCode) {
        this.fatalError.set(this.i18n.t('checkout.error.missingPlan'));
        this.bootLoading.set(false);
        return;
      }
      this.api
        .createPersonal({
          plan_code: planCode,
          billing_period: billingPeriod,
          plan_id: Number(q.get('plan_id') || 0) || undefined,
          plan_price_id: Number(q.get('plan_price_id') || 0) || undefined,
          idempotency_key: this.createKey,
        })
        .subscribe({
          next: (session) => this.onSessionReady(session, true),
          error: (e) => this.onFatalApiError(e),
        });
      return;
    }

    const orgId = this.orgId()!;
    const planId = Number(q.get('plan_id') || 0);
    const planPriceId = Number(q.get('plan_price_id') || 0);
    if (!planId || !planPriceId) {
      this.fatalError.set(this.i18n.t('checkout.error.missingPlan'));
      this.bootLoading.set(false);
      return;
    }
    this.api
      .createOrganization(orgId, {
        plan_id: planId,
        plan_price_id: planPriceId,
        billing_period: q.get('billing_period') || undefined,
        idempotency_key: this.createKey,
      })
      .subscribe({
        next: (session) => this.onSessionReady(session, true),
        error: (e) => this.onFatalApiError(e),
      });
  }

  private loadSession(checkoutId: number, initial: boolean): void {
    const obs =
      this.scope() === 'personal'
        ? this.api.getPersonal(checkoutId)
        : this.api.getOrganization(this.orgId()!, checkoutId);
    obs.subscribe({
      next: (session) => this.onSessionReady(session, initial),
      error: (e) => this.onFatalApiError(e),
    });
  }

  private onSessionReady(session: CheckoutSession, initial: boolean): void {
    this.bootLoading.set(false);
    // Abandoned/expired session loaded by id → start a fresh checkout for the same plan.
    if (
      initial &&
      (session.status === 'canceled' || session.status === 'expired') &&
      !this.route.snapshot.queryParamMap.get('plan_code') &&
      !this.route.snapshot.queryParamMap.get('plan_id')
    ) {
      this.fatalError.set(this.i18n.t('checkout.result.canceledBody'));
      return;
    }
    if (initial && (session.status === 'canceled' || session.status === 'expired')) {
      this.createKey = null;
      void this.router.navigate([], {
        relativeTo: this.route,
        queryParams: { checkout_id: null },
        queryParamsHandling: 'merge',
        replaceUrl: true,
      }).then(() => this.createSessionFromQuery());
      return;
    }
    if (!this.ui().disclosureSeen) {
      this.dispatch({ type: 'SET_DISCLOSURE_SEEN', seen: true });
    }
    this.dispatch({ type: 'APPLY_SESSION', session });
    if (initial && (session.status === 'draft' || session.status === 'awaiting_method' || session.status === 'ready' || session.status === 'failed')) {
      this.dispatch({ type: 'GO_STEP', step: 'review' });
    }
    void this.router.navigate([], {
      relativeTo: this.route,
      queryParams: { checkout_id: session.id },
      queryParamsHandling: 'merge',
      replaceUrl: true,
    });
    if (session.status === 'processing') {
      this.startPolling();
    } else {
      this.stopPolling();
    }
    if (session.status === 'succeeded') {
      void this.afterSuccess();
    }
  }

  private onFatalApiError(e: { error?: { detail?: { message?: string; code?: string } } }): void {
    this.bootLoading.set(false);
    const code = e?.error?.detail?.code;
    const msg = e?.error?.detail?.message;
    // Legacy conflict: open session exists — retry create once (backend now resumes).
    if (code === 'checkout_idempotency_conflict' && !this.conflictRetried) {
      this.conflictRetried = true;
      this.createKey = null;
      this.bootLoading.set(true);
      this.createSessionFromQuery();
      return;
    }
    this.fatalError.set(msg || (code ? this.errorMessage(code) : this.i18n.t('checkout.error.generic')));
  }

  submitPayment(): void {
    if (this.ui().submitting) return;
    const session = this.ui().session;
    if (!session) return;

    const validation = validateCardInput(
      this.pan,
      this.cvv,
      Number(this.expMonth),
      Number(this.expYear),
      this.cardBrand,
    );
    if (!validation.ok) {
      this.dispatch({ type: 'SET_ERROR', errorCode: validation.errors[0] || 'invalid_pan' });
      return;
    }

    let payload: SafePaymentMethodPayload;
    try {
      payload = mapToSafeMethod(
        this.pan,
        this.cvv,
        Number(this.expMonth),
        Number(this.expYear),
        this.cardBrand,
      );
    } catch {
      this.dispatch({ type: 'SET_ERROR', errorCode: 'invalid_pan' });
      return;
    }

    this.clearCardFields();
    this.dispatch({ type: 'SET_SUBMITTING', submitting: true });
    this.dispatch({ type: 'SET_ERROR', errorCode: null });

    const attach$ =
      this.scope() === 'personal'
        ? this.api.attachPersonalPaymentMethod(session.id, payload)
        : this.api.attachOrganizationPaymentMethod(this.orgId()!, session.id, payload);

    attach$.subscribe({
      next: (ready) => {
        this.dispatch({
          type: 'SET_ATTACHED_METHOD',
          method: {
            brand: payload.brand,
            last4: payload.last4,
            exp_month: payload.exp_month,
            exp_year: payload.exp_year,
            display_label: payload.display_label,
          },
        });
        this.confirmSession(ready);
      },
      error: (e) => {
        this.dispatch({
          type: 'SET_ERROR',
          errorCode: e?.error?.detail?.code || 'payment_method_required',
        });
      },
    });
  }

  selectBrand(brand: CardBrand): void {
    this.cardBrand = brand;
    this.pan = digitsOnly(this.pan).slice(0, panMaxDigits(brand));
    this.panDisplay = formatPanDisplay(this.pan, brand);
    this.cvv = digitsOnly(this.cvv).slice(0, cvvMaxDigits(brand));
    this.dispatch({ type: 'SET_ERROR', errorCode: null });
  }

  fillDemoCard(): void {
    const demo = DEMO_PAN_BY_BRAND[this.cardBrand];
    this.pan = demo;
    this.panDisplay = formatPanDisplay(demo, this.cardBrand);
    this.cvv = this.cardBrand === 'amex' ? '1234' : '123';
    this.expMonth = 12;
    this.expYear = new Date().getFullYear() + 2;
    this.expMonthText = '12';
    this.expYearText = String(this.expYear);
    this.dispatch({ type: 'SET_ERROR', errorCode: null });
  }

  demoPan(): string {
    return DEMO_PAN_BY_BRAND[this.cardBrand];
  }

  formatPanDisplay(pan: string, brand: CardBrand): string {
    return formatPanDisplay(pan, brand);
  }

  brandLabelKey(): string {
    return `checkout.payment.brand.${this.cardBrand}`;
  }

  panPreview(): string {
    return this.panDisplay || '•••• •••• •••• ••••';
  }

  expMonthDisplay(): string {
    return this.expMonthText.padStart(2, '0').slice(0, 2) || 'MM';
  }

  expYearDisplay(): string {
    return this.expYearText.slice(0, 4) || 'AAAA';
  }

  panInputMax(): number {
    return this.cardBrand === 'amex' ? 17 : 19;
  }

  cvvInputMax(): number {
    return cvvMaxDigits(this.cardBrand);
  }

  onPanChange(value: string): void {
    const digits = digitsOnly(value).slice(0, panMaxDigits(this.cardBrand));
    this.pan = digits;
    this.panDisplay = formatPanDisplay(digits, this.cardBrand);
  }

  onCvvChange(value: string): void {
    this.cvv = digitsOnly(value).slice(0, cvvMaxDigits(this.cardBrand));
  }

  onMonthChange(value: string): void {
    const digits = digitsOnly(value).slice(0, 2);
    this.expMonthText = digits;
    const n = Number(digits);
    this.expMonth = Number.isFinite(n) ? n : 0;
  }

  onYearChange(value: string): void {
    const digits = digitsOnly(value).slice(0, 4);
    this.expYearText = digits;
    const n = Number(digits);
    this.expYear = Number.isFinite(n) ? n : 0;
  }

  private confirmSession(session: CheckoutSession): void {
    this.confirmKey = this.confirmKey ?? newIdempotencyKey('checkout-confirm');
    this.dispatch({ type: 'GO_STEP', step: 'processing' });
    this.dispatch({ type: 'SET_SUBMITTING', submitting: true });

    const confirm$ =
      this.scope() === 'personal'
        ? this.api.confirmPersonal(session.id, { idempotency_key: this.confirmKey })
        : this.api.confirmOrganization(this.orgId()!, session.id, {
            idempotency_key: this.confirmKey,
          });

    confirm$.subscribe({
      next: (result) => {
        this.confirmKey = null;
        this.onSessionReady(result, false);
      },
      error: (e) => {
        const detail = e?.error?.detail;
        const nested = detail?.checkout as CheckoutSession | undefined;
        if (
          nested &&
          (nested.status === 'failed' ||
            nested.status === 'processing' ||
            detail?.code === 'payment_declined')
        ) {
          this.confirmKey = null;
          this.onSessionReady(nested, false);
          return;
        }
        const code = detail?.code || 'payment_confirmation_failed';
        this.dispatch({ type: 'SET_ERROR', errorCode: code });
        this.dispatch({ type: 'GO_STEP', step: 'payment' });
        this.pollSession();
      },
    });
  }

  retryPayment(): void {
    this.confirmKey = null;
    this.dispatch({ type: 'SET_ERROR', errorCode: null });
    this.dispatch({ type: 'GO_STEP', step: 'payment' });
  }

  pollSession(): void {
    const id = this.ui().session?.id;
    if (!id) return;
    this.loadSession(id, false);
  }

  private startPolling(): void {
    this.stopPolling();
    this.pollTimer = setInterval(() => this.pollSession(), 2500);
  }

  private stopPolling(): void {
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
    this.pollSub?.unsubscribe();
    this.pollSub = null;
  }

  private async afterSuccess(): Promise<void> {
    if (this.scope() !== 'organization') return;
    const orgId = this.orgId();
    if (!orgId) return;
    try {
      await this.orgCtx.bootstrap({ force: true });
      await this.orgCtx.activate(orgId);
    } catch {
      this.fatalError.set(this.i18n.t('checkout.error.generic'));
      return;
    }
    await this.router.navigate(['/organizations/onboarding'], {
      queryParams: { organization_id: orgId },
    });
  }

  /** Exposed for unit tests — clears in-memory card fields. */
  clearCardFields(): void {
    const panRef = { value: this.pan };
    const cvvRef = { value: this.cvv };
    clearSensitive(panRef);
    clearSensitive(cvvRef);
    this.pan = panRef.value;
    this.panDisplay = '';
    this.cvv = cvvRef.value;
  }
}
