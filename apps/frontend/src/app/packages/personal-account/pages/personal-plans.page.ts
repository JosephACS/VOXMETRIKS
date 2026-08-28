import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { catchError, finalize, forkJoin, of, timeout } from 'rxjs';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import { LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';
import {
  PersonalAccountApiService,
  PersonalPlan,
  PersonalSubscription,
} from '../services/personal-account-api.service';

@Component({
  selector: 'app-personal-plans-page',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe, LocaleMoneyPipe, ...ENTERPRISE_UI_IMPORTS],
  styleUrl: '../personal-account.css',
  template: `
    <div class="vx-enterprise personal-account-page">
      <app-enterprise-page-header
        [title]="'personal.plans.title' | t:lang()"
        [subtitle]="'personal.plans.subtitle' | t:lang()"
      />

      @if (loading()) {
        <div class="plan-loading" aria-busy="true" aria-live="polite">
          <div class="plan-loading__summary">
            <span></span><strong></strong><small></small>
          </div>
          <div class="plan-loading__grid">
            @for (_ of [1, 2]; track _) {
              <div class="plan-loading__card">
                <strong></strong><span></span><span></span><span></span><button disabled></button>
              </div>
            }
          </div>
        </div>
      } @else if (error()) {
        <app-enterprise-error-state [message]="error()!" (retry)="load()" />
      } @else {
        <section class="account-commerce-hub" aria-label="Plan y pagos">
          <div class="account-commerce-hub__summary">
            <span class="account-commerce-hub__eyebrow">{{ 'personal.accountHub.currentEyebrow' | t:lang() }}</span>
            <strong>{{ sub()?.plan_name || ('personal.accountHub.freePlan' | t:lang()) }}</strong>
            <span>{{ accountStatusHintKey() | t:lang() }}</span>
          </div>
          <div class="account-commerce-hub__actions">
            <a routerLink="/account/subscription" class="btn btn--primary">
              {{ 'personal.accountHub.manage' | t:lang() }}
            </a>
            <a routerLink="/account/billing" class="btn btn--secondary">
              {{ 'personal.accountHub.billing' | t:lang() }}
            </a>
          </div>
          <p class="account-commerce-hub__notice">
            <span aria-hidden="true">✓</span>
            {{ 'personal.accountHub.mockNotice' | t:lang() }}
          </p>
        </section>

        <div class="plan-picker-heading">
          <div>
            <h2>{{ 'personal.nav.plans' | t:lang() }}</h2>
            <p>{{ 'personal.plans.subtitle' | t:lang() }}</p>
          </div>
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
        </div>

        <div class="plan-grid">
          @for (p of plans(); track p.code) {
            <article
              class="plan-card"
              [class.plan-card--current]="isCurrent(p)"
              [class.plan-card--recommended]="p.code === 'premium_individual'"
            >
              <header>
                <h2>{{ p.display_name }}</h2>
                @if (isCurrent(p)) {
                  <span class="badge badge--current">{{ 'personal.plans.current' | t:lang() }}</span>
                }
                @if (p.code === 'premium_individual') {
                  <span class="badge badge--recommended">{{ 'personal.plans.recommended' | t:lang() }}</span>
                }
              </header>
              <p class="plan-price">
                @if (p.is_free) {
                  {{ 'personal.plans.freePrice' | t:lang() }}
                } @else {
                  {{ priceFor(p) | localeMoney: currencyFor(p) }}
                  <span class="muted"
                    >/
                    {{
                      period() === 'monthly'
                        ? ('personal.plans.month' | t:lang())
                        : ('personal.plans.year' | t:lang())
                    }}</span
                  >
                }
              </p>
              @if (!p.is_free && period() === 'annual' && annualSavings(p) > 0) {
                <span class="plan-save">
                  {{ 'personal.plans.saveAnnual' | t:lang() }}:
                  {{ annualSavings(p) | localeMoney: currencyFor(p) }}
                </span>
              }
              <p class="muted">{{ p.description }}</p>
              <ul class="plan-benefits">
                @for (f of displayFeatures(p).slice(0, 6); track f) {
                  <li>{{ f }}</li>
                }
              </ul>
              @if (!p.is_free && !isCurrent(p) && canManageBilling()) {
                <button
                  type="button"
                  class="btn btn--primary"
                  [disabled]="busy()"
                  (click)="checkout(p)"
                >
                  {{ 'personal.plans.cta' | t:lang() }}
                </button>
              } @else if (!p.is_free && !isCurrent(p)) {
                <p class="muted">{{ 'personal.billing.memberNoManage' | t:lang() }}</p>
              } @else if (isCurrent(p) && !p.is_free && canManageBilling()) {
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
  private router = inject(Router);
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
    forkJoin({
      plans: this.api.listPlans().pipe(timeout(8_000)),
      subscription: this.api.getSubscription().pipe(
        timeout(8_000),
        catchError(() => of(null)),
      ),
    }).pipe(finalize(() => this.loading.set(false))).subscribe({
      next: ({ plans, subscription }) => {
        this.plans.set(plans.items);
        this.sub.set(subscription);
      },
      error: () => {
        this.error.set(this.i18n.t('common.loadFailed'));
      },
    });
  }

  isCurrent(p: PersonalPlan): boolean {
    const sub = this.sub();
    if (!sub) return false;
    const status = (sub.status || '').toLowerCase();
    const keepsAccess = ['active', 'trialing', 'processing', 'past_due', 'canceling'].includes(status);
    if (!keepsAccess) return false;
    if (sub.plan_code === p.code) return true;
    return this.foldPlanName(sub.plan_name) === this.foldPlanName(p.display_name);
  }

  private foldPlanName(value: string | null | undefined): string {
    return (value || '')
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9]+/gi, '')
      .toLowerCase();
  }

  accountStatusHintKey(): string {
    return (this.sub()?.status || '').toLowerCase() === 'processing'
      ? 'personal.accountHub.processingHint'
      : 'personal.accountHub.activeHint';
  }

  canManageBilling(): boolean {
    const sub = this.sub();
    return !sub || (sub.can_manage_billing !== false && sub.household_role !== 'member');
  }

  priceFor(p: PersonalPlan): number {
    const pr = p.prices.find((x) => x.billing_period === this.period());
    return pr?.amount ?? p.prices[0]?.amount ?? 0;
  }

  currencyFor(p: PersonalPlan): string {
    const pr = p.prices.find((x) => x.billing_period === this.period());
    return (pr?.currency || p.prices[0]?.currency || 'USD').toUpperCase();
  }

  /** Approx. savings vs 12× monthly when viewing annual. */
  annualSavings(p: PersonalPlan): number {
    const monthly = p.prices.find((x) => x.billing_period === 'monthly')?.amount;
    const annual = p.prices.find((x) => x.billing_period === 'annual')?.amount;
    if (monthly == null || annual == null) return 0;
    return Math.max(0, Number(monthly) * 12 - Number(annual));
  }

  displayFeatures(p: PersonalPlan): string[] {
    return p.features
      .filter((f) => f.enabled)
      .map((f) => {
        const key = `personal.feature.${f.feature_code}`;
        const t = this.i18n.t(key);
        const missing = this.i18n.t('common.missingTranslation');
        if (t && t !== key && t !== missing) return t;
        if (f.limit_value != null) {
          return this.i18n.t('personal.feature.limitGeneric', {
            code: f.feature_code.replace(/_/g, ' '),
            n: f.limit_value,
          });
        }
        return f.feature_code.replace(/_/g, ' ');
      });
  }

  checkout(p: PersonalPlan): void {
    if (!this.canManageBilling()) return;
    this.success.set(null);
    // Free plans stay on the ensure/legacy path when exposed; paid plans use Spec 052 journey.
    if (p.is_free) {
      this.busy.set(true);
      this.api.checkout(p.code, 'monthly').subscribe({
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
      return;
    }
    void this.router.navigate(['/account/checkout'], {
      queryParams: {
        plan_code: p.code,
        billing_period: this.period(),
      },
    });
  }
}
