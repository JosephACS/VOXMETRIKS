import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { CrmApiError, CrmApiService } from '../services/crm-api.service';
import { CrmContextService } from '../services/crm-context.service';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
interface DashStats {
  prospects: number;
  opportunities: number;
  approvalsPending: number;
  activities: number;
}

@Component({
  selector: 'app-crm-dashboard-page',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe],
  styleUrls: ['../styles/crm.css'],
  template: `
    <section class="crm-page" data-testid="crm-dashboard-page">
      <h1>{{ 'crm.dashboard.title' | t:lang() }}</h1>
      <p class="lede">
        Resumen comercial. Roles activos:
        <strong>{{ roles().join(', ') || '—' }}</strong>
      </p>

      @if (error()) {
        <div class="crm-alert crm-alert--error" role="alert">{{ error() }}</div>
      }

      @if (loading()) {
        <p class="crm-muted">Cargando estadísticas…</p>
      } @else {
        <div class="crm-stats-grid">
          <div class="crm-stat">
            <div class="crm-stat__value">{{ stats().prospects }}</div>
            <div class="crm-stat__label">{{ 'crm.prospects.title' | t:lang() }}</div>
          </div>
          <div class="crm-stat">
            <div class="crm-stat__value">{{ stats().opportunities }}</div>
            <div class="crm-stat__label">Oportunidades</div>
          </div>
          <div class="crm-stat">
            <div class="crm-stat__value">{{ stats().approvalsPending }}</div>
            <div class="crm-stat__label">{{ 'crm.approvals.title' | t:lang() }}</div>
          </div>
          <div class="crm-stat">
            <div class="crm-stat__value">{{ stats().activities }}</div>
            <div class="crm-stat__label">Actividades recientes</div>
          </div>
        </div>
      }

      <div class="crm-card">
        <h2>Accesos rápidos</h2>
        <div class="crm-actions">
          <a class="crm-btn crm-btn--ghost" routerLink="/crm/prospects">Ver prospectos</a>
          <a class="crm-btn crm-btn--ghost" routerLink="/crm/opportunities">Pipeline</a>
          <a class="crm-btn crm-btn--ghost" routerLink="/crm/approvals">Aprobaciones</a>
          <a class="crm-btn crm-btn--ghost" routerLink="/crm/audit">{{ 'organizations.audit.title' | t:lang() }}</a>
        </div>
      </div>
    </section>
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
