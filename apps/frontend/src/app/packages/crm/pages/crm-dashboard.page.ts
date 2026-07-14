import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { CrmApiError, CrmApiService } from '../services/crm-api.service';
import { CrmContextService } from '../services/crm-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

interface DashStats {
  prospects: number;
  opportunities: number;
  approvalsPending: number;
  activities: number;
}

@Component({
  selector: 'app-crm-dashboard-page',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  styleUrls: ['../styles/crm.css'],
  template: `
    <div class="vx-enterprise crm-page" data-testid="crm-dashboard-page">
      <app-enterprise-page-header
        [title]="'crm.dashboard.title' | t:lang()"
        [subtitle]="'crm.dashboard.subtitle' | t:lang()"
      />

      <p class="muted">
        {{ 'crm.dashboard.roles' | t:lang() }}:
        <strong>{{ roles().join(', ') || ('common.notAvailable' | t:lang()) }}</strong>
      </p>

      @if (error()) {
        <app-enterprise-error-state [message]="error()!" (retry)="ngOnInit()" />
      }

      @if (loading()) {
        <app-enterprise-loading-skeleton [rows]="2" />
      } @else {
        <div class="crm-stats-grid">
          <app-enterprise-stat-card
            [label]="'crm.dashboard.prospects' | t:lang()"
            [value]="stats().prospects"
          />
          <app-enterprise-stat-card
            [label]="'crm.dashboard.opportunities' | t:lang()"
            [value]="stats().opportunities"
          />
          <app-enterprise-stat-card
            [label]="'crm.approvals.title' | t:lang()"
            [value]="stats().approvalsPending"
          />
          <app-enterprise-stat-card
            [label]="'crm.dashboard.activities' | t:lang()"
            [value]="stats().activities"
          />
        </div>
      }

      <app-enterprise-section-card [title]="'crm.dashboard.quick' | t:lang()">
        <app-enterprise-action-bar>
          <a class="btn btn--ghost" routerLink="/crm/prospects">
            {{ 'crm.dashboard.viewProspects' | t:lang() }}
          </a>
          <a class="btn btn--ghost" routerLink="/crm/opportunities">
            {{ 'crm.dashboard.pipeline' | t:lang() }}
          </a>
          <a class="btn btn--ghost" routerLink="/crm/approvals">
            {{ 'crm.approvals.title' | t:lang() }}
          </a>
          <a class="btn btn--ghost" routerLink="/crm/audit">
            {{ 'organizations.audit.title' | t:lang() }}
          </a>
        </app-enterprise-action-bar>
      </app-enterprise-section-card>
    </div>
  `,
})
export class CrmDashboardPageComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private readonly api = inject(CrmApiService);
  private readonly ctx = inject(CrmContextService);

  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly stats = signal<DashStats>({ prospects: 0, opportunities: 0, approvalsPending: 0, activities: 0 });
  readonly roles = this.ctx.roles;

  async ngOnInit(): Promise<void> {
    this.loading.set(true);
    this.error.set(null);
    try {
      const [prospects, opportunities, activities] = await Promise.allSettled([
        firstValueFrom(this.api.listProspects(1, 1)),
        firstValueFrom(this.api.listOpportunities(1, 1)),
        firstValueFrom(this.api.listActivities(1, 1)),
      ]);

      let approvalsPending = 0;
      try {
        const appr = await firstValueFrom(this.api.listApprovals(1, 1));
        approvalsPending = appr.total;
      } catch {
        // User may not have approval permissions
      }

      this.stats.set({
        prospects: prospects.status === 'fulfilled' ? prospects.value.total : 0,
        opportunities: opportunities.status === 'fulfilled' ? opportunities.value.total : 0,
        approvalsPending,
        activities: activities.status === 'fulfilled' ? activities.value.total : 0,
      });
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al cargar el panel CRM');
    } finally {
      this.loading.set(false);
    }
  }
}
