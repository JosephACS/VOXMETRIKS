import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { BusinessAnalyticsApiService } from '../services/business-analytics-api.service';
import { BusinessAlert } from '../models/business-analytics.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
@Component({
  selector: 'app-biz-alerts',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe],
  template: `
    <div class="biz-alerts">
      <a routerLink="/business-analytics">← Dashboard</a>
      <h1>{{ 'businessAnalytics.alerts.title' | t:lang() }}</h1>
      @if (alerts.length === 0) { <p>{{ 'businessAnalytics.alerts.empty' | t:lang() }}</p> }
      @else {
        <ul>
          @for (a of alerts; track a.id) {
            <li><strong [class]="'sev-' + a.severity">{{ a.severity }}</strong> {{ a.title }} — {{ a.status }}</li>
          }
        </ul>
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

  ngOnInit(): void {
    const orgId = this.orgCtx.activeOrganization()?.id;
    if (!orgId) return;
    this.api.listAlerts(orgId).subscribe((a) => (this.alerts = a));
  }
}
