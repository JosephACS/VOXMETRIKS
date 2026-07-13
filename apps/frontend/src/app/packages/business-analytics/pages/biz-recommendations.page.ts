import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { BusinessAnalyticsApiService } from '../services/business-analytics-api.service';
import { Recommendation } from '../models/business-analytics.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
@Component({
  selector: 'app-biz-recommendations',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe],
  template: `
    <div class="biz-recommendations">
      <a routerLink="/business-analytics">← Dashboard</a>
      <h1>{{ 'businessAnalytics.recommendations.title' | t:lang() }}</h1>
      <p class="subtitle">Honest rule-based insights — not AI.</p>
      <button type="button" (click)="generate()">Generate</button>
      @if (recs.length === 0) { <p>No recommendations yet.</p> }
      @else {
        <ul>
          @for (r of recs; track r.id) {
            <li>
              <strong>{{ r.title }}</strong>
              <p>{{ r.rationale }}</p>
              <small>Rule: {{ r.rule_code }} | AI: {{ r.is_ai ? 'yes' : 'no' }} | {{ r.evidence_ref }}</small>
            </li>
          }
        </ul>
      }
    </div>
  `,
})
export class BizRecommendationsPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(BusinessAnalyticsApiService);
  private orgCtx = inject(OrganizationContextService);
  recs: Recommendation[] = [];

  ngOnInit(): void { this.load(); }

  load(): void {
    const orgId = this.orgCtx.activeOrganization()?.id;
    if (!orgId) return;
    this.api.generateRecommendations(orgId).subscribe((r) => (this.recs = r));
  }

  generate(): void { this.load(); }
}
