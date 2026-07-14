import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { BusinessAnalyticsApiService } from '../services/business-analytics-api.service';
import { Recommendation } from '../models/business-analytics.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-biz-recommendations',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise biz-recommendations">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <a routerLink="/business-analytics" class="back-link">
          {{ 'businessAnalytics.recommendations.back' | t:lang() }}
        </a>

        <app-enterprise-page-header
          [title]="'businessAnalytics.recommendations.title' | t:lang()"
          [subtitle]="'businessAnalytics.recommendations.subtitle' | t:lang()"
        >
          <button type="button" class="btn btn--primary" (click)="generate()">
            {{ 'businessAnalytics.recommendations.generate' | t:lang() }}
          </button>
        </app-enterprise-page-header>

        @if (recs.length === 0) {
          <app-enterprise-empty-state
            [title]="'businessAnalytics.recommendations.empty' | t:lang()"
          />
        } @else {
          <ul class="ent-list">
            @for (r of recs; track r.id) {
              <li>
                <strong>{{ r.title }}</strong>
                <p>{{ r.rationale }}</p>
                <small>
                  {{ r.rule_code }} | {{ 'businessAnalytics.recommendations.notAi' | t:lang() }}:
                  {{ r.is_ai ? ('common.yes' | t:lang()) : ('common.no' | t:lang()) }} | {{ r.evidence_ref }}
                </small>
              </li>
            }
          </ul>
        }
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
  orgId: number | null = null;

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    if (this.orgId) this.load();
  }

  load(): void {
    const orgId = this.orgId;
    if (!orgId) return;
    this.api.generateRecommendations(orgId).subscribe((r) => (this.recs = r));
  }

  generate(): void {
    this.load();
  }
}
