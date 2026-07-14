import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { SubscriptionsApiService } from '../services/subscriptions-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { Subscription, SubscriptionEntitlement, AccessStateInfo, Plan } from '../models/subscriptions.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { LocaleDatePipe } from '../../../shared/pipes/locale-format.pipe';
import { StatusLabelPipe } from '../../../shared/pipes/status-label.pipe';

@Component({
  selector: 'app-subscription-overview',
  standalone: true,
  imports: [CommonModule, RouterModule, TranslatePipe, LocaleDatePipe, StatusLabelPipe],
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
            {{ 'subscriptions.plans.title' | t:lang() }}
          </a>
          @if (!subscription) {
            <a routerLink="/subscriptions/select-plan" class="btn btn--primary">
              {{ 'subscriptions.plans.chooseCta' | t:lang() }}
            </a>
          } @else {
            <a [routerLink]="['/subscriptions', subscription.id, 'addons']" class="btn btn--primary">
              {{ 'nav.subscriptions.overview' | t:lang() }} · Add-ons
            </a>
          }
        </div>
      </header>

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

      @if (loading) {
        <div class="vx-skel-block" aria-busy="true">
          <div class="vx-skel"></div>
          <div class="vx-skel"></div>
        </div>
      } @else if (error) {
        <div class="alert alert--danger" role="alert">{{ error }}</div>
      } @else if (subscription) {
        <div class="sub-card">
          <div class="sub-card__status vx-hero__meta" style="margin-top:0">
            <span class="badge" [class]="'badge--' + subscription.status">
              {{ subscription.status | statusLabel }}
            </span>
            @if (subscription.cancel_at_period_end) {
              <span class="badge badge--archived">Cancela al fin del periodo</span>
            }
            <span class="badge" [class]="'badge--' + subscription.access_state">
              {{ subscription.access_state | statusLabel }}
            </span>
          </div>

          <dl>
            <dt>Moneda</dt>
            <dd>{{ subscription.billing_currency }}</dd>
            @if (subscription.trial_ends_at) {
              <dt>Trial expira</dt>
              <dd>{{ subscription.trial_ends_at | localeDate }}</dd>
            }
            @if (subscription.current_period_start) {
              <dt>Periodo actual</dt>
              <dd>
                {{ subscription.current_period_start | localeDate }} —
                {{ subscription.current_period_end | localeDate }}
              </dd>
            }
          </dl>

          <div class="sub-card__actions">
            <a [routerLink]="['/subscriptions', subscription.id, 'usage']">Uso</a>
            <a [routerLink]="['/subscriptions', subscription.id, 'addons']">Add-ons</a>
            <a [routerLink]="['/billing/invoices']">{{ 'subscriptions.overview.invoices' | t:lang() }}</a>
            <a [routerLink]="['/subscriptions', subscription.id, 'cancel']" class="btn btn--danger" style="margin-left:auto">
              {{ 'subscriptions.cancel.title' | t:lang() }}
            </a>
          </div>
        </div>

        <section class="entitlements">
          <h2>{{ 'subscriptions.overview.entitlements' | t:lang() }}</h2>
          @if (entitlements.length > 0) {
            <div class="table-card">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Feature</th>
                    <th>Límite</th>
                    <th>Fuente</th>
                  </tr>
                </thead>
                <tbody>
                  @for (e of entitlements; track e.feature_code) {
                    <tr>
                      <td><strong>{{ e.feature_code }}</strong></td>
                      <td>{{ e.limit_value !== null ? e.limit_value : ('common.notAvailable' | t:lang()) }}</td>
                      <td><span class="badge badge--draft">{{ e.source }}</span></td>
                    </tr>
                  }
                </tbody>
              </table>
            </div>
          } @else {
            <div class="empty-state">
              <p>Sin entitlements activos.</p>
            </div>
          }
        </section>
      } @else {
        <div class="no-sub">
          <p>No tienes una suscripción activa.</p>
          <a routerLink="/subscriptions/plans" class="btn btn--primary">
            {{ 'subscriptions.plans.chooseCta' | t:lang() }}
          </a>
        </div>
      }
    </div>
  `,
})
export class SubscriptionOverviewPageComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private readonly api = inject(SubscriptionsApiService);
  private readonly orgCtx = inject(OrganizationContextService);

  organizationId: number | null = null;
  orgName: string | null = null;
  planName: string | null = null;
  subscription: Subscription | null = null;
  entitlements: SubscriptionEntitlement[] = [];
  accessState: AccessStateInfo | null = null;
  loading = false;
  error: string | null = null;

  ngOnInit(): void {
    const org = this.orgCtx.activeOrganization();
    const orgId = org?.id ?? null;
    this.organizationId = orgId;
    this.orgName = org?.display_name ?? null;
    if (orgId == null) {
      this.error = this.i18n.t('common.orgRequiredContext');
      return;
    }
    this.loading = true;
    this.api.listSubscriptions(orgId, { page: 1, limit: 10 }).subscribe({
      next: (r) => {
        const active = r.items.find((s) =>
          ['active', 'trialing', 'past_due'].includes(s.status),
        );
        this.subscription = active ?? null;
        if (active) {
          this.loadDetails(orgId, active);
        } else {
          this.loading = false;
        }
      },
      error: (e) => {
        this.error = e?.error?.detail?.message ?? 'Error al cargar suscripción';
        this.loading = false;
      },
    });
  }

  private loadDetails(orgId: number, sub: Subscription): void {
    this.api.getPlan(sub.plan_id).subscribe({
      next: (p: Plan) => (this.planName = p.display_name),
      error: () => (this.planName = null),
    });
    this.api.listEntitlements(orgId, sub.id).subscribe({
      next: (ents) => (this.entitlements = ents),
      error: () => {
        this.entitlements = [];
      },
    });
    this.api.getAccessState(orgId, sub.id).subscribe({
      next: (s) => {
        this.accessState = s;
        this.loading = false;
      },
      error: () => {
        this.loading = false;
      },
    });
  }
}
