import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { SubscriptionsApiService } from '../services/subscriptions-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { UsageRecord } from '../models/subscriptions.models';

@Component({
  selector: 'app-subscription-usage',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="subscription-usage">
      <h1 i18n="subscriptions.usage.title">Uso de Suscripción</h1>

      @if (records.length > 0) {
        <table>
          <thead>
            <tr>
              <th i18n="subscriptions.usage.feature">Característica</th>
              <th i18n="subscriptions.usage.quantity">Cantidad</th>
              <th i18n="subscriptions.usage.period">Periodo</th>
              <th i18n="subscriptions.usage.recorded">Registrado</th>
            </tr>
          </thead>
          <tbody>
            @for (r of records; track r.id) {
              <tr>
                <td>{{ r.feature_code }}</td>
                <td>{{ r.quantity }}</td>
                <td>{{ r.period_start }} — {{ r.period_end }}</td>
                <td>{{ r.recorded_at | date:'short' }}</td>
              </tr>
            }
          </tbody>
        </table>
      }

      @if (records.length === 0 && !loading) {
        <p i18n="subscriptions.usage.empty">
          Sin registros de uso.
        </p>
      }
      @if (loading) {
        <div i18n="common.loading">Cargando...</div>
      }
      @if (error) {
        <div class="error">{{ error }}</div>
      }
    </div>
  `,
})
export class SubscriptionUsagePageComponent implements OnInit {
  private readonly api = inject(SubscriptionsApiService);
  private readonly orgCtx = inject(OrganizationContextService);
  private readonly route = inject(ActivatedRoute);

  organizationId: number | null = null;
  subscriptionId = 0;
  records: UsageRecord[] = [];
  total = 0;
  loading = false;
  error: string | null = null;

  ngOnInit(): void {
    const orgId = this.orgCtx.activeOrganization()?.id ?? null;
    this.organizationId = orgId;
    if (orgId == null) {
      this.error = 'Select an organization context.';
      return;
    }
    this.subscriptionId = Number(this.route.snapshot.paramMap.get('id'));
    this.loading = true;
    this.api.listUsage(orgId, this.subscriptionId).subscribe({
      next: (r) => {
        this.records = r.items;
        this.total = r.total;
        this.loading = false;
      },
      error: (e) => {
        this.error = e?.error?.detail?.message ?? 'Error al cargar uso';
        this.loading = false;
      },
    });
  }
}
