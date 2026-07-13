import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { SubscriptionsApiService } from '../services/subscriptions-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { Plan, PlanPrice } from '../models/subscriptions.models';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
/**
 * Post-conversion / explicit plan selection.
 * Does NOT auto-create a subscription — owner chooses trial or paid.
 */
@Component({
  selector: 'app-subscription-select-plan',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink, TranslatePipe],
  template: `
    <div class="page select-plan-page">
      <a routerLink="/subscriptions/overview">{{ 'subscriptions.selectPlan.back' | t:lang() }}</a>
      <h1>{{ 'subscriptions.selectPlan.heading' | t:lang() }}</h1>
      <p class="subtitle">{{ 'subscriptions.selectPlan.subtitle' | t:lang() }}</p>

      @if (!orgId) {
        <p class="error">{{ 'subscriptions.selectPlan.orgFirst' | t:lang() }}</p>
      } @else if (loading) {
        <p>{{ 'subscriptions.selectPlan.loadingPlans' | t:lang() }}</p>
      } @else {
        <p class="muted">{{ 'common.organization' | t:lang() }} #{{ orgId }}@if (conversionId) { · #{{ conversionId }} }</p>

        <form [formGroup]="form" (ngSubmit)="submit()">
          <div class="form-field">
            <label>{{ 'subscriptions.selectPlan.planLabel' | t:lang() }}</label>
            <select formControlName="planId" (change)="onPlanChange()">
              <option [ngValue]="0">{{ 'common.select' | t:lang() }}</option>
              @for (p of plans; track p.id) {
                <option [ngValue]="p.id">{{ p.display_name }} (trial {{ p.trial_days_default }}d)</option>
              }
            </select>
          </div>

          @if (prices.length) {
            <div class="form-field">
              <label>Precio *</label>
              <select formControlName="planPriceId">
                <option [ngValue]="null">Seleccionar…</option>
                @for (pr of prices; track pr.id) {
                  <option [ngValue]="pr.id">
                    {{ formatPrice(pr) }}
                  </option>
                }
              </select>
            </div>
          }

          <div class="form-field">
            <label>Moneda de facturación *</label>
            <input formControlName="billingCurrency" maxlength="3" />
          </div>

          <div class="form-field">
            <label>Modo *</label>
            <select formControlName="mode">
              <option value="trial">{{ 'subscriptions.selectPlan.startTrial' | t:lang() }}</option>
              <option value="subscribe">Suscripción activa (sin trial)</option>
            </select>
          </div>

          <div class="actions">
            <button type="submit" class="btn btn--primary" [disabled]="form.invalid || saving">
              {{ saving ? 'Creando…' : 'Confirmar' }}
            </button>
            <a routerLink="/billing/invoices" class="btn btn--secondary">Ir a facturación</a>
          </div>
        </form>

        @if (error) { <p class="error">{{ error }}</p> }
        @if (success) { <p class="success">{{ success }}</p> }
      }
    </div>
  `,
})
export class SubscriptionSelectPlanPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(SubscriptionsApiService);
  private orgCtx = inject(OrganizationContextService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private fb = inject(FormBuilder);

  orgId: number | null = null;
  conversionId: number | null = null;
  plans: Plan[] = [];
  prices: PlanPrice[] = [];
  loading = false;
  saving = false;
  error: string | null = null;
  success: string | null = null;

  form = this.fb.group({
    planId: [0, [Validators.required, Validators.min(1)]],
    planPriceId: [null as number | null, Validators.required],
    billingCurrency: ['USD', [Validators.required, Validators.minLength(3), Validators.maxLength(3)]],
    mode: ['trial', Validators.required],
  });

  async ngOnInit(): Promise<void> {
    const qOrg = Number(this.route.snapshot.queryParamMap.get('organizationId') || 0);
    this.conversionId = Number(this.route.snapshot.queryParamMap.get('conversionId') || 0) || null;
    if (qOrg) {
      try {
        await this.orgCtx.activate(qOrg);
      } catch {
        /* fall through to active context */
      }
    }
    this.orgId = this.orgCtx.activeOrganization()?.id ?? (qOrg || null);
    if (!this.orgId) {
      this.error = 'Activa una organización primero.';
      return;
    }
    this.loading = true;
    this.api.listPlans({ status: 'active' }).subscribe({
      next: (r) => {
        this.plans = r.items || [];
        this.loading = false;
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
        if (this.prices.length === 1) {
          this.form.patchValue({
            planPriceId: this.prices[0].id,
            billingCurrency: this.prices[0].currency || 'USD',
          });
        }
      },
      error: () => {
        this.prices = [];
      },
    });
  }

  formatPrice(pr: PlanPrice): string {
    const amount = Number(pr.amount);
    const money = Number.isFinite(amount) ? amount.toFixed(2) : String(pr.amount);
    const period = pr.billing_period === 'annual' ? 'yearly' : pr.billing_period;
    return `$${money} ${pr.currency || 'USD'} / ${period}`;
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
      this.success = 'Suscripción creada. Puedes continuar a facturación cuando corresponda.';
      this.router.navigate(['/subscriptions/overview']);
    };
    const fail = (e: { error?: { detail?: { message?: string } } }) => {
      this.error = e?.error?.detail?.message || 'No se pudo crear la suscripción (¿ya existe una activa?)';
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
