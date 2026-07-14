import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import {
  PersonalAccountApiService,
  PersonalPlan,
  PersonalSubscription,
} from '../services/personal-account-api.service';

@Component({
  selector: 'app-personal-plans-page',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  styleUrl: '../personal-account.css',
  template: `
    <div class="vx-enterprise personal-account-page">
      <app-enterprise-page-header
        [title]="'personal.plans.title' | t:lang()"
        [subtitle]="'personal.plans.subtitle' | t:lang()"
      >
        <a routerLink="/account/subscription" class="btn btn--secondary">{{
          'personal.nav.subscription' | t:lang()
        }}</a>
      </app-enterprise-page-header>

      <div class="period-toggle" role="group">
        <button
          type="button"
          class="btn"
          [class.btn--primary]="period() === 'monthly'"
          [class.btn--secondary]="period() !== 'monthly'"
          (click)="period.set('monthly')"
        >
          {{ 'personal.plans.monthly' | t:lang() }}
        </button>
        <button
          type="button"
          class="btn"
          [class.btn--primary]="period() === 'annual'"
          [class.btn--secondary]="period() !== 'annual'"
          (click)="period.set('annual')"
        >
          {{ 'personal.plans.annual' | t:lang() }}
        </button>
      </div>

      @if (loading()) {
        <app-enterprise-loading-skeleton [rows]="3" />
      } @else if (error()) {
        <app-enterprise-error-state [message]="error()!" (retry)="load()" />
      } @else {
        <div class="plan-grid">
          @for (p of plans(); track p.code) {
            <article class="plan-card" [class.plan-card--current]="isCurrent(p)">
              <header>
                <h2>{{ p.display_name }}</h2>
                @if (isCurrent(p)) {
                  <span class="badge badge--ok">{{ 'personal.plans.current' | t:lang() }}</span>
                }
                @if (p.code === 'premium_individual') {
                  <span class="badge badge--mock">{{ 'personal.plans.recommended' | t:lang() }}</span>
                }
              </header>
              <p class="plan-price">
                @if (p.is_free) {
                  {{ 'personal.plans.freePrice' | t:lang() }}
                } @else {
                  {{ priceFor(p) | number: '1.2-2' }} USD
                  <span class="muted">/ {{ period() === 'monthly' ? ('personal.plans.month' | t:lang()) : ('personal.plans.year' | t:lang()) }}</span>
                }
              </p>
              <p class="muted">{{ p.description }}</p>
              <ul class="plan-benefits">
                @for (f of displayFeatures(p); track f) {
                  <li>{{ f }}</li>
                }
              </ul>
              @if (!p.is_free && !isCurrent(p)) {
                <button
                  type="button"
                  class="btn btn--primary"
                  [disabled]="busy()"
                  (click)="checkout(p)"
                >
                  {{ 'personal.plans.cta' | t:lang() }}
                </button>
              } @else if (isCurrent(p) && !p.is_free) {
                <a routerLink="/account/subscription" class="btn btn--secondary">{{
                  'personal.plans.manage' | t:lang()
                }}</a>
              }
            </article>
          }
        </div>
      }

      @if (success()) {
        <div class="alert alert--ok" role="status">{{ success() }}</div>
      }
    </div>
  `,
})
export class PersonalPlansPage implements OnInit {
  private api = inject(PersonalAccountApiService);
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  plans = signal<PersonalPlan[]>([]);
  sub = signal<PersonalSubscription | null>(null);
  period = signal<'monthly' | 'annual'>('monthly');
  loading = signal(true);
  busy = signal(false);
  error = signal<string | null>(null);
  success = signal<string | null>(null);

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.error.set(null);
    this.api.listPlans().subscribe({
      next: (res) => {
        this.plans.set(res.items);
        this.api.getSubscription().subscribe({
          next: (s) => {
            this.sub.set(s);
            this.loading.set(false);
          },
          error: () => {
            this.loading.set(false);
          },
        });
      },
      error: () => {
        this.error.set(this.i18n.t('common.loadFailed'));
        this.loading.set(false);
      },
    });
  }

  isCurrent(p: PersonalPlan): boolean {
    return this.sub()?.plan_code === p.code && this.sub()?.status === 'active';
  }

  priceFor(p: PersonalPlan): number {
    const pr = p.prices.find((x) => x.billing_period === this.period());
    return pr?.amount ?? p.prices[0]?.amount ?? 0;
  }

  displayFeatures(p: PersonalPlan): string[] {
    return p.features
      .filter((f) => f.enabled)
      .map((f) => {
        const key = `personal.feature.${f.feature_code}`;
        const t = this.i18n.t(key);
        if (t !== key) return t;
        if (f.limit_value != null) return `${f.feature_code}: ${f.limit_value}`;
        return f.feature_code;
      });
  }

  checkout(p: PersonalPlan): void {
    this.busy.set(true);
    this.success.set(null);
    const period = p.is_free ? 'monthly' : this.period();
    this.api.checkout(p.code, period).subscribe({
      next: (c) => {
        this.api.simulatePayment(c.attempt_id, 'succeeded').subscribe({
          next: () => {
            this.success.set(this.i18n.t('personal.plans.activated'));
            this.busy.set(false);
            this.load();
          },
          error: () => {
            this.error.set(this.i18n.t('common.actionFailed'));
            this.busy.set(false);
          },
        });
      },
      error: () => {
        this.error.set(this.i18n.t('common.actionFailed'));
        this.busy.set(false);
      },
    });
  }
}
