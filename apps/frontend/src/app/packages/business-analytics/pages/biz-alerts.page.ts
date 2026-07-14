import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { BusinessAnalyticsApiService } from '../services/business-analytics-api.service';
import { BusinessAlert } from '../models/business-analytics.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-biz-alerts',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    TranslatePipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  template: `
    <div class="vx-enterprise biz-alerts-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <app-enterprise-page-header
          [title]="'businessAnalytics.alerts.title' | t:lang()"
          [subtitle]="'businessAnalytics.alerts.subtitle' | t:lang()"
        >
          <a routerLink="/business-analytics" class="btn btn--secondary">
            {{ 'common.back' | t:lang() }}
          </a>
        </app-enterprise-page-header>

        @if (!alerts.length) {
          <app-enterprise-empty-state
            [title]="'businessAnalytics.alerts.emptyTitle' | t:lang()"
            [description]="'businessAnalytics.alerts.emptyBody' | t:lang()"
          />
        } @else {
          <app-enterprise-data-table>
            <table class="data-table">
              <thead>
                <tr>
                  <th>{{ 'businessAnalytics.alerts.severity' | t:lang() }}</th>
                  <th>{{ 'common.name' | t:lang() }}</th>
                  <th>{{ 'common.status' | t:lang() }}</th>
                </tr>
              </thead>
              <tbody>
                @for (a of alerts; track a.id) {
                  <tr>
                    <td><app-enterprise-status-badge [status]="a.severity" /></td>
                    <td>{{ a.title }}</td>
                    <td><app-enterprise-status-badge [status]="a.status" /></td>
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
export class BizAlertsPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(BusinessAnalyticsApiService);
  private orgCtx = inject(OrganizationContextService);
  alerts: BusinessAlert[] = [];
  orgId: number | null = null;

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    if (!this.orgId) return;
    this.api.listAlerts(this.orgId).subscribe((a) => (this.alerts = a));
  }
}
