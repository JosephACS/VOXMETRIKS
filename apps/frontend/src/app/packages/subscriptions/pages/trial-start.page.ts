import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { SubscriptionsApiService } from '../services/subscriptions-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { Plan, PlanPrice } from '../models/subscriptions.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { LocaleFormatService } from '../../../core/services/locale-format.service';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-trial-start',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
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

        <app-enterprise-section-card [title]="'subscriptions.trial.formTitle' | t:lang()">
          <form [formGroup]="form" (ngSubmit)="onSubmit()" class="form-grid">
            <app-enterprise-form-field
              [label]="'subscriptions.trial.plan' | t:lang()"
              [required]="true"
            >
              <select formControlName="planId" class="input" (change)="onPlanChange()">
                <option [ngValue]="0">{{ 'subscriptions.trial.selectPlan' | t:lang() }}</option>
                @for (p of plans; track p.id) {
                  <option [ngValue]="p.id">
                    {{ p.display_name }}
                    ({{ p.trial_days_default }}
                    {{ 'subscriptions.trial.days' | t:lang() }})
                  </option>
                }
              </select>
            </app-enterprise-form-field>

            @if (prices.length > 0) {
              <app-enterprise-form-field [label]="'subscriptions.trial.priceOptional' | t:lang()">
                <select formControlName="planPriceId" class="input">
                  <option [ngValue]="null">{{ 'subscriptions.trial.noPrice' | t:lang() }}</option>
                  @for (p of prices; track p.id) {
                    <option [ngValue]="p.id">{{ formatPrice(p) }}</option>
                  }
                </select>
              </app-enterprise-form-field>
            }

            <app-enterprise-form-field
              [label]="'subscriptions.trial.currency' | t:lang()"
              [required]="true"
            >
              <input
                formControlName="billingCurrency"
                class="input"
                maxlength="3"
                placeholder="USD"
              />
            </app-enterprise-form-field>

            <div class="form-grid__actions">
              <button
                type="submit"
                class="btn btn--primary"
                [disabled]="form.invalid || saving"
              >
                {{ 'subscriptions.trial.submit' | t:lang() }}
              </button>
            </div>
          </form>
        </app-enterprise-section-card>

        @if (error) {
          <app-enterprise-error-state [message]="error" (retry)="reloadPlans()" />
        }
      }
    </div>
  `,
})
export class TrialStartPageComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private readonly api = inject(SubscriptionsApiService);
  private readonly orgCtx = inject(OrganizationContextService);
  private readonly fb = inject(FormBuilder);
  private readonly router = inject(Router);
  private readonly money = inject(LocaleFormatService);

  organizationId: number | null = null;
  plans: Plan[] = [];
  prices: PlanPrice[] = [];
  saving = false;
  error: string | null = null;

  form = this.fb.group({
    planId: [0, [Validators.required, Validators.min(1)]],
    planPriceId: [null as number | null],
    billingCurrency: ['USD', [Validators.required, Validators.minLength(3), Validators.maxLength(3)]],
  });

  ngOnInit(): void {
    this.organizationId = this.orgCtx.activeOrganization()?.id ?? null;
    if (!this.organizationId) return;
    this.reloadPlans();
  }

  reloadPlans(): void {
    this.error = null;
    this.api.listPlans({ status: 'active' }).subscribe({
      next: (r) => (this.plans = r.items),
      error: (e) => {
        this.error = e?.error?.detail?.message ?? this.i18n.t('subscriptions.trial.loadFailed');
      },
    });
  }

  formatPrice(pr: PlanPrice): string {
    const period =
      pr.billing_period === 'annual'
        ? this.i18n.t('subscriptions.period.annual')
        : pr.billing_period === 'monthly'
          ? this.i18n.t('subscriptions.period.monthly')
          : pr.billing_period;
    return `${this.money.formatMoney(pr.amount, pr.currency || 'USD')} / ${period}`;
  }

  onPlanChange(): void {
    const planId = Number(this.form.value.planId);
    if (!planId) return;
    this.api.listPlanPrices(planId).subscribe({
      next: (items) => {
        this.prices = items;
        this.form.patchValue({ planPriceId: null });
      },
      error: () => {
        this.prices = [];
      },
    });
  }

  onSubmit(): void {
    if (!this.organizationId || this.form.invalid) return;
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
