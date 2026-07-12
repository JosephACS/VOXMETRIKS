import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { switchMap } from 'rxjs';
import { SubscriptionsApiService } from '../services/subscriptions-api.service';
import { Plan, PlanPrice, PlanFeature } from '../models/subscriptions.models';

@Component({
  selector: 'app-plan-detail',
  standalone: true,
  imports: [CommonModule, RouterModule],
  template: `
    @if (plan) {
      <div class="plan-detail">
        <div class="page-header">
          <h1>{{ plan.display_name }}
            <span class="badge" [class]="'badge--' + plan.status">{{ plan.status }}</span>
          </h1>
          @if (plan.description) {
            <p>{{ plan.description }}</p>
          }
          @if (plan.trial_days_default > 0) {
            <p>
              Trial: {{ plan.trial_days_default }} días
            </p>
          }
        </div>

        <section class="plan-prices">
          <h2 i18n="subscriptions.plan.prices">Precios</h2>
          @if (prices.length > 0) {
            <table>
              <thead>
                <tr>
                  <th i18n="subscriptions.price.currency">Moneda</th>
                  <th i18n="subscriptions.price.period">Periodo</th>
                  <th i18n="subscriptions.price.amount">Monto</th>
                  <th i18n="subscriptions.price.status">Estado</th>
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
            <p i18n="subscriptions.prices.empty">Sin precios configurados.</p>
          }
        </section>

        <section class="plan-features">
          <h2 i18n="subscriptions.plan.features">Características</h2>
          @if (features.length > 0) {
            <ul>
              @for (f of features; track f.feature_code) {
                <li>
                  <strong>{{ f.feature_code }}</strong>
                  @if (f.limit_value !== null) {
                    <span> — límite: {{ f.limit_value }}</span>
                  }
                  @if (!f.enabled) {
                    <span class="badge badge--archived"> deshabilitado</span>
                  }
                </li>
              }
            </ul>
          } @else {
            <p i18n="subscriptions.features.empty">Sin características configuradas.</p>
          }
        </section>
      </div>
    }

    @if (loading) {
      <div i18n="common.loading">Cargando...</div>
    }
    @if (error) {
      <div class="error">{{ error }}</div>
    }
  `,
})
export class PlanDetailPageComponent implements OnInit {
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
}
