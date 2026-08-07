import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { OrganizationContextService } from '../services/organization-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';

@Component({
  selector: 'app-business-for-enterprises-page',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe],
  styleUrls: ['../styles/organizations.css'],
  template: `
    <section class="org-page" data-testid="business-for-enterprises-page">
      <h1>{{ 'business.forEnterprises.title' | t:lang() }}</h1>
      <p class="lede">{{ 'business.forEnterprises.lede' | t:lang() }}</p>

      <div class="org-card">
        <p>{{ 'business.forEnterprises.body' | t:lang() }}</p>
        <div class="org-actions">
          <a class="org-btn" routerLink="/subscriptions/plans" [class.org-btn--ghost]="!hasOrg()">
            {{ 'business.forEnterprises.ctaPlans' | t:lang() }}
          </a>
          @if (!hasOrg()) {
            <a class="org-btn" routerLink="/organizations/new">
              {{ 'business.forEnterprises.ctaCreate' | t:lang() }}
            </a>
          } @else if (awaitingPlan()) {
            <a class="org-btn" routerLink="/subscriptions/trial">
              {{ 'business.forEnterprises.ctaTrial' | t:lang() }}
            </a>
            <a class="org-btn org-btn--ghost" routerLink="/subscriptions/select-plan">
              {{ 'business.forEnterprises.ctaChoosePlan' | t:lang() }}
            </a>
          } @else {
            <a class="org-btn org-btn--ghost" [routerLink]="['/organizations', orgId(), 'settings']">
              {{ 'business.forEnterprises.ctaOpenOrg' | t:lang() }}
            </a>
          }
          <a class="org-btn org-btn--ghost" routerLink="/discover">
            {{ 'business.forEnterprises.ctaPersonal' | t:lang() }}
          </a>
        </div>
      </div>
    </section>
  `,
})
export class BusinessForEnterprisesPageComponent implements OnInit {
  private readonly i18n = inject(I18nService);
  readonly lang = this.i18n.lang;
  readonly ctx = inject(OrganizationContextService);

  readonly hasOrg = signal(false);
  readonly awaitingPlan = signal(false);
  readonly orgId = signal<number | null>(null);

  async ngOnInit(): Promise<void> {
    await this.ctx.ensureReady();
    this.hasOrg.set(this.ctx.hasOrganization());
    this.orgId.set(this.ctx.organizationId());
    this.awaitingPlan.set(this.ctx.accessTier() === 'onboarding');
  }
}
