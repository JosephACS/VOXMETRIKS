import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { forkJoin, of } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { SubscriptionsApiService } from '../services/subscriptions-api.service';
import { BillingApiService } from '../../billing/services/billing-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import {
  Addon,
  AccessStateInfo,
  Plan,
  PlanPrice,
  Subscription,
  SubscriptionAddon,
  SubscriptionEntitlement,
  UsageRecord,
} from '../models/subscriptions.models';
import { Invoice } from '../../billing/models/billing.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { LocaleDatePipe, LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

type OverviewTab = 'usage' | 'addons' | 'invoices';

@Component({
  selector: 'app-subscription-overview',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    TranslatePipe,
    LocaleDatePipe,
    LocaleMoneyPipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  template: `
    <div class="subscription-overview vx-enterprise">
      <header class="vx-hero">
        <div>
          <h1 class="vx-hero__title">{{ 'subscriptions.overview.title' | t:lang() }}</h1>
          <p class="vx-hero__subtitle">{{ 'subscriptions.overview.subtitle' | t:lang() }}</p>
          <div class="vx-hero__meta">
            @if (orgName) {
              <span class="badge badge--active">{{ orgName }}</span>
            }
            @if (planName) {
              <span class="badge badge--current">{{ planName }}</span>
            }
          </div>
        </div>
        <div class="vx-hero__actions">
          <a routerLink="/subscriptions/plans" class="btn btn--secondary">
            {{ 'subscriptions.overview.changePlan' | t:lang() }}
          </a>
          @if (!subscription) {
            <a routerLink="/subscriptions/select-plan" class="btn btn--primary">
              {{ 'subscriptions.plans.chooseCta' | t:lang() }}
            </a>
          }
        </div>
      </header>

      @if (!organizationId) {
        <app-enterprise-org-required />
      } @else if (loading) {
        <app-enterprise-loading-skeleton [rows]="4" />
      } @else if (error) {
        <app-enterprise-error-state [message]="error" (retry)="reload()" />
      } @else if (subscription) {
        @if (accessState && accessState.access_state !== 'full') {
          <div class="access-banner" [class]="'access-banner--' + accessState.access_state">
            @switch (accessState.access_state) {
              @case ('limited') {
                <span
                  >{{ 'subscriptions.overview.limited' | t:lang() }}.
                  {{ accessState.reason }}</span
                >
              }
              @case ('blocked') {
                <span>{{ accessState.reason }}</span>
              }
            }
          </div>
        }

        <app-enterprise-section-card [title]="'subscriptions.overview.summary' | t:lang()">
          <dl class="sub-summary">
            <div>
              <dt>{{ 'subscriptions.overview.field.plan' | t:lang() }}</dt>
              <dd>{{ planName || ('subscriptions.overview.priceUnavailable' | t:lang()) }}</dd>
            </div>
            <div>
              <dt>{{ 'subscriptions.overview.field.price' | t:lang() }}</dt>
              <dd>
                @if (priceAmount != null) {
                  {{ priceAmount | localeMoney: priceCurrency }}
                } @else {
                  {{ 'subscriptions.overview.priceUnavailable' | t:lang() }}
                }
              </dd>
            </div>
            <div>
              <dt>{{ 'subscriptions.overview.field.period' | t:lang() }}</dt>
              <dd>{{ periodLabel() }}</dd>
            </div>
            <div>
              <dt>{{ 'subscriptions.overview.field.status' | t:lang() }}</dt>
              <dd>
                <app-enterprise-status-badge [status]="subscription.status" />
                @if (subscription.cancel_at_period_end) {
                  <span class="badge badge--archived">{{
                    'subscriptions.overview.cancelAtPeriodEnd' | t:lang()
                  }}</span>
                }
              </dd>
            </div>
            <div>
              <dt>{{ 'subscriptions.overview.field.access' | t:lang() }}</dt>
              <dd>
                <app-enterprise-status-badge [status]="subscription.access_state" />
              </dd>
            </div>
            <div>
              <dt>{{ 'subscriptions.overview.field.periodStart' | t:lang() }}</dt>
              <dd>
                @if (subscription.current_period_start) {
                  {{ subscription.current_period_start | localeDate }}
                } @else {
                  {{ 'subscriptions.overview.periodStartUnset' | t:lang() }}
                }
              </dd>
            </div>
            <div>
              <dt>{{ 'subscriptions.overview.field.renewal' | t:lang() }}</dt>
              <dd>
                @if (subscription.current_period_end) {
                  {{ subscription.current_period_end | localeDate }}
                } @else {
                  {{ 'subscriptions.overview.renewalUnset' | t:lang() }}
                }
              </dd>
            </div>
            <div>
              <dt>{{ 'subscriptions.overview.field.currency' | t:lang() }}</dt>
              <dd>{{ subscription.billing_currency || ('subscriptions.overview.currencyUnset' | t:lang()) }}</dd>
            </div>
            <div>
              <dt>{{ 'subscriptions.overview.field.organization' | t:lang() }}</dt>
              <dd>{{ orgName || ('common.notAvailable' | t:lang()) }}</dd>
            </div>
          </dl>

          <div class="sub-card__actions">
            <a routerLink="/subscriptions/plans" class="btn btn--secondary">{{
              'subscriptions.overview.changePlan' | t:lang()
            }}</a>
            <button type="button" class="btn btn--secondary" (click)="setTab('addons')">
              {{ 'subscriptions.overview.manageAddons' | t:lang() }}
            </button>
            <button type="button" class="btn btn--secondary" (click)="setTab('invoices')">
              {{ 'subscriptions.overview.invoices' | t:lang() }}
            </button>
            <a
              [routerLink]="['/subscriptions', subscription.id, 'cancel']"
              class="btn btn--danger"
              style="margin-left: auto"
            >
              {{ 'subscriptions.cancel.title' | t:lang() }}
            </a>
          </div>
        </app-enterprise-section-card>

        <app-enterprise-section-card [title]="'subscriptions.overview.entitlements' | t:lang()">
          @if (entitlementsLoading) {
            <app-enterprise-loading-skeleton [rows]="2" />
          } @else if (entitlementsError) {
            <app-enterprise-error-state [message]="entitlementsError" (retry)="loadEntitlements()" />
          } @else if (entitlements.length === 0) {
            <app-enterprise-empty-state
              [title]="'subscriptions.overview.entitlementsEmptyTitle' | t:lang()"
              [description]="'subscriptions.overview.entitlementsEmptyBody' | t:lang()"
            />
          } @else {
            <div class="entitlement-grid">
              @for (e of entitlements; track e.feature_code) {
                <article class="entitlement-card">
                  <h3>{{ featureName(e.feature_code) }}</h3>
                  <p class="muted">{{ featureDescription(e.feature_code) }}</p>
                  <dl>
                    <div>
                      <dt>{{ 'subscriptions.overview.ent.limit' | t:lang() }}</dt>
                      <dd>{{ limitLabel(e) }}</dd>
                    </div>
                    <div>
                      <dt>{{ 'subscriptions.overview.ent.usage' | t:lang() }}</dt>
                      <dd>{{ usageLabel(e) }}</dd>
                    </div>
                    <div>
                      <dt>{{ 'subscriptions.overview.ent.remaining' | t:lang() }}</dt>
                      <dd>{{ remainingLabel(e) }}</dd>
                    </div>
                    <div>
                      <dt>{{ 'common.status' | t:lang() }}</dt>
                      <dd>
                        <app-enterprise-status-badge [status]="e.enabled ? 'active' : 'closed'" />
                      </dd>
                    </div>
                  </dl>
                </article>
              }
            </div>
          }
        </app-enterprise-section-card>

        <div class="overview-tabs" role="tablist">
          <button
            type="button"
            class="overview-tab"
            role="tab"
            [class.is-active]="tab() === 'usage'"
            [attr.aria-selected]="tab() === 'usage'"
            (click)="setTab('usage')"
          >
            {{ 'subscriptions.overview.tab.usage' | t:lang() }}
          </button>
          <button
            type="button"
            class="overview-tab"
            role="tab"
            [class.is-active]="tab() === 'addons'"
            [attr.aria-selected]="tab() === 'addons'"
            (click)="setTab('addons')"
          >
            {{ 'subscriptions.overview.tab.addons' | t:lang() }}
          </button>
          <button
            type="button"
            class="overview-tab"
            role="tab"
            [class.is-active]="tab() === 'invoices'"
            [attr.aria-selected]="tab() === 'invoices'"
            (click)="setTab('invoices')"
          >
            {{ 'subscriptions.overview.tab.invoices' | t:lang() }}
          </button>
        </div>

        <app-enterprise-section-card [title]="tabTitle()">
          @if (tab() === 'usage') {
            @if (tabLoading()) {
              <app-enterprise-loading-skeleton [rows]="2" />
            } @else if (tabError()) {
              <app-enterprise-error-state [message]="tabError()!" (retry)="loadTabData()" />
            } @else if (usageRecords.length === 0) {
              <app-enterprise-empty-state
                [title]="'subscriptions.overview.usageEmptyTitle' | t:lang()"
                [description]="'subscriptions.overview.usageEmptyBody' | t:lang()"
              />
            } @else {
              <app-enterprise-data-table>
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>{{ 'subscriptions.overview.ent.feature' | t:lang() }}</th>
                      <th>{{ 'subscriptions.overview.ent.usage' | t:lang() }}</th>
                      <th>{{ 'subscriptions.overview.field.period' | t:lang() }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    @for (r of usageRecords; track r.id) {
                      <tr>
                        <td>{{ featureName(r.feature_code) }}</td>
                        <td>{{ r.quantity }}</td>
                        <td>{{ r.period_start | localeDate }} — {{ r.period_end | localeDate }}</td>
                      </tr>
                    }
                  </tbody>
                </table>
              </app-enterprise-data-table>
            }
          }

          @if (tab() === 'addons') {
            @if (tabLoading()) {
              <app-enterprise-loading-skeleton [rows]="2" />
            } @else if (tabError()) {
              <app-enterprise-error-state [message]="tabError()!" (retry)="loadTabData()" />
            } @else {
              <h3 class="subhead">{{ 'subscriptions.overview.addonsActive' | t:lang() }}</h3>
              @if (activeAddons.length === 0) {
                <app-enterprise-empty-state
                  [title]="'subscriptions.overview.addonsEmptyTitle' | t:lang()"
                  [description]="'subscriptions.overview.addonsEmptyBody' | t:lang()"
                />
              } @else {
                <ul class="ent-list">
                  @for (sa of activeAddons; track sa.id) {
                    <li>
                      {{ addonName(sa.addon_id) }}
                      <app-enterprise-status-badge [status]="sa.status" />
                    </li>
                  }
                </ul>
              }
              <div class="form-grid__actions" style="margin-top: 1rem">
                <a
                  [routerLink]="['/subscriptions', subscription.id, 'addons']"
                  class="btn btn--secondary"
                >
                  {{ 'subscriptions.overview.manageAddons' | t:lang() }}
                </a>
              </div>
            }
          }

          @if (tab() === 'invoices') {
            @if (tabLoading()) {
              <app-enterprise-loading-skeleton [rows]="2" />
            } @else if (tabError()) {
              <app-enterprise-error-state [message]="tabError()!" (retry)="loadTabData()" />
            } @else if (invoices.length === 0) {
              <app-enterprise-empty-state
                [title]="'subscriptions.overview.invoicesEmptyTitle' | t:lang()"
                [description]="'subscriptions.overview.invoicesEmptyBody' | t:lang()"
                [ctaLabel]="'subscriptions.overview.invoices' | t:lang()"
                ctaLink="/billing/invoices" />
            } @else {
              <app-enterprise-data-table>
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>{{ 'billing.invoices.number' | t:lang() }}</th>
                      <th>{{ 'common.status' | t:lang() }}</th>
                      <th>{{ 'common.amount' | t:lang() }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    @for (inv of invoices; track inv.id) {
                      <tr>
                        <td>
                          <a [routerLink]="['/billing/invoices', inv.id]">{{
                            inv.invoice_number || inv.id
                          }}</a>
                        </td>
                        <td><app-enterprise-status-badge [status]="inv.status" /></td>
                        <td>{{ inv.total | localeMoney: inv.currency }}</td>
                      </tr>
                    }
                  </tbody>
                </table>
              </app-enterprise-data-table>
            }
          }
        </app-enterprise-section-card>
      } @else {
        <app-enterprise-empty-state
          [title]="'subscriptions.overview.noSubTitle' | t:lang()"
          [description]="'subscriptions.overview.noSubBody' | t:lang()"
          [ctaLabel]="'subscriptions.plans.chooseCta' | t:lang()"
          ctaLink="/subscriptions/plans" />
      }
    </div>
  `,
  styles: [
    `
      .sub-summary {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 0.85rem 1rem;
        margin: 0 0 1.1rem;
      }
      .sub-summary dt {
        margin: 0;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: var(--text-muted);
      }
      .sub-summary dd {
        margin: 0.2rem 0 0;
        font-weight: 600;
        font-variant-numeric: tabular-nums;
      }
      .entitlement-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 0.85rem;
      }
      .entitlement-card {
        border: 1px solid var(--border);
        border-radius: 0.85rem;
        padding: 0.95rem 1rem;
        background: rgba(255, 255, 255, 0.03);
      }
      .entitlement-card h3 {
        margin: 0 0 0.25rem;
        font-size: 0.95rem;
      }
      .entitlement-card dl {
        display: grid;
        gap: 0.45rem;
        margin: 0.75rem 0 0;
      }
      .entitlement-card dt {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: var(--text-muted);
      }
      .entitlement-card dd {
        margin: 0.1rem 0 0;
        font-variant-numeric: tabular-nums;
      }
      .overview-tabs {
        display: flex;
        gap: 0.35rem;
        margin: 1.25rem 0 0.85rem;
        padding: 0.3rem;
        border-radius: 0.85rem;
        border: 1px solid var(--border);
        background: rgba(255, 255, 255, 0.03);
        flex-wrap: wrap;
      }
      .overview-tab {
        appearance: none;
        border: none;
        background: transparent;
        color: var(--text-muted);
        font: inherit;
        font-weight: 600;
        font-size: 0.875rem;
        padding: 0.55rem 0.95rem;
        border-radius: 0.65rem;
        cursor: pointer;
      }
      .overview-tab.is-active {
        background: rgba(30, 216, 150, 0.14);
        color: var(--accent);
      }
      .subhead {
        margin: 0 0 0.75rem;
        font-size: 0.9rem;
      }
      .sub-card__actions {
        display: flex;
        flex-wrap: wrap;
        gap: 0.55rem;
        align-items: center;
      }
    `,
  ],
})
export class SubscriptionOverviewPageComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private readonly api = inject(SubscriptionsApiService);
  private readonly billing = inject(BillingApiService);
  private readonly orgCtx = inject(OrganizationContextService);

  organizationId: number | null = null;
  orgName: string | null = null;
  planName: string | null = null;
  priceAmount: number | null = null;
  priceCurrency = 'USD';
  pricePeriod: string | null = null;
  subscription: Subscription | null = null;
  entitlements: SubscriptionEntitlement[] = [];
  accessState: AccessStateInfo | null = null;
  loading = false;
  error: string | null = null;
  entitlementsLoading = false;
  entitlementsError: string | null = null;

  readonly tab = signal<OverviewTab>('usage');
  readonly tabLoading = signal(false);
  readonly tabError = signal<string | null>(null);
  private loadedTabs = new Set<OverviewTab>();

  usageRecords: UsageRecord[] = [];
  activeAddons: SubscriptionAddon[] = [];
  availableAddons: Addon[] = [];
  invoices: Invoice[] = [];

  ngOnInit(): void {
    this.reload();
  }

  reload(): void {
    const org = this.orgCtx.activeOrganization();
    const orgId = org?.id ?? null;
    this.organizationId = orgId;
    this.orgName = org?.display_name ?? null;
    this.error = null;
    this.subscription = null;
    this.loadedTabs.clear();
    if (orgId == null) return;
    this.loading = true;
    this.api.listSubscriptions(orgId, { page: 1, limit: 10 }).subscribe({
      next: (r) => {
        const active =
          r.items.find((s) => ['active', 'trialing', 'past_due'].includes(s.status)) ?? null;
        this.subscription = active;
        if (active) {
          this.loadDetails(orgId, active);
        } else {
          this.loading = false;
        }
      },
      error: (e) => {
        this.error = e?.error?.detail?.message ?? this.i18n.t('common.loadFailed');
        this.loading = false;
      },
    });
  }

  private loadDetails(orgId: number, sub: Subscription): void {
    this.api.getPlan(sub.plan_id).subscribe({
      next: (p: Plan) => (this.planName = p.display_name),
      error: () => (this.planName = null),
    });
    if (sub.plan_price_id) {
      this.api.listPlanPrices(sub.plan_id).subscribe({
        next: (prices: PlanPrice[]) => {
          const pr = prices.find((x) => x.id === sub.plan_price_id) ?? null;
          if (pr) {
            this.priceAmount = Number(pr.amount);
            this.priceCurrency = pr.currency || sub.billing_currency || 'USD';
            this.pricePeriod = pr.billing_period;
          } else {
            this.priceAmount = null;
            this.pricePeriod = null;
          }
        },
        error: () => {
          this.priceAmount = null;
        },
      });
    } else {
      this.priceAmount = null;
      this.pricePeriod = null;
    }
    this.loadEntitlements();
    this.api.getAccessState(orgId, sub.id).subscribe({
      next: (s) => {
        this.accessState = s;
        this.loading = false;
        this.loadTabData();
      },
      error: () => {
        this.loading = false;
        this.loadTabData();
      },
    });
  }

  loadEntitlements(): void {
    const orgId = this.organizationId;
    const sub = this.subscription;
    if (!orgId || !sub) return;
    this.entitlementsLoading = true;
    this.entitlementsError = null;
    this.api.listEntitlements(orgId, sub.id).subscribe({
      next: (ents) => {
        this.entitlements = ents;
        this.entitlementsLoading = false;
      },
      error: (e) => {
        this.entitlements = [];
        this.entitlementsError = e?.error?.detail?.message ?? this.i18n.t('common.loadFailed');
        this.entitlementsLoading = false;
      },
    });
  }

  setTab(whichTab: OverviewTab): void {
    this.tab.set(whichTab);
    if (!this.loadedTabs.has(whichTab)) {
      this.loadTabData();
    }
  }

  loadTabData(): void {
    const orgId = this.organizationId;
    const sub = this.subscription;
    if (!orgId || !sub) return;
    const t = this.tab();
    this.tabLoading.set(true);
    this.tabError.set(null);
    if (t === 'usage') {
      this.api.listUsage(orgId, sub.id).subscribe({
        next: (r) => {
          this.usageRecords = r.items;
          this.loadedTabs.add('usage');
          this.tabLoading.set(false);
        },
        error: (e) => {
          this.tabError.set(e?.error?.detail?.message ?? this.i18n.t('common.loadFailed'));
          this.tabLoading.set(false);
        },
      });
      return;
    }
    if (t === 'addons') {
      forkJoin({
        active: this.api.listSubscriptionAddons(orgId, sub.id).pipe(catchError(() => of([]))),
        available: this.api.listAddons({ status: 'active' }).pipe(
          catchError(() => of({ items: [], total: 0, page: 1, limit: 25 })),
        ),
      }).subscribe({
        next: ({ active, available }) => {
          this.activeAddons = active.filter((a) => a.status === 'active');
          this.availableAddons = 'items' in available ? available.items : [];
          this.loadedTabs.add('addons');
          this.tabLoading.set(false);
        },
        error: (e) => {
          this.tabError.set(e?.error?.detail?.message ?? this.i18n.t('common.loadFailed'));
          this.tabLoading.set(false);
        },
      });
      return;
    }
    this.billing.listInvoices(orgId, { page: 1, page_size: 10 }).subscribe({
      next: (r) => {
        this.invoices = r.items ?? [];
        this.loadedTabs.add('invoices');
        this.tabLoading.set(false);
      },
      error: (e) => {
        this.tabError.set(e?.error?.detail?.message ?? this.i18n.t('common.loadFailed'));
        this.tabLoading.set(false);
      },
    });
  }

  tabTitle(): string {
    const t = this.tab();
    if (t === 'addons') return this.i18n.t('subscriptions.overview.tab.addons');
    if (t === 'invoices') return this.i18n.t('subscriptions.overview.tab.invoices');
    return this.i18n.t('subscriptions.overview.tab.usage');
  }

  periodLabel(): string {
    if (this.pricePeriod === 'annual') return this.i18n.t('subscriptions.period.annual');
    if (this.pricePeriod === 'monthly') return this.i18n.t('subscriptions.period.monthly');
    return this.i18n.t('subscriptions.overview.periodUnset');
  }

  featureName(code: string): string {
    const key = `subscriptions.feature.${code}`;
    const t = this.i18n.t(key);
    const missing = this.i18n.t('common.missingTranslation');
    if (t && t !== key && t !== missing) return t;
    return code.replace(/_/g, ' ');
  }

  featureDescription(code: string): string {
    const key = `subscriptions.feature.${code}.desc`;
    const t = this.i18n.t(key);
    const missing = this.i18n.t('common.missingTranslation');
    if (t && t !== key && t !== missing) return t;
    return this.i18n.t('subscriptions.overview.ent.defaultDesc');
  }

  limitLabel(e: SubscriptionEntitlement): string {
    if (!e.enabled) return this.i18n.t('subscriptions.overview.ent.notIncluded');
    if (e.limit_value == null) return this.i18n.t('subscriptions.overview.ent.unlimited');
    return String(e.limit_value);
  }

  usageLabel(e: SubscriptionEntitlement): string {
    if (!e.enabled) return this.i18n.t('subscriptions.overview.ent.notIncluded');
    if (e.limit_value == null) return this.i18n.t('subscriptions.overview.ent.included');
    if (e.current_usage != null) {
      return this.i18n.t('subscriptions.overview.ent.usageOf', {
        used: e.current_usage,
        limit: e.limit_value,
      });
    }
    return this.i18n.t('subscriptions.overview.ent.usageUnset');
  }

  remainingLabel(e: SubscriptionEntitlement): string {
    if (!e.enabled) return this.i18n.t('subscriptions.overview.ent.notIncluded');
    if (e.limit_value == null) return this.i18n.t('subscriptions.overview.ent.unlimited');
    if (e.remaining != null) return String(e.remaining);
    if (e.current_usage != null) return String(Math.max(0, e.limit_value - e.current_usage));
    return this.i18n.t('subscriptions.overview.ent.remainingUnset');
  }

  addonName(addonId: number): string {
    const found = this.availableAddons.find((a) => a.id === addonId);
    return found?.display_name ?? `#${addonId}`;
  }
}
