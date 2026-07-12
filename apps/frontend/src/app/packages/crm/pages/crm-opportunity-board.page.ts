import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { CrmApiError, CrmApiService } from '../services/crm-api.service';
import { Opportunity, OPPORTUNITY_STAGES, OpportunityCreateRequest, Prospect } from '../models/crm.models';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { StatusLabelPipe } from '../../../shared/pipes/status-label.pipe';
import { LocaleDatePipe, LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';

@Component({
  selector: 'app-crm-opportunity-board-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, TranslatePipe, StatusLabelPipe, LocaleMoneyPipe, LocaleDatePipe],
  styleUrls: ['../styles/crm.css'],
  template: `
    <section class="crm-page" data-testid="crm-opportunity-board-page">
      <h1>{{ 'crm.opportunities.board' | t:lang() }}</h1>
      <p class="lede">Vista kanban por etapa.</p>

      @if (error()) {
        <div class="crm-alert crm-alert--error" role="alert">{{ error() }}</div>
      }
      @if (success()) {
        <div class="crm-alert crm-alert--ok" role="status">{{ success() }}</div>
      }

      <!-- Create opportunity -->
      <div class="crm-card">
        <button type="button" class="crm-btn crm-btn--ghost" (click)="showCreate = !showCreate">
          {{ showCreate ? 'Cancelar' : '+ Nueva oportunidad' }}
        </button>
        @if (showCreate) {
          <form class="crm-form" style="margin-top:1rem" (ngSubmit)="create()">
            <label>Prospecto *
              <select [(ngModel)]="form.prospect_id" name="prospect_id" required>
                <option [ngValue]="0">— Selecciona prospecto —</option>
                @for (p of prospects(); track p.id) {
                  <option [ngValue]="p.id">{{ p.display_name }} ({{ p.company_name || '#' + p.id }})</option>
                }
              </select>
            </label>
            <label>Nombre *
              <input [(ngModel)]="form.name" name="name" required placeholder="Nombre de la oportunidad" />
            </label>
            <label>Valor esperado
              <input [(ngModel)]="form.expected_value" name="expected_value" type="number" min="0" placeholder="0.00" />
            </label>
            <label>Moneda
              <input [(ngModel)]="form.currency" name="currency" placeholder="USD" maxlength="3" />
            </label>
            <label>Probabilidad (0–100)
              <input [(ngModel)]="form.probability" name="probability" type="number" min="0" max="100" placeholder="50" />
            </label>
            <div class="crm-actions">
              <button type="submit" class="crm-btn"
                [disabled]="!form.name || !form.prospect_id || saving()">
                {{ saving() ? 'Creando…' : 'Crear' }}
              </button>
            </div>
          </form>
        }
      </div>

      @if (loading()) {
        <p class="crm-muted">Cargando pipeline…</p>
      } @else {
        <div class="crm-board">
          @for (stage of stages; track stage) {
            <div class="crm-board-col">
              <h3>{{ stage }} <span class="crm-muted">({{ byStage(stage).length }})</span></h3>
              @if (!byStage(stage).length) {
                <p class="crm-muted" style="font-size:0.78rem">{{ 'crm.opportunities.empty' | t:lang() }}</p>
              }
              @for (opp of byStage(stage); track opp.id) {
                <a class="crm-board-item" [routerLink]="['/crm/opportunities', opp.id]">
                  <strong>{{ opp.name }}</strong>
                  @if (opp.expected_value) {
                    <div class="crm-muted">{{ opp.currency || 'USD' }} {{ opp.expected_value | number:'1.0-0' }}</div>
                  }
                  @if (opp.probability != null) {
                    <div class="crm-muted">{{ opp.probability }}% prob.</div>
                  }
                </a>
              }
            </div>
          }
        </div>
        <p class="crm-muted" style="margin-top:0.75rem">
          Total: {{ items().length }} oportunidades
        </p>
      }
    </section>
  `,
})
export class CrmOpportunityBoardPageComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private readonly api = inject(CrmApiService);

  readonly stages = [...OPPORTUNITY_STAGES];

  showCreate = false;
  form: OpportunityCreateRequest = { prospect_id: 0, name: '' };

  readonly items = signal<Opportunity[]>([]);
  readonly prospects = signal<Prospect[]>([]);
  readonly loading = signal(true);
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);
  readonly success = signal<string | null>(null);

  byStage(stage: string): Opportunity[] {
    return this.items().filter((o) => o.stage === stage);
  }

  async ngOnInit(): Promise<void> {
    await this.load();
  }

  async load(): Promise<void> {
    this.loading.set(true);
    this.error.set(null);
    this.success.set(null);
    try {
      const [opps, pros] = await Promise.all([
        firstValueFrom(this.api.listOpportunities(1, 100)),
        firstValueFrom(this.api.listProspects(1, 100)),
      ]);
      this.items.set(opps.items);
      this.prospects.set(pros.items);
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al cargar oportunidades');
    } finally {
      this.loading.set(false);
    }
  }

  async create(): Promise<void> {
    if (!this.form.name || !this.form.prospect_id) return;
    this.saving.set(true);
    this.error.set(null);
    try {
      await firstValueFrom(this.api.createOpportunity(this.form));
      this.form = { prospect_id: 0, name: '' };
      this.showCreate = false;
      this.success.set('Oportunidad creada.');
      await this.load();
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al crear oportunidad');
    } finally {
      this.saving.set(false);
    }
  }
}
