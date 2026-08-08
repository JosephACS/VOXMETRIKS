import { Component, DestroyRef, OnInit, computed, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { forkJoin, of } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import { SubscriptionsApiService } from '../services/subscriptions-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { Plan, PlanFeature, PlanPrice } from '../models/subscriptions.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

interface TrialPlanCard {
  plan: Plan;
  prices: PlanPrice[];
  features: PlanFeature[];
  primaryPrice: PlanPrice | null;
}

@Component({
  selector: 'app-trial-start',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    RouterLink,
    TranslatePipe,
    LocaleMoneyPipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  template: `
    <div class="vx-enterprise trial-start-page">
      @if (!organizationId) {
        <app-enterprise-org-required />
      } @else {
        <app-enterprise-page-header
          [title]="'subscriptions.trial.title' | t:lang()"
          [subtitle]="'subscriptions.trial.subtitle' | t:lang()"
        >
          <a routerLink="/subscriptions/overview" class="btn btn--secondary">{{
            'common.back' | t:lang()
          }}</a>
        </app-enterprise-page-header>

        <p class="muted" style="margin-bottom:1rem">
          {{ 'subscriptions.trial.noChargeNote' | t:lang() }}
        </p>

        @if (loading()) {
          <app-enterprise-loading-skeleton [rows]="4" />
        } @else if (error && !cards().length) {
          <app-enterprise-error-state [message]="error" (retry)="reloadPlans()" />
        } @else if (!cards().length) {
          <app-enterprise-empty-state
            [title]="'subscriptions.trial.noPlans' | t:lang()"
            [description]="'subscriptions.trial.loadFailed' | t:lang()"
          />
        } @else {
          <div class="plans-grid">
            @for (card of cards(); track card.plan.id) {
              <article
                class="plan-card"
                [class.plan-card--recommended]="selectedPlanId() === card.plan.id"
              >
                <h2 class="plan-card__name">{{ card.plan.display_name }}</h2>
                <div class="plan-card__price">
                  @if (card.primaryPrice) {
                    <span class="plan-card__amount">
                      {{ card.primaryPrice.amount | localeMoney:card.primaryPrice.currency }}
                    </span>
                    <span class="plan-card__period">
                      / {{ periodLabel(card.primaryPrice.billing_period) }}
                    </span>
                  } @else {
                    <span class="plan-card__amount">{{ 'subscriptions.plans.priceUnavailable' | t:lang() }}</span>
                  }
                </div>
                <p class="plan-card__desc">
                  {{ card.plan.description || ('subscriptions.plans.noDescription' | t:lang()) }}
                </p>
                @if (card.plan.trial_days_default > 0) {
                  <div class="plan-card__meta">
                    {{ card.plan.trial_days_default }}
                    {{ 'subscriptions.trial.days' | t:lang() }}
                  </div>
                }
                @if (card.features.length) {
                  <ul class="plan-card__features">
                    @for (f of card.features.slice(0, 6); track f.id) {
                      <li>
                        {{ featureLabel(f) }}
                        @if (f.limit_value != null) {
                          <span class="muted">({{ f.limit_value }})</span>
                        }
                      </li>
                    }
                  </ul>
                }
                <div class="plan-card__actions">
                  <button
                    type="button"
                    class="btn"
                    [class.btn--primary]="selectedPlanId() === card.plan.id"
                    [class.btn--secondary]="selectedPlanId() !== card.plan.id"
                    (click)="selectPlan(card)"
                  >
                    {{
                      (selectedPlanId() === card.plan.id
                        ? 'subscriptions.trial.selected'
                        : 'subscriptions.trial.selectPlanCta') | t:lang()
                    }}
                  </button>
                </div>
              </article>
            }
          </div>

          <app-enterprise-section-card
            [title]="'subscriptions.trial.formTitle' | t:lang()"
            style="margin-top:1.25rem"
          >
            <form [formGroup]="form" (ngSubmit)="onSubmit()" class="form-grid">
              @if (selectedPrices().length > 1) {
                <app-enterprise-form-field [label]="'subscriptions.trial.priceOptional' | t:lang()">
                  <select formControlName="planPriceId" class="input">
                    <option [ngValue]="null">{{ 'subscriptions.trial.noPrice' | t:lang() }}</option>
                    @for (p of selectedPrices(); track p.id) {
                      <option [ngValue]="p.id">{{ formatPrice(p) }}</option>
                    }
                  </select>
                </app-enterprise-form-field>
              }

              <app-enterprise-form-field [label]="'subscriptions.trial.currency' | t:lang()">
                @if (currencyLocked()) {
                  <p class="muted" style="margin:0">{{ form.value.billingCurrency }}</p>
                } @else {
                  <input
                    formControlName="billingCurrency"
                    class="input"
                    maxlength="3"
                    placeholder="USD"
                  />
                }
              </app-enterprise-form-field>

              <p class="muted">{{ 'subscriptions.trial.confirmNoCharge' | t:lang() }}</p>

              <div class="form-grid__actions">
                <button
                  type="submit"
                  class="btn btn--primary"
                  [disabled]="form.invalid || saving || !selectedPlanId()"
                >
                  {{ 'subscriptions.trial.submit' | t:lang() }}
                </button>
              </div>
            </form>
          </app-enterprise-section-card>
        }

        @if (error) {
          <app-enterprise-error-state [message]="error" />
        }
      }
    </div>
  `,
})
export class TrialStartPageComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;
  private readonly destroyRef = inject(DestroyRef);

  private readonly api = inject(SubscriptionsApiService);
  private readonly orgCtx = inject(OrganizationContextService);
  private readonly fb = inject(FormBuilder);
  private readonly router = inject(Router);

  organizationId: number | null = null;
  saving = false;
  error: string | null = null;

  readonly loading = signal(false);
  readonly cards = signal<TrialPlanCard[]>([]);
  readonly selectedPlanId = signal<number | null>(null);
  readonly selectedPrices = signal<PlanPrice[]>([]);
  /** Locked when a concrete plan price is selected; free currency when none. */
  readonly currencyLocked = computed(() => this.selectedPriceId() != null);
  private readonly selectedPriceId = signal<number | null>(null);

  form = this.fb.group({
    planId: [0, [Validators.required, Validators.min(1)]],
    planPriceId: [null as number | null],
    billingCurrency: ['USD', [Validators.required, Validators.minLength(3), Validators.maxLength(3)]],
  });

  ngOnInit(): void {
    this.organizationId = this.orgCtx.activeOrganization()?.id ?? null;
    this.form.controls.planPriceId.valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((priceId) => {
        this.onPlanPriceIdChange(priceId);
      });
    if (!this.organizationId) return;
    this.reloadPlans();
  }

  reloadPlans(): void {
    this.error = null;
    this.loading.set(true);
    this.api.listPlans({ status: 'active', limit: 50 }).subscribe({
      next: (r) => {
        const plans = [...r.items].sort((a, b) => a.sort_order - b.sort_order);
        if (!plans.length) {
          this.cards.set([]);
          this.loading.set(false);
          return;
        }
        forkJoin(
          plans.map((p) =>
            forkJoin({
              plan: of(p),
              prices: this.api.listPlanPrices(p.id).pipe(catchError(() => of([] as PlanPrice[]))),
              features: this.api.listPlanFeatures(p.id).pipe(catchError(() => of([] as PlanFeature[]))),
            }).pipe(
              map(({ plan, prices, features }) => ({
                plan,
                prices,
                features,
                primaryPrice: this.pickPrimaryPrice(prices),
              })),
            ),
          ),
        ).subscribe({
          next: (cards) => {
            this.cards.set(cards);
            this.loading.set(false);
          },
          error: (e) => {
            this.loading.set(false);
            this.error = e?.error?.detail?.message ?? this.i18n.t('subscriptions.trial.loadFailed');
          },
        });
      },
      error: (e) => {
        this.loading.set(false);
        this.error = e?.error?.detail?.message ?? this.i18n.t('subscriptions.trial.loadFailed');
      },
    });
  }

  selectPlan(card: TrialPlanCard): void {
    this.selectedPlanId.set(card.plan.id);
    this.selectedPrices.set(card.prices);
    const primary = card.primaryPrice;
    this.form.patchValue({
      planId: card.plan.id,
      planPriceId: primary?.id ?? null,
      billingCurrency: (primary?.currency || this.form.value.billingCurrency || 'USD').toUpperCase(),
    });
    this.selectedPriceId.set(primary?.id ?? null);
  }

  /** Keep billing currency aligned with the selected price; unlock when cleared. */
  onPlanPriceIdChange(priceId: number | null): void {
    this.selectedPriceId.set(priceId ?? null);
    if (priceId == null) return;
    const price = this.selectedPrices().find((p) => p.id === priceId);
    if (!price) return;
    this.form.patchValue(
      { billingCurrency: (price.currency || 'USD').toUpperCase() },
      { emitEvent: false },
    );
  }

  periodLabel(period: string): string {
    if (period === 'annual') return this.i18n.t('subscriptions.period.annual');
    if (period === 'monthly') return this.i18n.t('subscriptions.period.monthly');
    return period;
  }

  featureLabel(f: PlanFeature): string {
    const key = `subscriptions.feature.${f.feature_code}`;
    const t = this.i18n.t(key);
    const missing = this.i18n.t('common.missingTranslation');
    if (t && t !== key && t !== missing) return t;
    return f.feature_code.replace(/[_.]/g, ' ');
  }

  formatPrice(pr: PlanPrice): string {
    return `${pr.amount} ${pr.currency} / ${this.periodLabel(pr.billing_period)}`;
  }

  private pickPrimaryPrice(prices: PlanPrice[]): PlanPrice | null {
    if (!prices.length) return null;
    return (
      prices.find((p) => p.billing_period === 'monthly' && p.status === 'active') ||
      prices.find((p) => p.status === 'active') ||
      prices[0]
    );
  }

  onSubmit(): void {
    if (!this.organizationId || this.form.invalid || !this.selectedPlanId()) return;
    this.saving = true;
    this.error = null;
    const v = this.form.getRawValue();
    this.api
      .startTrial(this.organizationId, {
        organization_id: this.organizationId,
        plan_id: Number(v.planId),
        plan_price_id: v.planPriceId ?? undefined,
        billing_currency: (v.billingCurrency || 'USD').toUpperCase(),
      })
      .subscribe({
        next: () => {
          this.saving = false;
          void this.router.navigate(['/subscriptions/overview']);
        },
        error: (e) => {
          this.saving = false;
          this.error = e?.error?.detail?.message ?? this.i18n.t('common.actionFailed');
        },
      });
  }
}
