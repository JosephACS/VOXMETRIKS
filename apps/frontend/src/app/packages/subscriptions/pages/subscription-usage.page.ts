import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute } from '@angular/router';
import { SubscriptionsApiService } from '../services/subscriptions-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { UsageRecord } from '../models/subscriptions.models';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { StatusLabelPipe } from '../../../shared/pipes/status-label.pipe';
import { LocaleDatePipe, LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';

@Component({
  selector: 'app-subscription-usage',
  standalone: true,
  imports: [CommonModule, TranslatePipe, StatusLabelPipe, LocaleMoneyPipe, LocaleDatePipe],
  template: `
    <div class="subscription-usage">
      <h1>{{ 'subscriptions.usage.title' | t:lang() }}</h1>

      @if (records.length > 0) {
        <table>
          <thead>
            <tr>
              <th>Característica</th>
              <th>Cantidad</th>
              <th>Periodo</th>
              <th>Registrado</th>
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
        <p>
          Sin registros de uso.
        </p>
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
export class SubscriptionUsagePageComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

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
      this.error = this.i18n.t('common.orgRequiredContext');
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
