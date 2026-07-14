import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { CrmApiError, CrmApiService } from '../services/crm-api.service';
import { Opportunity, OPPORTUNITY_STAGES, OpportunityCreateRequest, Prospect } from '../models/crm.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { StatusLabelPipe } from '../../../shared/pipes/status-label.pipe';
import { LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-crm-opportunity-board-page',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink,
    TranslatePipe,
    StatusLabelPipe,
    LocaleMoneyPipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  styleUrls: ['../styles/crm.css'],
  template: `
    <div class="vx-enterprise crm-page" data-testid="crm-opportunity-board-page">
      <app-enterprise-page-header
        [title]="'crm.opportunities.board' | t:lang()"
        [subtitle]="'crm.opportunities.subtitle' | t:lang()"
      >
        <button type="button" class="btn btn--secondary" (click)="showCreate = !showCreate">
          {{ (showCreate ? 'common.cancel' : 'crm.opportunities.create') | t:lang() }}
        </button>
      </app-enterprise-page-header>

      @if (error()) {
        <app-enterprise-error-state [message]="error()!" (retry)="load()" />
      }
      @if (success()) {
        <div class="alert alert--success" role="status">{{ success() }}</div>
      }

      @if (showCreate) {
        <app-enterprise-section-card [title]="'crm.opportunities.create' | t:lang()">
          <form class="form-grid" (ngSubmit)="create()">
            <app-enterprise-form-field [label]="'crm.opportunities.prospect' | t:lang()" [required]="true">
              <select class="select" [(ngModel)]="form.prospect_id" name="prospect_id" required>
                <option [ngValue]="0">{{ 'crm.opportunities.selectProspect' | t:lang() }}</option>
                @for (p of prospects(); track p.id) {
                  <option [ngValue]="p.id">{{ p.display_name }} ({{ p.company_name || '#' + p.id }})</option>
                }
              </select>
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'common.name' | t:lang()" [required]="true">
              <input
                class="input"
                [(ngModel)]="form.name"
                name="name"
                required
                [placeholder]="'crm.opportunities.namePlaceholder' | t:lang()"
              />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'crm.opportunities.expectedValue' | t:lang()">
              <input class="input" [(ngModel)]="form.expected_value" name="expected_value" type="number" min="0" />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'common.currency' | t:lang()">
              <input class="input" [(ngModel)]="form.currency" name="currency" maxlength="3" placeholder="USD" />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'crm.opportunities.probability' | t:lang()">
              <input class="input" [(ngModel)]="form.probability" name="probability" type="number" min="0" max="100" />
            </app-enterprise-form-field>
            <div class="form-grid__actions">
              <button type="submit" class="btn btn--primary" [disabled]="!form.name || !form.prospect_id || saving()">
                {{ (saving() ? 'crm.contacts.creating' : 'common.create') | t:lang() }}
              </button>
            </div>
          </form>
        </app-enterprise-section-card>
      }

      @if (loading()) {
        <app-enterprise-loading-skeleton [rows]="3" />
        <p class="muted">{{ 'crm.opportunities.loadingPipeline' | t:lang() }}</p>
      } @else {
        <div class="crm-board">
          @for (stage of stages; track stage) {
            <div class="crm-board-col">
              <h3>{{ stage | statusLabel }} <span class="muted">({{ byStage(stage).length }})</span></h3>
              @if (!byStage(stage).length) {
                <p class="muted" style="font-size: 0.78rem">{{ 'crm.opportunities.empty' | t:lang() }}</p>
              }
              @for (opp of byStage(stage); track opp.id) {
                <a class="crm-board-item" [routerLink]="['/crm/opportunities', opp.id]">
                  <strong>{{ opp.name }}</strong>
                  @if (opp.expected_value) {
                    <div class="muted">{{ opp.expected_value | localeMoney:opp.currency || 'USD' }}</div>
                  }
                  @if (opp.probability != null) {
                    <div class="muted">{{ 'crm.opportunities.probShort' | t:{ pct: opp.probability }:lang() }}</div>
                  }
                </a>
              }
            </div>
          }
        </div>
        <p class="muted">
          {{ 'crm.opportunities.totalCount' | t:{ count: items().length }:lang() }}
        </p>
      }
    </div>
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
      this.success.set(this.i18n.t('crm.opportunities.createdMsg'));
      await this.load();
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al crear oportunidad');
    } finally {
      this.saving.set(false);
    }
  }
}
