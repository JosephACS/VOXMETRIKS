import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { BusinessAnalyticsApiService } from '../services/business-analytics-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';

@Component({
  selector: 'app-biz-quality',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <div class="biz-quality">
      <a routerLink="/business-analytics">← Dashboard</a>
      <h1>Data Quality</h1>
      @if (results.length === 0) { <p>No quality checks run yet.</p> }
      @else {
        <ul>
          @for (q of results; track $index) {
            <li>{{ q | json }}</li>
          }
        </ul>
      }
    </div>
  `,
})
export class BizQualityPage implements OnInit {
  private api = inject(BusinessAnalyticsApiService);
  private orgCtx = inject(OrganizationContextService);
  results: unknown[] = [];

  ngOnInit(): void {
    const orgId = this.orgCtx.activeOrganization()?.id;
    if (!orgId) return;
    this.api.listQuality(orgId).subscribe((r) => (this.results = r));
  }
}
