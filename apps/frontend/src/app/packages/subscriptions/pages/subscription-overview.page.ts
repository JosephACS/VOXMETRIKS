import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { SubscriptionsApiService } from '../services/subscriptions-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { Subscription, SubscriptionEntitlement, AccessStateInfo } from '../models/subscriptions.models';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
/** Org subscription overview — requires organizationId from context/route. */
@Component({
  selector: 'app-subscription-overview',
  standalone: true,
  imports: [CommonModule, RouterModule, TranslatePipe],
  template: `
    <div class="subscription-overview">
      <div class="page-header">
        <h1>{{ 'subscriptions.overview.title' | t:lang() }}</h1>
      </div>

      @if (accessState && accessState.access_state !== 'full') {
        <div class="access-banner"
             [class]="'access-banner--' + accessState.access_state">
          @switch (accessState.access_state) {
            @case ('limited') {
              <span>
                ⚠️ Acceso limitado. {{ accessState.reason }}
              </span>
            }
            @case ('blocked') {
              <span>
                🚫 Acceso bloqueado. {{ accessState.reason }}
              </span>
            }
          }
        </div>
      }

      @if (subscription) {
        <div class="sub-card">
          <div class="sub-card__status">
            <span class="badge" [class]="'badge--' + subscription.status">
              {{ subscription.status }}
            </span>
            @if (subscription.cancel_at_period_end) {
              <span class="badge badge--archived">Cancela al fin del periodo</span>
            }
          </div>

          <dl>
            <dt>Moneda de facturación</dt>
            <dd>{{ subscription.billing_currency }}</dd>

            @if (subscription.trial_ends_at) {
              <dt>Trial expira</dt>
              <dd>{{ subscription.trial_ends_at | date }}</dd>
            }

            @if (subscription.current_period_start) {
              <dt>Periodo actual</dt>
              <dd>{{ subscription.current_period_start | date }} —
                  {{ subscription.current_period_end | date }}</dd>
            }
          </dl>

          <div class="sub-card__actions">
            <a [routerLink]="['/subscriptions', subscription.id, 'usage']">Uso</a>
            <a [routerLink]="['/subscriptions', subscription.id, 'addons']">Addons</a>
            <a [routerLink]="['/billing/invoices']">Facturas</a>
          </div>
        </div>

        <section class="entitlements">
          <h2>Entitlements activos</h2>
          @if (entitlements.length > 0) {
            <ul>
              @for (e of entitlements; track e.feature_code) {
                <li>
                  <strong>{{ e.feature_code }}</strong>
                  @if (e.limit_value !== null) {
                    <span> — límite {{ e.limit_value }}</span>
                  }
                  <span class="badge badge--draft"> {{ e.source }}</span>
                </li>
              }
            </ul>
          } @else {
            <p>
              Sin entitlements activos.
            </p>
          }
        </section>
      } @else {
        @if (!loading) {
          <div class="no-sub">
            <p>No tienes una suscripción activa.</p>
            <a [routerLink]="['/subscriptions/plans']" class="btn btn--primary">Elegir un plan</a>
          </div>
        }
      }

      @if (loading) {
        <div>{{ 'common.loading' | t:lang() }}</div>
      }
      @if (error) {
        <div class="error">{{ error }}</div>
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
  subscription: Subscription | null = null;
  entitlements: SubscriptionEntitlement[] = [];
  accessState: AccessStateInfo | null = null;
  loading = false;
  error: string | null = null;

  ngOnInit(): void {
    const orgId = this.orgCtx.activeOrganization()?.id ?? null;
    this.organizationId = orgId;
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
          this.loadDetails(orgId, active.id);
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

  private loadDetails(orgId: number, subId: number): void {
    this.api.listEntitlements(orgId, subId).subscribe({
      next: (ents) => (this.entitlements = ents),
      error: () => {
        this.entitlements = [];
      },
    });
    this.api.getAccessState(orgId, subId).subscribe({
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
