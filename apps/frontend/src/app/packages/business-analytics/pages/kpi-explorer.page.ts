import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { BusinessAnalyticsApiService } from '../services/business-analytics-api.service';
import { KpiDefinition } from '../models/business-analytics.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
@Component({
  selector: 'app-kpi-explorer',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe],
  template: `
    <div class="vx-enterprise kpi-explorer">
      <a routerLink="/business-analytics">← Dashboard</a>
      <h1>{{ 'businessAnalytics.kpis.title' | t:lang() }}</h1>
      @if (loading) { <p>{{ 'common.loading' | t:lang() }}</p> }
      @else {
        <table>
          <thead><tr><th>Code</th><th>Name</th><th>Formula</th><th>Source</th><th>Null handling</th></tr></thead>
          <tbody>
            @for (k of kpis; track k.id) {
              <tr>
                <td>{{ k.code }} v{{ k.version }}</td>
                <td>{{ k.name }}</td>
                <td>{{ k.formula_description }}</td>
                <td>{{ k.source_type }}</td>
                <td>{{ k.null_handling }}</td>
              </tr>
            }
          </tbody>
        </table>
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

  ngOnInit(): void {
    const orgId = this.orgCtx.activeOrganization()?.id;
    if (!orgId) return;
    this.loading = true;
    this.api.listKpis(orgId).subscribe({
      next: (k) => { this.kpis = k; this.loading = false; },
      error: () => { this.loading = false; },
    });
  }
}
