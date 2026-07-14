import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { forkJoin, of } from 'rxjs';
import { catchError, map, switchMap } from 'rxjs/operators';
import { SubscriptionsApiService } from '../services/subscriptions-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import {
  BillingPeriod,
  Plan,
  PlanFeature,
  PlanPrice,
  Subscription,
} from '../models/subscriptions.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';

type PeriodMode = 'monthly' | 'annual';

interface PlanCardVm {
  plan: Plan;
  price: PlanPrice | null;
  altPrice: PlanPrice | null;
  features: PlanFeature[];
  isCurrent: boolean;
  isRecommended: boolean;
}

@Component({
  selector: 'app-plans-catalog',
  standalone: true,
  imports: [CommonModule, RouterModule, TranslatePipe, LocaleMoneyPipe],
  template: `
    <div class="plans-catalog vx-enterprise--wide">
      <header class="vx-hero plans-hero">
        <div>
          <h1 class="vx-hero__title">{{ 'subscriptions.plans.title' | t:lang() }}</h1>
          <p class="vx-hero__subtitle">{{ 'subscriptions.plans.subtitle' | t:lang() }}</p>
          <div class="vx-hero__meta">
            @if (orgName()) {
              <span class="badge badge--active">{{ orgName() }}</span>
            }
            @if (currentPlanName()) {
              <span class="badge badge--current">
                {{ 'subscriptions.plans.currentPlanBadge' | t:lang() }}: {{ currentPlanName() }}
              </span>
            } @else {
              <span class="badge">{{ 'subscriptions.plans.noActiveSub' | t:lang() }}</span>
            }
          </div>
          <div class="billing-toggle" role="group" [attr.aria-label]="'subscriptions.plans.periodToggle' | t:lang()">
            <button
              type="button"
              class="billing-toggle__btn"
              [class.is-active]="period() === 'monthly'"
              (click)="setPeriod('monthly')"
            >
              {{ 'subscriptions.plans.monthly' | t:lang() }}
            </button>
            <button
              type="button"
              class="billing-toggle__btn"
              [class.is-active]="period() === 'annual'"
              (click)="setPeriod('annual')"
            >
              {{ 'subscriptions.plans.annual' | t:lang() }}
            </button>
            @if (annualSavingsLabel()) {
              <span class="billing-toggle__save">{{ annualSavingsLabel() }}</span>
            }
          </div>
        </div>
        <div class="vx-hero__actions">
          <a routerLink="/subscriptions/overview" class="btn btn--secondary">
            {{ 'subscriptions.plans.mySubscription' | t:lang() }}
          </a>
          <a routerLink="/subscriptions/select-plan" class="btn btn--primary">
            {{ 'subscriptions.plans.chooseCta' | t:lang() }}
          </a>
        </div>
      </header>

      @if (loading()) {
        <div class="vx-skel-block" aria-busy="true">
          <div class="vx-skel"></div>
          <div class="vx-skel"></div>
          <div class="vx-skel"></div>
        </div>
      } @else if (error()) {
        <div class="alert alert--danger" role="alert">{{ error() }}</div>
      } @else if (cards().length === 0) {
        <div class="empty-state">
          <p>{{ 'subscriptions.plans.empty' | t:lang() }}</p>
        </div>
      } @else {
        <div class="plans-grid">
          @for (card of cards(); track card.plan.id) {
            <article
              class="plan-card"
              [class.plan-card--recommended]="card.isRecommended"
              [class.plan-card--current]="card.isCurrent"
            >
              <div class="plan-card__ribbons">
                @if (card.isRecommended) {
                  <span class="badge badge--recommended">
                    {{ 'subscriptions.plans.recommended' | t:lang() }}
                  </span>
                }
                @if (card.isCurrent) {
                  <span class="badge badge--current">
                    {{ 'subscriptions.plans.currentPlanBadge' | t:lang() }}
                  </span>
                }
              </div>

              <h2 class="plan-card__name">{{ card.plan.display_name }}</h2>

              <div class="plan-card__price">
                @if (card.price) {
                  <span class="plan-card__amount">
                    {{ card.price.amount | localeMoney:card.price.currency }}
                  </span>
                  <span class="plan-card__period">
                    / {{ periodLabel(card.price.billing_period) }}
                  </span>
                  @if (period() === 'annual' && card.altPrice) {
                    <span class="plan-card__annual-note">
                      {{ 'subscriptions.plans.equivMonthly' | t:lang() }}
                      {{ monthlyEquivalent(card.price) | localeMoney:card.price.currency }}
                    </span>
                  }
                } @else {
                  <span class="plan-card__amount">{{ 'common.notAvailable' | t:lang() }}</span>
                  <span class="plan-card__period">{{ 'subscriptions.plans.priceUnavailable' | t:lang() }}</span>
                }
              </div>

              <p class="plan-card__desc">
                {{ card.plan.description || ('subscriptions.plans.noDescription' | t:lang()) }}
              </p>

              @if (card.features.length) {
                <ul class="plan-card__features">
                  @for (f of visibleFeatures(card.features); track f.id) {
                    <li>
                      <span>{{ featureLabel(f) }}</span>
                    </li>
                  }
                </ul>
              } @else {
                <p class="plan-card__meta">{{ 'subscriptions.plans.featuresUnavailable' | t:lang() }}</p>
              }

              @if (card.plan.trial_days_default > 0) {
                <div class="plan-card__meta">
                  {{ card.plan.trial_days_default }}
                  {{ 'subscriptions.plans.trialDays' | t:lang() }}
                </div>
              }

              <div class="plan-card__actions">
                @if (card.isCurrent) {
                  <button type="button" class="btn btn--secondary" disabled>
                    {{ 'subscriptions.plans.currentPlanCta' | t:lang() }}
                  </button>
                } @else if (!card.price) {
                  <p class="plan-card__unavailable">{{ 'subscriptions.plans.priceUnavailable' | t:lang() }}</p>
                  <a [routerLink]="['/subscriptions/plans', card.plan.id]" class="btn btn--ghost">
                    {{ 'subscriptions.plans.viewDetail' | t:lang() }}
                  </a>
                } @else if (isUpgrade(card)) {
                  <a
                    class="btn btn--primary"
                    [routerLink]="['/subscriptions/select-plan']"
                    [queryParams]="{ planId: card.plan.id, period: period() }"
                  >
                    {{ 'subscriptions.plans.upgradeCta' | t:lang() }}
                  </a>
                } @else if (isDowngrade(card)) {
                  <a
                    class="btn btn--secondary"
                    [routerLink]="['/subscriptions/select-plan']"
                    [queryParams]="{ planId: card.plan.id, period: period() }"
                  >
                    {{ 'subscriptions.plans.changeCta' | t:lang() }}
                  </a>
                  <p class="plan-card__meta">{{ 'subscriptions.plans.downgradeWarn' | t:lang() }}</p>
                } @else {
                  <a
                    class="btn btn--primary"
                    [routerLink]="['/subscriptions/select-plan']"
                    [queryParams]="{ planId: card.plan.id, period: period() }"
                  >
                    {{ 'subscriptions.plans.selectCta' | t:lang() }}
                  </a>
                }
                <a [routerLink]="['/subscriptions/plans', card.plan.id]" class="btn btn--ghost">
                  {{ 'subscriptions.plans.viewDetail' | t:lang() }}
                </a>
              </div>
            </article>
          }
        </div>
      }
    </div>
  `,
})
export class PlansCatalogPageComponent implements OnInit {
  private readonly i18n = inject(I18nService);
  readonly lang = this.i18n.lang;
  private readonly api = inject(SubscriptionsApiService);
  private readonly orgCtx = inject(OrganizationContextService);

  readonly period = signal<PeriodMode>('monthly');
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly plans = signal<Plan[]>([]);
  readonly pricesByPlan = signal<Record<number, PlanPrice[]>>({});
  readonly featuresByPlan = signal<Record<number, PlanFeature[]>>({});
  readonly currentSub = signal<Subscription | null>(null);

  readonly orgName = computed(() => this.orgCtx.activeOrganization()?.display_name ?? null);

  readonly currentPlanName = computed(() => {
    const sub = this.currentSub();
    if (!sub) return null;
    return this.plans().find((p) => p.id === sub.plan_id)?.display_name ?? null;
  });

  readonly cards = computed((): PlanCardVm[] => {
    const period = this.period();
    const ranked = [...this.plans()].sort((a, b) => a.sort_order - b.sort_order || a.id - b.id);
    const recommendedId = this.pickRecommendedId(ranked);
    const currentPlanId = this.currentSub()?.plan_id ?? null;

    return ranked.map((plan) => {
      const prices = this.pricesByPlan()[plan.id] ?? [];
      const price = this.pickPrice(prices, period);
      const altPrice = this.pickPrice(prices, period === 'monthly' ? 'annual' : 'monthly');
      return {
        plan,
        price,
        altPrice,
        features: this.featuresByPlan()[plan.id] ?? [],
        isCurrent: currentPlanId === plan.id,
        isRecommended: plan.id === recommendedId && currentPlanId !== plan.id,
      };
    });
  });

  readonly annualSavingsLabel = computed(() => {
    const savings = this.bestAnnualSavingsPercent();
    if (savings == null || savings <= 0) return null;
    return this.i18n.t('subscriptions.plans.saveUpTo', { pct: savings });
  });

  ngOnInit(): void {
    this.loading.set(true);
    this.error.set(null);
    const orgId = this.orgCtx.activeOrganization()?.id ?? null;

    this.api
      .listPlans({ status: 'active', limit: 50 })
      .pipe(
        switchMap((r) => {
          const items = [...(r.items || [])].sort((a, b) => a.sort_order - b.sort_order || a.id - b.id);
          this.plans.set(items);
          if (!items.length) {
            return of({ prices: {}, features: {}, sub: null as Subscription | null });
          }
          const priceCalls = items.map((p) =>
            this.api.listPlanPrices(p.id, true).pipe(catchError(() => of([] as PlanPrice[]))),
          );
          const featureCalls = items.map((p) =>
            this.api.listPlanFeatures(p.id).pipe(catchError(() => of([] as PlanFeature[]))),
          );
          const subCall = orgId
            ? this.api.listSubscriptions(orgId, { page: 1, limit: 10 }).pipe(
                map((sr) => {
                  const active = sr.items.find((s) =>
                    ['active', 'trialing', 'past_due'].includes(s.status),
                  );
                  return active ?? null;
                }),
                catchError(() => of(null)),
              )
            : of(null);

          return forkJoin({
            priceLists: forkJoin(priceCalls),
            featureLists: forkJoin(featureCalls),
            sub: subCall,
          }).pipe(
            map(({ priceLists, featureLists, sub }) => {
              const prices: Record<number, PlanPrice[]> = {};
              const features: Record<number, PlanFeature[]> = {};
              items.forEach((p, i) => {
                prices[p.id] = priceLists[i] || [];
                features[p.id] = (featureLists[i] || []).filter((f) => f.enabled);
              });
              return { prices, features, sub };
            }),
          );
        }),
      )
      .subscribe({
        next: ({ prices, features, sub }) => {
          this.pricesByPlan.set(prices);
          this.featuresByPlan.set(features);
          this.currentSub.set(sub);
          this.loading.set(false);
        },
        error: (e) => {
          this.error.set(e?.error?.detail?.message ?? this.i18n.t('subscriptions.plans.loadError'));
          this.loading.set(false);
        },
      });
  }

  setPeriod(mode: PeriodMode): void {
    this.period.set(mode);
  }

  periodLabel(period: BillingPeriod): string {
    if (period === 'annual') return this.i18n.t('subscriptions.plans.perYear');
    if (period === 'monthly') return this.i18n.t('subscriptions.plans.perMonth');
    return period;
  }

  monthlyEquivalent(price: PlanPrice): number {
    const amount = Number(price.amount);
    if (!Number.isFinite(amount)) return 0;
    return amount / 12;
  }

  visibleFeatures(features: PlanFeature[]): PlanFeature[] {
    return features.slice(0, 8);
  }

  featureLabel(f: PlanFeature): string {
    const code = f.feature_code.replace(/[_.]/g, ' ');
    if (f.limit_value != null) {
      return `${code} · ${f.limit_value}`;
    }
    return code;
  }

  isUpgrade(card: PlanCardVm): boolean {
    const current = this.currentSub();
    if (!current) return false;
    const cur = this.plans().find((p) => p.id === current.plan_id);
    if (!cur) return false;
    return card.plan.sort_order > cur.sort_order;
  }

  isDowngrade(card: PlanCardVm): boolean {
    const current = this.currentSub();
    if (!current) return false;
    const cur = this.plans().find((p) => p.id === current.plan_id);
    if (!cur) return false;
    return card.plan.sort_order < cur.sort_order;
  }

  private pickPrice(prices: PlanPrice[], period: PeriodMode): PlanPrice | null {
    const match = prices.find((p) => p.status === 'active' && p.billing_period === period);
    return match ?? null;
  }

  private pickRecommendedId(plans: Plan[]): number | null {
    if (!plans.length) return null;
    const professional = plans.find((p) => /professional|pro/i.test(p.code) || /professional|pro/i.test(p.display_name));
    if (professional) return professional.id;
    if (plans.length === 1) return plans[0].id;
    const mid = plans[Math.min(1, plans.length - 1)];
    return mid.id;
  }

  private bestAnnualSavingsPercent(): number | null {
    let best: number | null = null;
    for (const plan of this.plans()) {
      const prices = this.pricesByPlan()[plan.id] ?? [];
      const monthly = this.pickPrice(prices, 'monthly');
      const annual = this.pickPrice(prices, 'annual');
      if (!monthly || !annual) continue;
      const m = Number(monthly.amount);
      const a = Number(annual.amount);
      if (!Number.isFinite(m) || !Number.isFinite(a) || m <= 0) continue;
      const yearlyIfMonthly = m * 12;
      if (yearlyIfMonthly <= a) continue;
      const pct = Math.round(((yearlyIfMonthly - a) / yearlyIfMonthly) * 100);
      if (best == null || pct > best) best = pct;
    }
    return best;
  }
}
