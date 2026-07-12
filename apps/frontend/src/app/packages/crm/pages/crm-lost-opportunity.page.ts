import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { CrmApiError, CrmApiService } from '../services/crm-api.service';
import { Opportunity, OpportunityStageHistory } from '../models/crm.models';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { StatusLabelPipe } from '../../../shared/pipes/status-label.pipe';
import { LocaleDatePipe, LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';

@Component({
  selector: 'app-crm-lost-opportunity-page',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe, StatusLabelPipe, LocaleMoneyPipe, LocaleDatePipe],
  styleUrls: ['../styles/crm.css'],
  template: `
    <section class="crm-page" data-testid="crm-lost-opportunity-page">
      <div style="display:flex;align-items:center;gap:0.75rem;flex-wrap:wrap;margin-bottom:0.5rem">
        <a class="crm-btn crm-btn--ghost" routerLink="/crm/opportunities">← Pipeline</a>
        <h1 style="margin:0">Oportunidad cerrada #{{ oppId }}</h1>
        @if (opp()) {
          <span class="crm-badge crm-badge--{{ opp()!.stage }}">{{ opp()!.stage }}</span>
          @if (opp()!.outcome) {
            <span class="crm-badge crm-badge--{{ opp()!.outcome }}">{{ opp()!.outcome }}</span>
          }
        }
      </div>

      @if (error()) {
        <div class="crm-alert crm-alert--error" role="alert">{{ error() }}</div>
      }

      @if (loading()) {
        <p class="crm-muted">{{ 'common.loading' | t:lang() }}</p>
      } @else if (opp()) {
        <div class="crm-card">
          <h2>{{ opp()!.name }}</h2>
          @if (opp()!.description) {
            <p>{{ opp()!.description }}</p>
          }
          <dl style="display:grid;grid-template-columns:auto 1fr;gap:0.3rem 1rem;font-size:0.875rem;margin-top:0.5rem">
            <dt class="crm-muted">Etapa final</dt>
            <dd><span class="crm-badge crm-badge--{{ opp()!.stage }}">{{ opp()!.stage }}</span></dd>
            <dt class="crm-muted">Resultado</dt>
            <dd>{{ opp()!.outcome || '—' }}</dd>
            @if (opp()!.expected_value) {
              <dt class="crm-muted">Valor esperado</dt>
              <dd>{{ opp()!.currency || 'USD' }} {{ opp()!.expected_value | number:'1.2-2' }}</dd>
            }
            @if (opp()!.probability != null) {
              <dt class="crm-muted">Probabilidad al cerrar</dt>
              <dd>{{ opp()!.probability }}%</dd>
            }
            <dt class="crm-muted">Fecha cierre esperada</dt>
            <dd>{{ (opp()!.expected_close_date | date:'shortDate') || '—' }}</dd>
            <dt class="crm-muted">Fecha cierre real</dt>
            <dd>{{ (opp()!.actual_close_date | date:'shortDate') || '—' }}</dd>
            <dt class="crm-muted">Prospecto</dt>
            <dd>
              <a [routerLink]="['/crm/prospects', opp()!.prospect_id]">#{{ opp()!.prospect_id }}</a>
            </dd>
            <dt class="crm-muted">Creada</dt>
            <dd>{{ opp()!.created_at | date:'medium' }}</dd>
          </dl>
        </div>

        <!-- Stage history -->
        @if (history().length) {
          <div class="crm-card">
            <h2>Historial de etapas</h2>
            <table class="crm-table">
              <thead>
                <tr><th>Desde</th><th>Hacia</th><th>Motivo</th><th>Fecha</th></tr>
              </thead>
              <tbody>
                @for (h of history(); track h.id) {
                  <tr>
                    <td>{{ h.from_stage || '—' }}</td>
                    <td>{{ h.to_stage }}</td>
                    <td>{{ h.reason || '—' }}</td>
                    <td class="crm-muted">{{ h.occurred_at | date:'short' }}</td>
                  </tr>
                }
              </tbody>
            </table>
          </div>
        }

        <div class="crm-actions">
          <a class="crm-btn crm-btn--ghost" [routerLink]="['/crm/opportunities', oppId]">
            Ver detalle completo
          </a>
        </div>
      }
    </section>
  `,
})
export class CrmLostOpportunityPageComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private readonly api = inject(CrmApiService);
  private readonly route = inject(ActivatedRoute);

  oppId = 0;

  readonly opp = signal<Opportunity | null>(null);
  readonly history = signal<OpportunityStageHistory[]>([]);
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);

  async ngOnInit(): Promise<void> {
    this.oppId = Number(this.route.snapshot.paramMap.get('id'));
    await this.load();
  }

  async load(): Promise<void> {
    this.loading.set(true);
    this.error.set(null);
    try {
      const [o, hist] = await Promise.all([
        firstValueFrom(this.api.getOpportunity(this.oppId)),
        firstValueFrom(this.api.getOpportunityStageHistory(this.oppId)),
      ]);
      this.opp.set(o);
      this.history.set(hist);
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al cargar oportunidad');
    } finally {
      this.loading.set(false);
    }
  }
}
