import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { CrmApiError, CrmApiService } from '../services/crm-api.service';
import { Opportunity, OpportunityStageHistory } from '../models/crm.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { LocaleDatePipe, LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-crm-lost-opportunity-page',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    TranslatePipe,
    LocaleDatePipe,
    LocaleMoneyPipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  styleUrls: ['../styles/crm.css'],
  template: `
    <div class="vx-enterprise crm-page" data-testid="crm-lost-opportunity-page">
      <app-enterprise-page-header [title]="('crm.lostOpportunity.closed' | t:lang()) + ' #' + oppId">
        <a class="btn btn--ghost" routerLink="/crm/opportunities">
          ← {{ 'crm.lostOpportunity.backPipeline' | t:lang() }}
        </a>
        @if (opp()) {
          <app-enterprise-status-badge [status]="opp()!.stage" />
          @if (opp()!.outcome) {
            <app-enterprise-status-badge [status]="opp()!.outcome || 'unknown'" />
          }
        }
      </app-enterprise-page-header>

      @if (error()) {
        <app-enterprise-error-state [message]="error()!" (retry)="load()" />
      }

      @if (loading()) {
        <app-enterprise-loading-skeleton [rows]="3" />
      } @else if (opp()) {
        <app-enterprise-section-card [title]="opp()!.name">
          @if (opp()!.description) {
            <p>{{ opp()!.description }}</p>
          }
          <div class="form-grid" style="font-size: 0.875rem; margin-top: 0.5rem">
            <div>
              <dt class="muted">{{ 'crm.lostOpportunity.finalStage' | t:lang() }}</dt>
              <dd><app-enterprise-status-badge [status]="opp()!.stage" /></dd>
            </div>
            <div>
              <dt class="muted">{{ 'crm.lostOpportunity.result' | t:lang() }}</dt>
              <dd>{{ opp()!.outcome || ('common.notAvailable' | t:lang()) }}</dd>
            </div>
            @if (opp()!.expected_value) {
              <div>
                <dt class="muted">{{ 'crm.lostOpportunity.expectedValue' | t:lang() }}</dt>
                <dd>{{ opp()!.expected_value | localeMoney:opp()!.currency || 'USD' }}</dd>
              </div>
            }
            @if (opp()!.probability != null) {
              <div>
                <dt class="muted">{{ 'crm.lostOpportunity.closeProbability' | t:lang() }}</dt>
                <dd>{{ opp()!.probability }}%</dd>
              </div>
            }
            <div>
              <dt class="muted">{{ 'crm.lostOpportunity.expectedCloseDate' | t:lang() }}</dt>
              <dd>{{ opp()!.expected_close_date | localeDate }}</dd>
            </div>
            <div>
              <dt class="muted">{{ 'crm.lostOpportunity.actualCloseDate' | t:lang() }}</dt>
              <dd>{{ opp()!.actual_close_date | localeDate }}</dd>
            </div>
            <div>
              <dt class="muted">{{ 'crm.lostOpportunity.prospect' | t:lang() }}</dt>
              <dd>
                <a [routerLink]="['/crm/prospects', opp()!.prospect_id]">#{{ opp()!.prospect_id }}</a>
              </dd>
            </div>
            <div>
              <dt class="muted">{{ 'common.created' | t:lang() }}</dt>
              <dd>{{ opp()!.created_at | localeDate:true }}</dd>
            </div>
          </div>
        </app-enterprise-section-card>

        @if (history().length) {
          <app-enterprise-section-card [title]="'crm.lostOpportunity.history' | t:lang()">
            <app-enterprise-data-table>
              <table class="data-table">
                <thead>
                  <tr>
                    <th>{{ 'common.from' | t:lang() }}</th>
                    <th>{{ 'common.to' | t:lang() }}</th>
                    <th>{{ 'common.reason' | t:lang() }}</th>
                    <th>{{ 'common.date' | t:lang() }}</th>
                  </tr>
                </thead>
                <tbody>
                  @for (h of history(); track h.id) {
                    <tr>
                      <td>{{ h.from_stage || ('common.notAvailable' | t:lang()) }}</td>
                      <td>{{ h.to_stage }}</td>
                      <td>{{ h.reason || ('common.notAvailable' | t:lang()) }}</td>
                      <td class="muted">{{ h.occurred_at | localeDate:true }}</td>
                    </tr>
                  }
                </tbody>
              </table>
            </app-enterprise-data-table>
          </app-enterprise-section-card>
        }

        <app-enterprise-action-bar>
          <a class="btn btn--ghost" [routerLink]="['/crm/opportunities', oppId]">
            {{ 'crm.lostOpportunity.viewFull' | t:lang() }}
          </a>
        </app-enterprise-action-bar>
      }
    </div>
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
