import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { SubscriptionsApiService } from '../services/subscriptions-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { Plan, PlanPrice } from '../models/subscriptions.models';
import { I18nService } from '../../../core/services/i18n.service';
import { LocaleFormatService } from '../../../core/services/locale-format.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

/**
 * Post-conversion / explicit plan selection.
 * Does NOT auto-create a subscription — owner chooses trial or paid.
 */
@Component({
  selector: 'app-subscription-select-plan',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="page select-plan-page vx-enterprise--narrow">
      <a routerLink="/subscriptions/overview" class="btn btn--ghost" style="margin-bottom:1rem;width:fit-content">
        {{ 'subscriptions.selectPlan.back' | t:lang() }}
      </a>

      <header class="vx-hero">
        <div>
          <h1 class="vx-hero__title">{{ 'subscriptions.selectPlan.heading' | t:lang() }}</h1>
          <p class="vx-hero__subtitle">{{ 'subscriptions.selectPlan.subtitle' | t:lang() }}</p>
          <div class="vx-hero__meta">
            @if (orgName) {
              <span class="badge badge--active">{{ orgName }}</span>
            }
            @if (conversionId) {
              <span class="badge">#{{ conversionId }}</span>
            }
          </div>
        </div>
        <div class="vx-hero__actions">
          <a routerLink="/subscriptions/plans" class="btn btn--secondary">
            {{ 'subscriptions.plans.title' | t:lang() }}
          </a>
        </div>
      </header>

      @if (!orgId) {
        <app-enterprise-org-required />
      } @else if (loading) {
        <div class="vx-skel-block" aria-busy="true">
          <div class="vx-skel"></div>
          <div class="vx-skel"></div>
        </div>
      } @else {
        <div class="vx-card">
          <form class="vx-form" [formGroup]="form" (ngSubmit)="submit()">
            <div class="form-field">
              <label>{{ 'subscriptions.selectPlan.planLabel' | t:lang() }}</label>
              <select formControlName="planId" (change)="onPlanChange()">
                <option [ngValue]="0">{{ 'common.select' | t:lang() }}</option>
                @for (p of plans; track p.id) {
                  <option [ngValue]="p.id">
                    {{ p.display_name }} ({{ p.trial_days_default }}
                    {{ 'subscriptions.trial.days' | t:lang() }})
                  </option>
                }
              </select>
            </div>

            @if (prices.length) {
              <div class="form-field">
                <label>{{ 'subscriptions.selectPlan.priceLabel' | t:lang() }}</label>
                <select formControlName="planPriceId">
                  <option [ngValue]="null">{{ 'common.select' | t:lang() }}</option>
                  @for (pr of prices; track pr.id) {
                    <option [ngValue]="pr.id">{{ formatPrice(pr) }}</option>
                  }
                </select>
              </div>
            }

            <div class="form-field">
              <label>{{ 'subscriptions.selectPlan.currencyLabel' | t:lang() }}</label>
              <input formControlName="billingCurrency" maxlength="3" class="input" />
            </div>

            <div class="form-field">
              <label>{{ 'subscriptions.selectPlan.modeLabel' | t:lang() }}</label>
              <select formControlName="mode">
                <option value="trial">{{ 'subscriptions.selectPlan.startTrial' | t:lang() }}</option>
                <option value="subscribe">{{ 'subscriptions.selectPlan.subscribeMode' | t:lang() }}</option>
              </select>
            </div>

            <div class="actions">
              <button type="submit" class="btn btn--primary" [disabled]="form.invalid || saving">
                {{ saving ? ('common.saving' | t:lang()) : ('common.confirm' | t:lang()) }}
              </button>
              <a routerLink="/billing/invoices" class="btn btn--secondary">{{
                'subscriptions.selectPlan.goBilling' | t:lang()
              }}</a>
            </div>
          </form>
        </div>

        @if (error) {
          <div class="alert alert--danger" role="alert">{{ error }}</div>
        }
        @if (success) {
          <div class="alert alert--success" role="status">{{ success }}</div>
        }
      }
    </div>
  `,
})
export class SubscriptionSelectPlanPage implements OnInit {
  private i18n = inject(I18nService);
  private money = inject(LocaleFormatService);
  readonly lang = this.i18n.lang;

  private api = inject(SubscriptionsApiService);
  private orgCtx = inject(OrganizationContextService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private fb = inject(FormBuilder);

  orgId: number | null = null;
  orgName: string | null = null;
  conversionId: number | null = null;
  plans: Plan[] = [];
  prices: PlanPrice[] = [];
  loading = false;
  saving = false;
  error: string | null = null;
  success: string | null = null;
  private preferredPeriod: string | null = null;

  form = this.fb.group({
    planId: [0, [Validators.required, Validators.min(1)]],
    planPriceId: [null as number | null, Validators.required],
    billingCurrency: ['USD', [Validators.required, Validators.minLength(3), Validators.maxLength(3)]],
    mode: ['trial', Validators.required],
  });

  async ngOnInit(): Promise<void> {
    const qOrg = Number(this.route.snapshot.queryParamMap.get('organizationId') || 0);
    const qPlan = Number(this.route.snapshot.queryParamMap.get('planId') || 0);
    this.preferredPeriod = this.route.snapshot.queryParamMap.get('period');
    this.conversionId = Number(this.route.snapshot.queryParamMap.get('conversionId') || 0) || null;
    if (qOrg) {
      try {
        await this.orgCtx.activate(qOrg);
      } catch {
        /* fall through */
      }
    }
    const org = this.orgCtx.activeOrganization();
    this.orgId = org?.id ?? (qOrg || null);
    this.orgName = org?.display_name ?? null;
    if (!this.orgId) {
      this.error = 'Activa una organización primero.';
      return;
    }
    this.loading = true;
    this.api.listPlans({ status: 'active' }).subscribe({
      next: (r) => {
        this.plans = r.items || [];
        this.loading = false;
        if (qPlan > 0 && this.plans.some((p) => p.id === qPlan)) {
          this.form.patchValue({ planId: qPlan });
          this.onPlanChange();
        }
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || 'No se pudieron cargar planes';
        this.loading = false;
      },
    });
  }

  onPlanChange(): void {
    const planId = Number(this.form.value.planId);
    this.prices = [];
    this.form.patchValue({ planPriceId: null });
    if (!planId) return;
    this.api.listPlanPrices(planId).subscribe({
      next: (prices) => {
        this.prices = (prices || []).filter((p) => p.status === 'active');
        const preferred = this.preferredPeriod
          ? this.prices.find((p) => p.billing_period === this.preferredPeriod)
          : null;
        const auto = preferred || (this.prices.length === 1 ? this.prices[0] : null);
        if (auto) {
          this.form.patchValue({
            planPriceId: auto.id,
            billingCurrency: auto.currency || 'USD',
          });
        }
      },
      error: () => {
        this.prices = [];
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

  submit(): void {
    const orgId = this.orgId;
    if (!orgId || this.form.invalid) return;
    const v = this.form.value;
    const currency = (v.billingCurrency || 'USD').toUpperCase();
    const selected = this.prices.find((p) => p.id === v.planPriceId);
    if (selected && selected.currency && selected.currency.toUpperCase() !== currency) {
      this.error = `Moneda inválida: el precio es ${selected.currency}, no ${currency}`;
      return;
    }
    this.saving = true;
    this.error = null;
    this.success = null;

    const done = () => {
      this.saving = false;
      this.success = this.i18n.t('subscriptions.selectPlan.success');
      this.router.navigate(['/subscriptions/overview']);
    };
    const fail = (e: { error?: { detail?: { message?: string } } }) => {
      this.error = e?.error?.detail?.message || this.i18n.t('subscriptions.selectPlan.failed');
      this.saving = false;
    };

    if (v.mode === 'trial') {
      this.api.startTrial(orgId, {
        organization_id: orgId,
        plan_id: v.planId!,
        plan_price_id: v.planPriceId ?? undefined,
        billing_currency: currency,
        activation_source: this.conversionId ? 'crm_conversion' : 'manual_select_plan',
      }).subscribe({ next: done, error: fail });
    } else {
      this.api.createSubscription(orgId, {
        organization_id: orgId,
        plan_id: v.planId!,
        plan_price_id: v.planPriceId!,
        billing_currency: currency,
        activation_source: this.conversionId ? 'crm_conversion' : 'manual_select_plan',
      }).subscribe({ next: done, error: fail });
    }
  }
}
