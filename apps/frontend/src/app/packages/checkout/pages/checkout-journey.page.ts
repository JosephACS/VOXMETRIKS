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
  clearSensitive,
  mapToSafeMethod,
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
            <section class="vx-card" data-testid="checkout-payment">
              <h2>{{ 'checkout.payment.heading' | t:lang() }}</h2>
              @if (ui().attachedMethod; as m) {
                <p class="muted">
                  {{ m.display_label || (m.brand + ' ···· ' + m.last4) }}
                </p>
              }
              <form class="vx-form" (ngSubmit)="submitPayment()">
                <div class="form-field">
                  <label for="checkout-pan">{{ 'checkout.payment.pan' | t:lang() }}</label>
                  <input
                    id="checkout-pan"
                    name="pan"
                    class="input"
                    autocomplete="cc-number"
                    inputmode="numeric"
                    data-testid="checkout-card-pan"
                    [(ngModel)]="pan"
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
                    [(ngModel)]="cvv"
                  />
                </div>
                <div class="form-row">
                  <div class="form-field">
                    <label for="checkout-exp-month">{{ 'checkout.payment.expMonth' | t:lang() }}</label>
                    <input
                      id="checkout-exp-month"
                      name="expMonth"
                      type="number"
                      min="1"
                      max="12"
                      class="input"
                      [(ngModel)]="expMonth"
                    />
                  </div>
                  <div class="form-field">
                    <label for="checkout-exp-year">{{ 'checkout.payment.expYear' | t:lang() }}</label>
                    <input
                      id="checkout-exp-year"
                      name="expYear"
                      type="number"
                      min="2024"
                      max="2100"
                      class="input"
                      [(ngModel)]="expYear"
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
                  <button type="button" class="btn btn--secondary" (click)="retryPayment()">
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
  cvv = '';
  expMonth = 12;
  expYear = new Date().getFullYear() + 2;

  private createKey: string | null = null;
  private confirmKey: string | null = null;
  private pollSub: Subscription | null = null;
  private pollTimer: ReturnType<typeof setInterval> | null = null;

  ngOnInit(): void {
    const dataScope = this.route.snapshot.data['checkoutScope'] as CheckoutScope | undefined;
    this.scope.set(dataScope === 'organization' ? 'organization' : 'personal');
    const qOrg = Number(this.route.snapshot.queryParamMap.get('organization_id') || 0);
    this.orgId.set(qOrg > 0 ? qOrg : this.orgCtx.organizationId());
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
    if (!this.ui().disclosureSeen) {
      this.dispatch({ type: 'SET_DISCLOSURE_SEEN', seen: true });
    }
    this.dispatch({ type: 'APPLY_SESSION', session });
    if (initial && (session.status === 'draft' || session.status === 'awaiting_method')) {
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
    this.fatalError.set(msg || (code ? this.errorMessage(code) : this.i18n.t('checkout.error.generic')));
  }

  submitPayment(): void {
    if (this.ui().submitting) return;
    const session = this.ui().session;
    if (!session) return;

    const validation = validateCardInput(this.pan, this.cvv, Number(this.expMonth), Number(this.expYear));
    if (!validation.ok) {
      this.dispatch({ type: 'SET_ERROR', errorCode: validation.errors[0] || 'invalid_pan' });
      return;
    }

    let payload: SafePaymentMethodPayload;
    try {
      payload = mapToSafeMethod(this.pan, this.cvv, Number(this.expMonth), Number(this.expYear));
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
    if (this.scope() === 'organization') {
      try {
        await this.orgCtx.bootstrap({ force: true });
      } catch {
        /* non-blocking */
      }
    }
  }

  /** Exposed for unit tests — clears in-memory card fields. */
  clearCardFields(): void {
    const panRef = { value: this.pan };
    const cvvRef = { value: this.cvv };
    clearSensitive(panRef);
    clearSensitive(cvvRef);
    this.pan = panRef.value;
    this.cvv = cvvRef.value;
  }
}
