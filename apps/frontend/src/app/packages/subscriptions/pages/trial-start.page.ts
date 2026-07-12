import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { SubscriptionsApiService } from '../services/subscriptions-api.service';
import { Plan, PlanPrice } from '../models/subscriptions.models';

@Component({
  selector: 'app-trial-start',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="trial-start">
      <h1 i18n="subscriptions.trial.title">Iniciar Trial</h1>

      <form [formGroup]="form" (ngSubmit)="onSubmit()">
        <div class="form-field">
          <label i18n="subscriptions.trial.plan">Plan</label>
          <select formControlName="planId" (change)="onPlanChange()">
            <option value="" i18n="common.selectOption">Seleccionar...</option>
            @for (p of plans; track p.id) {
              <option [value]="p.id">
                {{ p.display_name }} ({{ p.trial_days_default }} días trial)
              </option>
            }
          </select>
        </div>

        @if (prices.length > 0) {
          <div class="form-field">
            <label i18n="subscriptions.trial.price">Precio (opcional)</label>
            <select formControlName="planPriceId">
              <option value="" i18n="common.none">Ninguno</option>
              @for (p of prices; track p.id) {
                <option [value]="p.id">
                  {{ p.currency }} {{ p.amount }} / {{ p.billing_period }}
                </option>
              }
            </select>
          </div>
        }

        <div class="form-field">
          <label i18n="subscriptions.trial.currency">Moneda</label>
          <input formControlName="billingCurrency" placeholder="USD" maxlength="3" />
        </div>

        <div class="form-actions">
          <button type="submit" [disabled]="form.invalid || saving" class="btn btn--primary"
                  i18n="subscriptions.trial.submit">Iniciar Trial</button>
        </div>

        @if (error) {
          <div class="error">{{ error }}</div>
        }
      </form>
    </div>
  `,
})
export class TrialStartPageComponent implements OnInit {
  private readonly api = inject(SubscriptionsApiService);
  private readonly fb = inject(FormBuilder);
  private readonly router = inject(Router);

  organizationId = 0;
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
    this.api.listPlans({ status: 'active' }).subscribe({
      next: (r) => (this.plans = r.items),
      error: (e) => {
        this.error = e?.error?.detail?.message ?? 'Error al cargar planes';
      },
    });
  }

  onPlanChange(): void {
    const planId = Number(this.form.value.planId);
    if (!planId) return;
    this.api.listPlanPrices(planId).subscribe({
      next: (prices) => (this.prices = prices),
      error: (e) => {
        this.error = e?.error?.detail?.message ?? 'Error al cargar precios';
        this.prices = [];
      },
    });
  }

  onSubmit(): void {
    if (this.form.invalid) return;
    this.saving = true;
    this.error = null;
    const { planId, planPriceId, billingCurrency } = this.form.value;
    this.api.startTrial(this.organizationId, {
      organization_id: this.organizationId,
      plan_id: planId!,
      plan_price_id: planPriceId ?? undefined,
      billing_currency: billingCurrency!,
    }).subscribe({
      next: () => this.router.navigate(['/subscriptions']),
      error: (e) => {
        this.error = e?.error?.detail?.message ?? 'Error al iniciar trial';
        this.saving = false;
      },
    });
  }
}
