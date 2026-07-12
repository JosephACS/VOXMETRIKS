import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { BusinessAnalyticsApiService } from '../services/business-analytics-api.service';
import { DashboardOverview } from '../models/business-analytics.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';

@Component({
  selector: 'app-biz-analytics-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <div class="biz-analytics-dashboard">
      <h1>Enterprise Analytics</h1>
      <p class="subtitle">KPI catalog wrapping existing warehouse metrics — sources always labeled.</p>
      <nav class="subnav">
        <a routerLink="/business-analytics">Dashboard</a> |
        <a routerLink="/business-analytics/kpis">KPI Explorer</a> |
        <a routerLink="/business-analytics/alerts">Alerts</a> |
        <a routerLink="/business-analytics/recommendations">Recommendations</a> |
        <a routerLink="/business-analytics/quality">Data Quality</a>
      </nav>

      @if (loading) { <p>Loading…</p> }
      @else if (overview) {
        <p>Period: {{ overview.period }}</p>
        <div class="kpi-grid">
          @for (entry of kpiEntries; track entry.code) {
            <div class="kpi-card">
              <h3>{{ entry.code }}</h3>
              @if (entry.data.value != null) {
                <p class="kpi-value">{{ entry.data.value | number }}</p>
              } @else {
                <p class="kpi-null">— ({{ entry.data.quality_status }})</p>
              }
              <p class="kpi-source">{{ entry.data.source_label }}</p>
              @if (entry.data.is_synthetic) { <span class="badge">synthetic</span> }
            </div>
          }
        </div>
      }
      @if (error) { <p class="error">{{ error }}</p> }
    </div>
  `,
})
export class BizAnalyticsDashboardPage implements OnInit {
  private api = inject(BusinessAnalyticsApiService);
  private orgCtx = inject(OrganizationContextService);

  overview: DashboardOverview | null = null;
  kpiEntries: { code: string; data: DashboardOverview['kpis'][string] }[] = [];
  loading = false;
  error: string | null = null;

  ngOnInit(): void { this.load(); }

  load(): void {
    const orgId = this.orgCtx.activeOrganization()?.id;
    if (!orgId) { this.error = 'Select an organization'; return; }
    this.loading = true;
    this.api.getDashboard(orgId).subscribe({
      next: (d) => {
        this.overview = d;
        this.kpiEntries = Object.entries(d.kpis).map(([code, data]) => ({ code, data }));
        this.loading = false;
      },
      error: (e) => { this.error = e?.error?.message || 'Failed'; this.loading = false; },
    });
  }
}
