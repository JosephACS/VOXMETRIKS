import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { SubscriptionsApiService } from '../services/subscriptions-api.service';
import { Addon, SubscriptionAddon } from '../models/subscriptions.models';

@Component({
  selector: 'app-subscription-addons',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="subscription-addons">
      <h1 i18n="subscriptions.addons.title">Addons de Suscripción</h1>

      <section class="active-addons">
        <h2 i18n="subscriptions.addons.active">Addons activos</h2>
        @if (activeAddons.length > 0) {
          <ul>
            @for (sa of activeAddons; track sa.addon_id) {
              <li>
                Addon #{{ sa.addon_id }} — {{ sa.status }}
                <button (click)="remove(sa.addon_id)"
                        i18n="subscriptions.addons.remove">Quitar</button>
              </li>
            }
          </ul>
        } @else {
          <p i18n="subscriptions.addons.none">
            Sin addons activos.
          </p>
        }
      </section>

      <section class="available-addons">
        <h2 i18n="subscriptions.addons.available">Addons disponibles</h2>
        @if (availableAddons.length > 0) {
          <ul>
            @for (addon of availableAddons; track addon.id) {
              <li>
                <strong>{{ addon.display_name }}</strong>
                @if (addon.amount) {
                  <span> — {{ addon.currency }} {{ addon.amount }}/{{ addon.billing_period }}</span>
                }
                <button (click)="add(addon.id)"
                        [disabled]="isAdded(addon.id)"
                        i18n="subscriptions.addons.add">Agregar</button>
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
  private readonly api = inject(SubscriptionsApiService);
  private readonly route = inject(ActivatedRoute);

  organizationId = 0;
  subscriptionId = 0;
  activeAddons: SubscriptionAddon[] = [];
  availableAddons: Addon[] = [];
  error: string | null = null;

  ngOnInit(): void {
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
    this.api.addAddon(this.organizationId, this.subscriptionId, addonId).subscribe({
      next: () => this.refresh(),
      error: (e) => (this.error = e?.error?.detail?.message ?? 'Error al agregar addon'),
    });
  }

  remove(addonId: number): void {
    this.api.removeAddon(this.organizationId, this.subscriptionId, addonId).subscribe({
      next: () => this.refresh(),
      error: (e) => (this.error = e?.error?.detail?.message ?? 'Error al quitar addon'),
    });
  }

  private refresh(): void {
    this.api.listSubscriptionAddons(this.organizationId, this.subscriptionId).subscribe({
      next: (addons) => (this.activeAddons = addons.filter((a) => a.status === 'active')),
      error: () => {
        this.activeAddons = [];
        this.error = 'Error al cargar addons de la suscripción';
      },
    });
  }
}
