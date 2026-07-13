import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { SubscriptionsApiService } from '../services/subscriptions-api.service';
import { Plan } from '../models/subscriptions.models';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
@Component({
  selector: 'app-plans-catalog',
  standalone: true,
  imports: [CommonModule, RouterModule, TranslatePipe],
  template: `
    <div class="plans-catalog">
      <div class="page-header">
        <h1>{{ 'subscriptions.plans.title' | t:lang() }}</h1>
        <p>Planes disponibles para organizaciones</p>
      </div>

      @if (plans.length > 0) {
        <div class="plans-grid">
          @for (plan of plans; track plan.id) {
            <div class="plan-card"
                 [class]="'plan-card--' + plan.status">
              <div class="plan-card__header">
                <h2>{{ plan.display_name }}</h2>
                <span class="badge" [class]="'badge--' + plan.status">{{ plan.status }}</span>
              </div>
              @if (plan.description) {
                <p class="plan-card__desc">{{ plan.description }}</p>
              }
              <div class="plan-card__meta">
                @if (plan.trial_days_default > 0) {
                  <span>
                    {{ plan.trial_days_default }} días trial
                  </span>
                }
              </div>
              <div class="plan-card__actions">
                <a [routerLink]="['/subscriptions/plans', plan.id]" class="btn btn--primary">Ver detalle</a>
              </div>
            </div>
          }
        </div>
      } @else {
        <p>No hay planes disponibles.</p>
      }

      @if (loading) {
        <div class="loading">{{ 'common.loading' | t:lang() }}</div>
      }
      @if (error) {
        <div class="error">{{ error }}</div>
      }
    </div>
  `,
})
export class PlansCatalogPageComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private readonly api = inject(SubscriptionsApiService);

  plans: Plan[] = [];
  loading = false;
  error: string | null = null;

  ngOnInit(): void {
    this.loading = true;
    this.api.listPlans({ status: 'active' }).subscribe({
      next: (r) => {
        this.plans = r.items;
        this.loading = false;
      },
      error: (e) => {
        this.error = e?.error?.detail?.message ?? 'Error al cargar planes';
        this.loading = false;
      },
    });
  }
}
