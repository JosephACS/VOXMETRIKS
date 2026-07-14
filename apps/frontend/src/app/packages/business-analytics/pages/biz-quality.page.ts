import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { BusinessAnalyticsApiService } from '../services/business-analytics-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
@Component({
  selector: 'app-biz-quality',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe],
  template: `
    <div class="vx-enterprise page biz-quality">
      <a routerLink="/business-analytics">← Dashboard</a>
      <h1>{{ 'businessAnalytics.quality.title' | t:lang() }}</h1>
      <p class="subtitle">Warehouse / KPI quality checks — sources labeled.</p>
      @if (!orgId) {
        <p class="error">Select an organization context.</p>
      } @else if (loading) {
        <p>{{ 'common.loading' | t:lang() }}</p>
      } @else if (error) {
        <p class="error">{{ error }}</p>
      } @else if (results.length === 0) {
        <p class="empty-state">No quality checks available.</p>
      } @else {
        <table class="data-table">
          <thead>
            <tr><th>Check</th><th>Status</th><th>Detail</th></tr>
          </thead>
          <tbody>
            @for (q of rows; track $index) {
              <tr>
                <td>{{ q.name }}</td>
                <td><span class="badge">{{ q.status }}</span></td>
                <td>{{ q.detail }}</td>
              </tr>
            }
          </tbody>
        </table>
      }
    </div>
  `,
})
export class BizQualityPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(BusinessAnalyticsApiService);
  private orgCtx = inject(OrganizationContextService);
  orgId: number | null = null;
  results: unknown[] = [];
  rows: Array<{ name: string; status: string; detail: string }> = [];
  loading = false;
  error = '';

  ngOnInit(): void {
    this.orgId = this.orgCtx.activeOrganization()?.id ?? null;
    if (!this.orgId) return;
    this.loading = true;
    this.api.listQuality(this.orgId).subscribe({
      next: (r) => {
        this.results = r || [];
        this.rows = this.results.map((item, i) => {
          if (item && typeof item === 'object') {
            const o = item as Record<string, unknown>;
            return {
              name: String(o['code'] ?? o['name'] ?? o['check'] ?? `check-${i + 1}`),
              status: String(o['status'] ?? o['quality_status'] ?? 'No disponible'),
              detail: String(o['message'] ?? o['detail'] ?? o['source_label'] ?? '—'),
            };
          }
          return { name: `check-${i + 1}`, status: 'No disponible', detail: String(item) };
        });
        this.loading = false;
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || 'Failed to load quality checks';
        this.loading = false;
      },
    });
  }
}
