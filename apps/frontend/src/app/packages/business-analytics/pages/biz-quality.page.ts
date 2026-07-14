import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { BusinessAnalyticsApiService } from '../services/business-analytics-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-biz-quality',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    TranslatePipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  template: `
    <div class="vx-enterprise biz-quality-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <app-enterprise-page-header
          [title]="'businessAnalytics.quality.title' | t:lang()"
          [subtitle]="'businessAnalytics.quality.subtitle' | t:lang()"
        >
          <a routerLink="/business-analytics" class="btn btn--secondary">
            {{ 'common.back' | t:lang() }}
          </a>
        </app-enterprise-page-header>

        @if (loading) {
          <app-enterprise-loading-skeleton [rows]="3" />
        } @else if (error) {
          <app-enterprise-error-state [message]="error" />
        } @else if (results.length === 0) {
          <app-enterprise-empty-state
            [title]="'businessAnalytics.quality.emptyTitle' | t:lang()"
            [description]="'businessAnalytics.quality.emptyBody' | t:lang()"
          />
        } @else {
          <app-enterprise-data-table>
            <table class="data-table">
              <thead>
                <tr>
                  <th>{{ 'businessAnalytics.quality.check' | t:lang() }}</th>
                  <th>{{ 'common.status' | t:lang() }}</th>
                  <th>{{ 'businessAnalytics.quality.detail' | t:lang() }}</th>
                </tr>
              </thead>
              <tbody>
                @for (q of rows; track $index) {
                  <tr>
                    <td>{{ q.name }}</td>
                    <td><app-enterprise-status-badge [status]="q.status" /></td>
                    <td>{{ q.detail }}</td>
                  </tr>
                }
              </tbody>
            </table>
          </app-enterprise-data-table>
        }
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
    this.orgId = this.orgCtx.organizationId();
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
              status: String(o['status'] ?? o['quality_status'] ?? 'unknown'),
              detail: String(o['message'] ?? o['detail'] ?? o['source_label'] ?? '—'),
            };
          }
          return { name: `check-${i + 1}`, status: 'unknown', detail: String(item) };
        });
        this.loading = false;
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || this.i18n.t('common.loadFailed');
        this.loading = false;
      },
    });
  }
}
