import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { SubscriptionsApiService } from '../services/subscriptions-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { Addon, SubscriptionAddon } from '../models/subscriptions.models';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
@Component({
  selector: 'app-subscription-addons',
  standalone: true,
  imports: [CommonModule, TranslatePipe],
  template: `
    <div class="vx-enterprise subscription-addons">
      <h1>{{ 'subscriptions.addons.title' | t:lang() }}</h1>

      <section class="active-addons">
        <h2>Addons activos</h2>
        @if (activeAddons.length > 0) {
          <ul>
            @for (sa of activeAddons; track sa.addon_id) {
              <li>
                Addon #{{ sa.addon_id }} — {{ sa.status }}
                <button (click)="remove(sa.addon_id)">Quitar</button>
              </li>
            }
          </ul>
        } @else {
          <p>
            Sin addons activos.
          </p>
        }
      </section>

      <section class="available-addons">
        <h2>Addons disponibles</h2>
        @if (availableAddons.length > 0) {
          <ul>
            @for (addon of availableAddons; track addon.id) {
              <li>
                <strong>{{ addon.display_name }}</strong>
                @if (addon.amount) {
                  <span> — {{ addon.currency }} {{ addon.amount }}/{{ addon.billing_period }}</span>
                }
                <button (click)="add(addon.id)"
                        [disabled]="isAdded(addon.id)">Agregar</button>
              </li>
            }
          </ul>
        }
      </section>

      @if (error) {
        <div class="error">{{ error }}</div>
      }
    </div>
  `,
})
export class SubscriptionAddonsPageComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private readonly api = inject(SubscriptionsApiService);
  private readonly orgCtx = inject(OrganizationContextService);
  private readonly route = inject(ActivatedRoute);

  organizationId: number | null = null;
  subscriptionId = 0;
  activeAddons: SubscriptionAddon[] = [];
  availableAddons: Addon[] = [];
  error: string | null = null;

  ngOnInit(): void {
    this.organizationId = this.orgCtx.activeOrganization()?.id ?? null;
    if (!this.organizationId) {
      this.error = this.i18n.t('common.orgRequiredContext');
      return;
    }
    this.subscriptionId = Number(this.route.snapshot.paramMap.get('id'));
    this.refresh();
    this.api.listAddons({ status: 'active', limit: 50 }).subscribe({
      next: (r) => (this.availableAddons = r.items),
      error: () => {
        this.availableAddons = [];
      },
    });
  }

  isAdded(addonId: number): boolean {
    return this.activeAddons.some((a) => a.addon_id === addonId && a.status === 'active');
  }

  add(addonId: number): void {
    const orgId = this.organizationId;
    if (orgId == null) return;
    this.api.addAddon(orgId, this.subscriptionId, addonId).subscribe({
      next: () => this.refresh(),
      error: (e) => (this.error = e?.error?.detail?.message ?? 'Error al agregar addon'),
    });
  }

  remove(addonId: number): void {
    const orgId = this.organizationId;
    if (orgId == null) return;
    this.api.removeAddon(orgId, this.subscriptionId, addonId).subscribe({
      next: () => this.refresh(),
      error: (e) => (this.error = e?.error?.detail?.message ?? 'Error al quitar addon'),
    });
  }

  private refresh(): void {
    const orgId = this.organizationId;
    if (orgId == null) return;
    this.api.listSubscriptionAddons(orgId, this.subscriptionId).subscribe({
      next: (addons) => (this.activeAddons = addons.filter((a) => a.status === 'active')),
      error: () => {
        this.activeAddons = [];
        this.error = 'Error al cargar addons de la suscripción';
      },
    });
  }
}
