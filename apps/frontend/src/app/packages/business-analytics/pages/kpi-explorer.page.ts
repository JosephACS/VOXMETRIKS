import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { BusinessAnalyticsApiService } from '../services/business-analytics-api.service';
import { KpiDefinition } from '../models/business-analytics.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-kpi-explorer',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise--wide kpi-explorer">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <app-enterprise-page-header
          [title]="'businessAnalytics.kpis.title' | t:lang()"
          [subtitle]="'businessAnalytics.kpis.subtitle' | t:lang()"
          [orgName]="orgName || undefined"
        >
          <a routerLink="/business-analytics" class="btn btn--secondary">{{ 'common.back' | t:lang() }}</a>
        </app-enterprise-page-header>

        @if (loading) {
          <app-enterprise-loading-skeleton [rows]="4" />
        } @else if (error) {
          <app-enterprise-error-state [message]="error" (retry)="load()" />
        } @else {
          <app-enterprise-data-table
            [empty]="kpis.length === 0"
            [emptyTitle]="'businessAnalytics.kpis.emptyTitle' | t:lang()"
            [emptyDescription]="'businessAnalytics.kpis.emptyBody' | t:lang()"
          >
            <table class="data-table">
              <thead>
                <tr>
                  <th>{{ 'businessAnalytics.kpis.col.code' | t:lang() }}</th>
                  <th>{{ 'businessAnalytics.kpis.col.name' | t:lang() }}</th>
                  <th>{{ 'businessAnalytics.kpis.col.formula' | t:lang() }}</th>
                  <th>{{ 'businessAnalytics.kpis.col.source' | t:lang() }}</th>
                  <th>{{ 'businessAnalytics.kpis.col.frequency' | t:lang() }}</th>
                  <th>{{ 'businessAnalytics.kpis.col.owner' | t:lang() }}</th>
                  <th>{{ 'businessAnalytics.kpis.nullHandling' | t:lang() }}</th>
                  <th>{{ 'common.status' | t:lang() }}</th>
                </tr>
              </thead>
              <tbody>
                @for (k of kpis; track k.id) {
                  <tr>
                    <td class="mono">
                      {{ k.code }}
                      @if (k.version) {
                        <span class="muted"> v{{ k.version }}</span>
                      }
                    </td>
                    <td>{{ k.name }}</td>
                    <td>{{ k.formula_description || ('common.notAvailable' | t:lang()) }}</td>
                    <td>{{ sourceLabel(k.source_type) }}</td>
                    <td>{{ 'businessAnalytics.kpis.frequency.period' | t:lang() }}</td>
                    <td>{{ 'businessAnalytics.kpis.owner.analytics' | t:lang() }}</td>
                    <td>{{ nullHandlingLabel(k.null_handling) }}</td>
                    <td>
                      <app-enterprise-status-badge status="active" />
                    </td>
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
export class KpiExplorerPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;
  private api = inject(BusinessAnalyticsApiService);
  private orgCtx = inject(OrganizationContextService);

  kpis: KpiDefinition[] = [];
  loading = false;
  error: string | null = null;
  orgId: number | null = null;
  orgName: string | null = null;

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    this.orgName = this.orgCtx.activeOrganization()?.display_name ?? null;
    if (!this.orgId) return;
    this.load();
  }

  load(): void {
    const orgId = this.orgId;
    if (!orgId) return;
    this.loading = true;
    this.error = null;
    this.api.listKpis(orgId).subscribe({
      next: (k) => {
        this.kpis = k || [];
        this.loading = false;
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || this.i18n.t('common.failed');
        this.loading = false;
      },
    });
  }

  sourceLabel(code: string | null | undefined): string {
    if (!code) return this.i18n.t('common.notAvailable');
    const key = `businessAnalytics.kpis.source.${code}`;
    const t = this.i18n.t(key);
    return t === key ? code : t;
  }

  nullHandlingLabel(code: string | null | undefined): string {
    if (!code) return this.i18n.t('common.notAvailable');
    const key = `businessAnalytics.kpis.null.${code}`;
    const t = this.i18n.t(key);
    return t === key ? code : t;
  }
}
