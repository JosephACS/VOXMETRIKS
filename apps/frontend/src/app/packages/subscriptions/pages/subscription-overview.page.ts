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
  styleUrls: ['../../organizations/styles/workspace-settings.css'],
  template: `
    <div class="subscription-overview vx-enterprise ws-page" data-testid="plan-billing">
      <header class="ws-head">
        <p class="ws-kicker">Organización</p>
        <h1 class="ws-title">Plan y facturación</h1>
        <p class="ws-sub">Consulta el plan activo, renovación y facturas del espacio de trabajo.</p>
      </header>

      <div class="ws-actions" style="margin-bottom: 0.85rem">
        <a routerLink="/subscriptions/plans" class="primary">Cambiar plan</a>
        @if (!subscription) {
          <a routerLink="/subscriptions/select-plan">Elegir plan</a>
        }
        <a routerLink="/billing/invoices">Ver facturas</a>
        @if (organizationId) {
          <a [routerLink]="['/organizations', organizationId]">Volver a Organización</a>
        }
      </div>

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
                <span>{{ 'subscriptions.overview.limited' | t:lang() }}. {{ accessState.reason }}</span>
              }
              @case ('blocked') {
                <span>{{ accessState.reason }}</span>
              }
            }
          </div>
        }

        <section class="ws-section">
          <h2 class="ws-section__title">Plan actual</h2>
          <dl class="ws-dl">
            <div>
              <dt>{{ 'subscriptions.overview.field.plan' | t:lang() }}</dt>
              <dd>{{ planName || ('subscriptions.overview.planUnset' | t:lang()) }}</dd>
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
                  <span class="ws-pill ws-pill--warn">{{ 'subscriptions.overview.cancelAtPeriodEnd' | t:lang() }}</span>
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
              <dt>{{ 'subscriptions.overview.field.organization' | t:lang() }}</dt>
              <dd>{{ orgName || ('common.notAvailable' | t:lang()) }}</dd>
            </div>
          </dl>
          <div class="ws-actions" style="margin-top: 0.85rem">
            <a routerLink="/subscriptions/plans">{{ 'subscriptions.overview.changePlan' | t:lang() }}</a>
            <button type="button" (click)="setTab('addons')">{{ 'subscriptions.overview.manageAddons' | t:lang() }}</button>
            <button type="button" (click)="setTab('invoices')">{{ 'subscriptions.overview.invoices' | t:lang() }}</button>
            @if (canCancel) {
              <a [routerLink]="['/subscriptions', subscription.id, 'cancel']">{{ 'subscriptions.cancel.title' | t:lang() }}</a>
            }
          </div>
        </section>

        <section class="ws-section">
          <h2 class="ws-section__title">{{ 'subscriptions.overview.entitlements' | t:lang() }}</h2>
          @if (entitlementsLoading) {
            <app-enterprise-loading-skeleton [rows]="2" />
          } @else if (entitlementsError) {
            <app-enterprise-error-state [message]="entitlementsError" (retry)="loadEntitlements()" />
          } @else if (entitlements.length === 0) {
            <p class="ws-empty">{{ 'subscriptions.overview.entitlementsEmptyBody' | t:lang() }}</p>
          } @else {
            <ul class="ws-rows">
              @for (e of entitlements; track e.feature_code) {
                <li>
                  <div>
                    <p class="ws-row__title">{{ featureName(e.feature_code) }}</p>
                    <p class="ws-row__meta">{{ featureDescription(e.feature_code) }}</p>
                  </div>
                  <div class="ws-row__side">
                    <span class="ws-pill ws-pill--muted">{{ limitLabel(e) }}</span>
                    <span class="ws-row__meta">{{ usageLabel(e) }}</span>
                  </div>
                </li>
              }
            </ul>
          }
        </section>

        <div class="overview-tabs" role="tablist">
          <button type="button" class="overview-tab" role="tab" [class.is-active]="tab() === 'usage'" (click)="setTab('usage')">
            {{ 'subscriptions.overview.tab.usage' | t:lang() }}
          </button>
          <button type="button" class="overview-tab" role="tab" [class.is-active]="tab() === 'addons'" (click)="setTab('addons')">
            {{ 'subscriptions.overview.tab.addons' | t:lang() }}
          </button>
          <button type="button" class="overview-tab" role="tab" [class.is-active]="tab() === 'invoices'" (click)="setTab('invoices')">
            {{ 'subscriptions.overview.tab.invoices' | t:lang() }}
          </button>
        </div>

        <section class="ws-section">
          <h2 class="ws-section__title">{{ tabTitle() }}</h2>
          @if (tab() === 'usage') {
            @if (tabLoading()) {
              <app-enterprise-loading-skeleton [rows]="2" />
            } @else if (tabError()) {
              <app-enterprise-error-state [message]="tabError()!" (retry)="loadTabData()" />
            } @else if (usageRecords.length === 0) {
              <p class="ws-empty">{{ 'subscriptions.overview.usageEmptyBody' | t:lang() }}</p>
            } @else {
              <ul class="ws-rows">
                @for (r of usageRecords; track r.id) {
                  <li>
                    <div>
                      <p class="ws-row__title">{{ featureName(r.feature_code) }}</p>
                      <p class="ws-row__meta">{{ r.period_start | localeDate }} – {{ r.period_end | localeDate }}</p>
                    </div>
                    <div class="ws-row__side"><span class="ws-invoice-amount">{{ r.quantity }}</span></div>
                  </li>
                }
              </ul>
            }
          }

          @if (tab() === 'addons') {
            @if (tabLoading()) {
              <app-enterprise-loading-skeleton [rows]="2" />
            } @else if (tabError()) {
              <app-enterprise-error-state [message]="tabError()!" (retry)="loadTabData()" />
            } @else if (activeAddons.length === 0) {
              <p class="ws-empty">{{ 'subscriptions.overview.addonsEmptyBody' | t:lang() }}</p>
              <div class="ws-actions" style="margin-top: 0.75rem">
                <a [routerLink]="['/subscriptions', subscription.id, 'addons']">{{ 'subscriptions.overview.manageAddons' | t:lang() }}</a>
              </div>
            } @else {
              <ul class="ws-rows">
                @for (sa of activeAddons; track sa.id) {
                  <li>
                    <div><p class="ws-row__title">{{ addonName(sa.addon_id) }}</p></div>
                    <div class="ws-row__side"><app-enterprise-status-badge [status]="sa.status" /></div>
                  </li>
                }
              </ul>
              <div class="ws-actions" style="margin-top: 0.75rem">
                <a [routerLink]="['/subscriptions', subscription.id, 'addons']">{{ 'subscriptions.overview.manageAddons' | t:lang() }}</a>
              </div>
            }
          }

          @if (tab() === 'invoices') {
            @if (tabLoading()) {
              <app-enterprise-loading-skeleton [rows]="2" />
            } @else if (tabError()) {
              <app-enterprise-error-state [message]="tabError()!" (retry)="loadTabData()" />
            } @else if (invoices.length === 0) {
              <p class="ws-empty">{{ 'subscriptions.overview.invoicesEmptyBody' | t:lang() }}</p>
              <div class="ws-actions" style="margin-top: 0.75rem">
                <a routerLink="/billing/invoices">{{ 'subscriptions.overview.invoices' | t:lang() }}</a>
              </div>
            } @else {
              <ul class="ws-rows">
                @for (inv of invoices; track inv.id) {
                  <li>
                    <div>
                      <p class="ws-row__title">{{ inv.invoice_number || ('Factura #' + inv.id) }}</p>
                      <p class="ws-row__meta">{{ humanInvoiceStatus(inv.status) }}</p>
                    </div>
                    <div class="ws-row__side">
                      <span class="ws-invoice-amount">{{ inv.total | localeMoney: inv.currency }}</span>
                      <a class="ws-link" [routerLink]="['/billing/invoices', inv.id]">Ver factura</a>
                    </div>
                  </li>
                }
              </ul>
            }
          }
        </section>
      } @else {
        <section class="ws-section">
          <p class="ws-empty">{{ 'subscriptions.overview.noSubBody' | t:lang() }}</p>
          <div class="ws-actions" style="margin-top: 0.75rem">
            <a class="primary" routerLink="/subscriptions/plans">{{ 'subscriptions.plans.chooseCta' | t:lang() }}</a>
          </div>
        </section>
      }
    </div>
  `,
  styles: [
    `
      .overview-tabs {
        display: flex;
        gap: 0.35rem;
        margin: 0.25rem 0 0.85rem;
        padding: 0.3rem;
        border-radius: 0.85rem;
        border: 1px solid var(--vx-border-subtle, var(--border, rgba(255, 255, 255, 0.08)));
        background: var(--vx-surface, rgba(255, 255, 255, 0.03));
        flex-wrap: wrap;
      }
      .overview-tab {
        appearance: none;
        border: none;
        background: transparent;
        color: var(--vx-text-secondary, var(--text-muted));
        font: inherit;
        font-weight: 600;
        font-size: 0.875rem;
        padding: 0.55rem 0.95rem;
        border-radius: 0.65rem;
        cursor: pointer;
      }
      .overview-tab.is-active {
        background: color-mix(in srgb, var(--vx-accent, #e8a33d) 14%, transparent);
        color: var(--vx-accent, var(--accent, #e8a33d));
      }
      .access-banner {
        margin-bottom: 0.85rem;
        padding: 0.75rem 0.9rem;
        border-radius: 8px;
        border: 1px solid color-mix(in srgb, var(--vx-warning, #fbbf24) 35%, transparent);
        background: color-mix(in srgb, var(--vx-warning, #fbbf24) 10%, transparent);
        font-size: 0.85rem;
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

  get canCancel(): boolean {
    return this.orgCtx.hasPermission('subscription.cancel');
  }

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

  humanInvoiceStatus(status: string): string {
    const s = (status || '').toLowerCase();
    if (s === 'paid') return 'Pagada';
    if (s === 'past_due') return 'Vencida';
    if (s === 'failed') return 'Fallida';
    if (s === 'issued' || s === 'draft' || s === 'partially_paid' || s === 'pending') return 'Pendiente';
    if (s === 'void') return 'Anulada';
    return status || 'Sin datos';
  }

  addonName(addonId: number): string {
    const found = this.availableAddons.find((a) => a.id === addonId);
    return found?.display_name ?? `#${addonId}`;
  }
}
