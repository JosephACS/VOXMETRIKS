import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { switchMap } from 'rxjs';
import { SubscriptionsApiService } from '../services/subscriptions-api.service';
import { Plan, PlanPrice, PlanFeature } from '../models/subscriptions.models';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
@Component({
  selector: 'app-plan-detail',
  standalone: true,
  imports: [CommonModule, RouterModule, TranslatePipe],
  template: `
    @if (plan) {
      <div class="vx-enterprise plan-detail">
        <div class="page-header">
          <h1>{{ plan.display_name }}
            <span class="badge" [class]="'badge--' + plan.status">{{ plan.status }}</span>
          </h1>
          @if (plan.description) {
            <p>{{ plan.description }}</p>
          }
          @if (plan.trial_days_default > 0) {
            <p>
              {{ 'subscriptions.trial.label' | t:lang() }}: {{ plan.trial_days_default }}
              {{ 'subscriptions.trial.days' | t:lang() }}
            </p>
          }
        </div>

        <section class="plan-prices">
          <h2>Precios</h2>
          @if (prices.length > 0) {
            <table>
              <thead>
                <tr>
                  <th>Moneda</th>
                  <th>Periodo</th>
                  <th>Monto</th>
                  <th>Estado</th>
                </tr>
              </thead>
              <tbody>
                @for (price of prices; track price.id) {
                  <tr>
                    <td>{{ price.currency }}</td>
                    <td>{{ price.billing_period }}</td>
                    <td>{{ price.amount }}</td>
                    <td>{{ price.status }}</td>
                  </tr>
                }
              </tbody>
            </table>
          } @else {
            <p>{{ 'subscriptions.planDetail.noPrices' | t:lang() }}.</p>
          }
        </section>

        <section class="plan-features">
          <h2>{{ 'subscriptions.planDetail.features' | t:lang() }}</h2>
          @if (features.length > 0) {
            <ul>
              @for (f of features; track f.feature_code) {
                <li>
                  <strong>{{ featureName(f.feature_code) }}</strong>
                  @if (f.limit_value !== null) {
                    <span> — {{ f.limit_value }}</span>
                  }
                  @if (!f.enabled) {
                    <span class="badge badge--archived">{{ 'common.disabled' | t:lang() }}</span>
                  }
                </li>
              }
            </ul>
          } @else {
            <p>{{ 'subscriptions.planDetail.noFeatures' | t:lang() }}</p>
          }
        </section>
      </div>
    }

    @if (loading) {
      <div>{{ 'common.loading' | t:lang() }}</div>
    }
    @if (error) {
      <div class="error">{{ error }}</div>
    }
  `,
})
export class PlanDetailPageComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private readonly api = inject(SubscriptionsApiService);
  private readonly route = inject(ActivatedRoute);

  plan: Plan | null = null;
  prices: PlanPrice[] = [];
  features: PlanFeature[] = [];
  loading = false;
  error: string | null = null;

  ngOnInit(): void {
    this.loading = true;
    this.route.paramMap
      .pipe(switchMap((params) => this.api.getPlan(Number(params.get('id')))))
      .subscribe({
        next: (plan) => {
          this.plan = plan;
          this.loadPricesAndFeatures(plan.id);
        },
        error: (e) => {
          this.error = e?.error?.detail?.message ?? 'Plan no encontrado';
          this.loading = false;
        },
      });
  }

  private loadPricesAndFeatures(planId: number): void {
    this.api.listPlanPrices(planId).subscribe({
      next: (prices) => (this.prices = prices),
      error: () => {
        this.prices = [];
      },
    });
    this.api.listPlanFeatures(planId).subscribe({
      next: (features) => {
        this.features = features;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      },
    });
  }

  featureName(code: string): string {
    const key = `subscriptions.feature.${code}`;
    const t = this.i18n.t(key);
    const missing = this.i18n.t('common.missingTranslation');
    if (t && t !== key && t !== missing) return t;
    return code.replace(/[_.]/g, ' ');
  }
}
