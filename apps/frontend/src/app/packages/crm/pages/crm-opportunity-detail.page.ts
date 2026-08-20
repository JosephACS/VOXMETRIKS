import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { CrmApiError, CrmApiService } from '../services/crm-api.service';
import {
  Opportunity,
  OpportunityStageHistory,
  Quotation,
  SalesActivity,
  CommercialContract,
  CustomerConversion,
  OPPORTUNITY_STAGES,
} from '../models/crm.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { StatusLabelPipe } from '../../../shared/pipes/status-label.pipe';
import { LocaleDatePipe } from '../../../shared/pipes/locale-format.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-crm-opportunity-detail-page',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink,
    TranslatePipe,
    StatusLabelPipe,
    LocaleDatePipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  styleUrls: ['../styles/crm.css'],
  template: `
    <div class="vx-enterprise crm-page" data-testid="crm-opportunity-detail-page">
      <app-enterprise-page-header [title]="opp()?.name || ('crm.lostOpportunity.closed' | t:lang()) + ' #' + oppId">
        <a class="btn btn--ghost" routerLink="/crm/opportunities">
          ← {{ 'crm.opportunityDetail.backPipeline' | t:lang() }}
        </a>
        @if (opp()) {
          <app-enterprise-status-badge [status]="opp()!.stage" />
        }
      </app-enterprise-page-header>

      @if (error()) {
        <app-enterprise-error-state [message]="error()!" (retry)="load()" />
      }
      @if (success()) {
        <div class="alert alert--success" role="status">{{ success() }}</div>
      }

      @if (loading()) {
        <app-enterprise-loading-skeleton [rows]="4" />
      } @else if (opp()) {
        <app-enterprise-section-card [title]="'crm.opportunityDetail.data' | t:lang()">
          <form class="form-grid" (ngSubmit)="saveOpp()">
            <app-enterprise-form-field [label]="'common.name' | t:lang()" [required]="true">
              <input class="input" [(ngModel)]="editForm.name" name="name" required />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'common.description' | t:lang()">
              <textarea class="input" [(ngModel)]="editForm.description" name="description" rows="2"></textarea>
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'crm.opportunities.expectedValue' | t:lang()">
              <input class="input" [(ngModel)]="editForm.expected_value" name="expected_value" type="number" min="0" />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'common.currency' | t:lang()">
              <input class="input" [(ngModel)]="editForm.currency" name="currency" maxlength="3" />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'crm.opportunities.probability' | t:lang()">
              <input class="input" [(ngModel)]="editForm.probability" name="probability" type="number" min="0" max="100" />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'crm.opportunityDetail.closeDate' | t:lang()">
              <input class="input" [(ngModel)]="editForm.expected_close_date" name="expected_close_date" type="date" />
            </app-enterprise-form-field>
            <div class="form-grid__actions">
              <button type="submit" class="btn btn--primary" [disabled]="saving()">
                {{ (saving() ? 'common.saving' : 'common.save') | t:lang() }}
              </button>
            </div>
          </form>
        </app-enterprise-section-card>

        @if (!isClosedStage()) {
          <app-enterprise-section-card [title]="'crm.opportunityDetail.advance' | t:lang()">
            <form class="form-grid">
              <app-enterprise-form-field [label]="'crm.opportunityDetail.newStage' | t:lang()">
                <select class="select" [(ngModel)]="newStage" name="newStage">
                  @for (s of openStages; track s) {
                    <option [value]="s" [disabled]="s === opp()!.stage">{{ s | statusLabel }}</option>
                  }
                </select>
              </app-enterprise-form-field>
              <app-enterprise-form-field [label]="'common.reasonOptional' | t:lang()">
                <input class="input" [(ngModel)]="stageReason" name="stageReason" />
              </app-enterprise-form-field>
              <app-enterprise-action-bar>
                <button
                  type="button"
                  class="btn btn--secondary"
                  [disabled]="!newStage || newStage === opp()!.stage || saving()"
                  (click)="advanceStage()"
                >
                  {{ 'crm.opportunityDetail.advance' | t:lang() }}
                </button>
                <button type="button" class="btn btn--danger" [disabled]="saving()" (click)="showCloseForm = !showCloseForm">
                  {{ 'crm.opportunityDetail.close' | t:lang() }}
                </button>
              </app-enterprise-action-bar>
            </form>

            @if (showCloseForm) {
              <div style="margin-top: 1rem; border-top: 1px solid var(--border, #30363d); padding-top: 1rem">
                <h3 style="font-size: 0.95rem; margin: 0 0 0.6rem">{{ 'crm.opportunityDetail.close' | t:lang() }}</h3>
                <form class="form-grid">
                  <app-enterprise-form-field [label]="'crm.opportunityDetail.outcome' | t:lang()" [required]="true">
                    <select class="select" [(ngModel)]="closeOutcome" name="closeOutcome">
                      <option value="won">{{ 'closed_won' | statusLabel }}</option>
                      <option value="lost">{{ 'closed_lost' | statusLabel }}</option>
                      <option value="canceled">{{ 'canceled' | statusLabel }}</option>
                    </select>
                  </app-enterprise-form-field>
                  <app-enterprise-form-field [label]="'crm.opportunityDetail.finalStage' | t:lang()" [required]="true">
                    <select class="select" [(ngModel)]="closeStage" name="closeStage">
                      <option value="closed_won">{{ 'closed_won' | statusLabel }}</option>
                      <option value="closed_lost">{{ 'closed_lost' | statusLabel }}</option>
                      <option value="canceled">{{ 'canceled' | statusLabel }}</option>
                    </select>
                  </app-enterprise-form-field>
                  <app-enterprise-form-field [label]="'common.reason' | t:lang()">
                    <input class="input" [(ngModel)]="closeReason" name="closeReason" />
                  </app-enterprise-form-field>
                  <div class="form-grid__actions">
                    <button type="button" class="btn btn--danger" [disabled]="saving()" (click)="closeOpp()">
                      {{ 'crm.opportunityDetail.confirmClose' | t:lang() }}
                    </button>
                  </div>
                </form>
              </div>
            }
          </app-enterprise-section-card>
        }

        @if (history().length) {
          <app-enterprise-section-card [title]="'crm.opportunityDetail.stageHistory' | t:lang()">
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
                      <td>
                        @if (h.from_stage) {
                          {{ h.from_stage | statusLabel }}
                        } @else {
                          {{ 'common.notAvailable' | t:lang() }}
                        }
                      </td>
                      <td>{{ h.to_stage | statusLabel }}</td>
                      <td>{{ h.reason || ('common.notAvailable' | t:lang()) }}</td>
                      <td class="muted">{{ h.occurred_at | localeDate:true }}</td>
                    </tr>
                  }
                </tbody>
              </table>
            </app-enterprise-data-table>
          </app-enterprise-section-card>
        }

        <app-enterprise-section-card [title]="'crm.opportunityDetail.quotations' | t:lang()">
          @if (quotations().length) {
            <app-enterprise-data-table>
              <table class="data-table">
                <thead>
                  <tr>
                    <th>{{ 'common.id' | t:lang() }}</th>
                    <th>{{ 'common.status' | t:lang() }}</th>
                    <th>{{ 'common.currency' | t:lang() }}</th>
                    <th>{{ 'crm.opportunityDetail.currentVersion' | t:lang() }}</th>
                  </tr>
                </thead>
                <tbody>
                  @for (q of quotations(); track q.id) {
                    <tr>
                      <td><a [routerLink]="['/crm/quotations', q.id]">Q-{{ q.id }}</a></td>
                      <td><app-enterprise-status-badge [status]="q.status" /></td>
                      <td>{{ q.currency || ('common.notAvailable' | t:lang()) }}</td>
                      <td>v{{ q.current_version_no ?? ('common.notAvailable' | t:lang()) }}</td>
                    </tr>
                  }
                </tbody>
              </table>
            </app-enterprise-data-table>
          } @else {
            <app-enterprise-empty-state [title]="'crm.opportunityDetail.noQuotations' | t:lang()" />
          }
          <app-enterprise-action-bar>
            <button type="button" class="btn btn--secondary" [disabled]="saving()" (click)="createQuotation()">
              + {{ 'crm.opportunityDetail.createQuotation' | t:lang() }}
            </button>
          </app-enterprise-action-bar>
        </app-enterprise-section-card>

        <app-enterprise-section-card [title]="'crm.opportunityDetail.contracts' | t:lang()">
          @if (contracts().length) {
            <app-enterprise-data-table>
              <table class="data-table">
                <thead>
                  <tr>
                    <th>{{ 'common.id' | t:lang() }}</th>
                    <th>{{ 'crm.opportunityDetail.legalName' | t:lang() }}</th>
                    <th>{{ 'common.status' | t:lang() }}</th>
                  </tr>
                </thead>
                <tbody>
                  @for (c of contracts(); track c.id) {
                    <tr>
                      <td><a [routerLink]="['/crm/contracts', c.id]">C-{{ c.id }}</a></td>
                      <td>{{ c.legal_name || ('common.notAvailable' | t:lang()) }}</td>
                      <td><app-enterprise-status-badge [status]="c.status" /></td>
                    </tr>
                  }
                </tbody>
              </table>
            </app-enterprise-data-table>
          } @else {
            <app-enterprise-empty-state
              [title]="'crm.opportunityDetail.noContracts' | t:lang()"
              [description]="'crm.opportunityDetail.noContractsHint' | t:lang()"
            />
          }
        </app-enterprise-section-card>

        <app-enterprise-section-card [title]="'crm.opportunityDetail.conversion' | t:lang()">
          <p class="muted">{{ 'crm.opportunityDetail.conversionHint' | t:lang() }}</p>
          @if (conversions().length) {
            <app-enterprise-data-table>
              <table class="data-table">
                <thead>
                  <tr>
                    <th>{{ 'common.id' | t:lang() }}</th>
                    <th>{{ 'common.mode' | t:lang() }}</th>
                    <th>{{ 'common.status' | t:lang() }}</th>
                    <th>{{ 'common.organization' | t:lang() }}</th>
                  </tr>
                </thead>
                <tbody>
                  @for (cv of conversions(); track cv.id) {
                    <tr>
                      <td><a [routerLink]="['/crm/conversions', cv.id]">CV-{{ cv.id }}</a></td>
                      <td>{{ cv.mode }}</td>
                      <td><app-enterprise-status-badge [status]="cv.status" /></td>
                      <td>{{ cv.organization_id ?? ('common.notAvailable' | t:lang()) }}</td>
                    </tr>
                  }
                </tbody>
              </table>
            </app-enterprise-data-table>
          } @else {
            <app-enterprise-empty-state [title]="'crm.opportunityDetail.noConversions' | t:lang()" />
          }
          <app-enterprise-action-bar>
            <button type="button" class="btn btn--primary" [disabled]="saving()" (click)="prepareConversion('link_existing')">
              {{ 'crm.opportunityDetail.prepareLinkOrg' | t:lang() }}
            </button>
            <button type="button" class="btn btn--secondary" [disabled]="saving()" (click)="prepareConversion('create_org')">
              {{ 'crm.opportunityDetail.prepareCreateOrg' | t:lang() }}
            </button>
          </app-enterprise-action-bar>
        </app-enterprise-section-card>

        <app-enterprise-section-card [title]="'crm.opportunityDetail.activities' | t:lang()">
          @if (activities().length) {
            <app-enterprise-data-table>
              <table class="data-table">
                <thead>
                  <tr>
                    <th>{{ 'common.type' | t:lang() }}</th>
                    <th>{{ 'crm.opportunityDetail.subject' | t:lang() }}</th>
                    <th>{{ 'common.status' | t:lang() }}</th>
                    <th>{{ 'common.date' | t:lang() }}</th>
                  </tr>
                </thead>
                <tbody>
                  @for (a of activities(); track a.id) {
                    <tr>
                      <td>{{ a.activity_type }}</td>
                      <td>{{ a.subject }}</td>
                      <td><app-enterprise-status-badge [status]="a.status" /></td>
                      <td class="muted">{{ a.created_at | localeDate }}</td>
                    </tr>
                  }
                </tbody>
              </table>
            </app-enterprise-data-table>
          } @else {
            <app-enterprise-empty-state [title]="'crm.opportunityDetail.noActivities' | t:lang()" />
          }
          <app-enterprise-action-bar>
            <button type="button" class="btn btn--secondary" (click)="showActivityForm = !showActivityForm">
              {{ (showActivityForm ? 'common.cancel' : 'crm.opportunityDetail.addActivity') | t:lang() }}
            </button>
          </app-enterprise-action-bar>
          @if (showActivityForm) {
            <form class="form-grid" style="margin-top: 0.75rem" (ngSubmit)="createActivity()">
              <app-enterprise-form-field [label]="'common.type' | t:lang()" [required]="true">
                <select class="select" [(ngModel)]="actForm.activity_type" name="activity_type" required>
                  <option value="call">{{ 'crm.opportunityDetail.activityType.call' | t:lang() }}</option>
                  <option value="email">{{ 'crm.opportunityDetail.activityType.email' | t:lang() }}</option>
                  <option value="meeting">{{ 'crm.opportunityDetail.activityType.meeting' | t:lang() }}</option>
                  <option value="demo">{{ 'crm.opportunityDetail.activityType.demo' | t:lang() }}</option>
                  <option value="note">{{ 'crm.opportunityDetail.activityType.note' | t:lang() }}</option>
                </select>
              </app-enterprise-form-field>
              <app-enterprise-form-field [label]="'crm.opportunityDetail.subject' | t:lang()" [required]="true">
                <input class="input" [(ngModel)]="actForm.subject" name="subject" required />
              </app-enterprise-form-field>
              <app-enterprise-form-field [label]="'crm.opportunityDetail.detail' | t:lang()">
                <textarea class="input" [(ngModel)]="actForm.body" name="body" rows="2"></textarea>
              </app-enterprise-form-field>
              <div class="form-grid__actions">
                <button type="submit" class="btn btn--primary" [disabled]="!actForm.subject || saving()">
                  {{ 'crm.opportunityDetail.saveActivity' | t:lang() }}
                </button>
              </div>
            </form>
          }
        </app-enterprise-section-card>

        <app-enterprise-section-card>
          <div class="form-grid muted" style="font-size: 0.875rem">
            <div>
              <dt>{{ 'crm.opportunityDetail.prospect' | t:lang() }}</dt>
              <dd>#{{ opp()!.prospect_id }}</dd>
            </div>
            <div>
              <dt>{{ 'common.created' | t:lang() }}</dt>
              <dd>{{ opp()!.created_at | localeDate:true }}</dd>
            </div>
            <div>
              <dt>{{ 'common.updated' | t:lang() }}</dt>
              <dd>{{ opp()!.updated_at | localeDate:true }}</dd>
            </div>
            @if (opp()!.actual_close_date) {
              <div>
                <dt>{{ 'crm.opportunityDetail.actualClose' | t:lang() }}</dt>
                <dd>{{ opp()!.actual_close_date | localeDate }}</dd>
              </div>
            }
          </div>
        </app-enterprise-section-card>
      }
    </div>
  `,
})
export class CrmOpportunityDetailPageComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private readonly api = inject(CrmApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly stages = [...OPPORTUNITY_STAGES];
  /** Stages selectable for advance (terminal stages use close). */
  readonly openStages = ['qualification', 'proposal', 'negotiation'] as const;

  oppId = 0;
  showCloseForm = false;
  showActivityForm = false;
  newStage = '';
  stageReason = '';
  closeOutcome = 'won';
  closeStage = 'closed_won';
  closeReason = '';

  editForm = {
    name: '',
    description: '',
    expected_value: 0,
    currency: 'USD',
    probability: 50,
    expected_close_date: '',
  };
  actForm = { activity_type: 'call', subject: '', body: '', opportunity_id: 0 };

  readonly opp = signal<Opportunity | null>(null);
  readonly history = signal<OpportunityStageHistory[]>([]);
  readonly quotations = signal<Quotation[]>([]);
  readonly contracts = signal<CommercialContract[]>([]);
  readonly conversions = signal<CustomerConversion[]>([]);
  readonly activities = signal<SalesActivity[]>([]);
  readonly loading = signal(true);
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);
  readonly success = signal<string | null>(null);
  /** One-time claim token from prepare (create_org); shown until leaving the page. */
  readonly claimTokenOnce = signal<string | null>(null);

  isClosedStage(): boolean {
    const s = this.opp()?.stage;
    return (
      s === 'closed_won' ||
      s === 'closed_lost' ||
      s === 'canceled' ||
      s === 'won' ||
      s === 'lost'
    );
  }

  async ngOnInit(): Promise<void> {
    this.oppId = Number(this.route.snapshot.paramMap.get('id'));
    this.actForm.opportunity_id = this.oppId;
    await this.load();
  }

  async load(): Promise<void> {
    this.loading.set(true);
    this.error.set(null);
    this.success.set(null);
    try {
      const [o, hist, quots, acts, contractsRes, conversionsRes] = await Promise.all([
        firstValueFrom(this.api.getOpportunity(this.oppId)),
        firstValueFrom(this.api.getOpportunityStageHistory(this.oppId)),
        firstValueFrom(this.api.listQuotations(1, 25, this.oppId)),
        firstValueFrom(this.api.listActivities(1, 25, this.oppId)),
        firstValueFrom(this.api.listContracts(1, 25, this.oppId)),
        firstValueFrom(this.api.listConversions(1, 25, this.oppId)),
      ]);
      this.opp.set(o);
      this.newStage = o.stage;
      this.editForm = {
        name: o.name,
        description: o.description ?? '',
        expected_value: o.expected_value ?? 0,
        currency: o.currency ?? 'USD',
        probability: o.probability ?? 50,
        expected_close_date: o.expected_close_date ?? '',
      };
      this.history.set(hist);
      this.quotations.set(quots.items);
      this.activities.set(acts.items);
      this.contracts.set(contractsRes.items ?? []);
      this.conversions.set(conversionsRes.items ?? []);
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al cargar oportunidad');
    } finally {
      this.loading.set(false);
    }
  }

  async saveOpp(): Promise<void> {
    if (!this.editForm.name) return;
    this.saving.set(true);
    this.error.set(null);
    try {
      const updated = await firstValueFrom(
        this.api.updateOpportunity(this.oppId, {
          name: this.editForm.name,
          description: this.editForm.description || undefined,
          expected_value: this.editForm.expected_value || undefined,
          currency: this.editForm.currency || undefined,
          probability: this.editForm.probability ?? undefined,
          expected_close_date: this.editForm.expected_close_date || undefined,
        }),
      );
      this.opp.set(updated);
      this.success.set('Oportunidad actualizada.');
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al guardar');
    } finally {
      this.saving.set(false);
    }
  }

  async advanceStage(): Promise<void> {
    if (!this.newStage) return;
    this.saving.set(true);
    this.error.set(null);
    try {
      const updated = await firstValueFrom(
        this.api.advanceOpportunityStage(this.oppId, this.newStage, this.stageReason || undefined),
      );
      this.opp.set(updated);
      this.stageReason = '';
      this.success.set(`Etapa avanzada a "${this.newStage}".`);
      const hist = await firstValueFrom(this.api.getOpportunityStageHistory(this.oppId));
      this.history.set(hist);
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al avanzar etapa');
    } finally {
      this.saving.set(false);
    }
  }

  async closeOpp(): Promise<void> {
    this.saving.set(true);
    this.error.set(null);
    try {
      const updated = await firstValueFrom(
        this.api.closeOpportunity(
          this.oppId,
          this.closeOutcome,
          this.closeStage,
          this.closeReason || undefined,
        ),
      );
      this.opp.set(updated);
      this.showCloseForm = false;
      this.success.set(`Oportunidad cerrada (${this.closeOutcome}).`);
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al cerrar oportunidad');
    } finally {
      this.saving.set(false);
    }
  }

  async createQuotation(): Promise<void> {
    this.saving.set(true);
    this.error.set(null);
    try {
      const q = await firstValueFrom(
        this.api.createQuotation({ opportunity_id: this.oppId, currency: this.editForm.currency || 'USD' }),
      );
      await this.router.navigate(['/crm/quotations', q.id]);
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al crear cotización');
      this.saving.set(false);
    }
  }

  async prepareConversion(mode: 'create_org' | 'link_existing'): Promise<void> {
    this.saving.set(true);
    this.error.set(null);
    this.claimTokenOnce.set(null);
    try {
      const res = await firstValueFrom(
        this.api.prepareConversion({ opportunity_id: this.oppId, mode }),
      );
      const token = res.claim_token?.trim() || null;
      this.success.set(
        this.i18n.t('crm.opportunityDetail.prepareSuccess', { id: res.conversion.id }),
      );
      if (token) {
        this.claimTokenOnce.set(token);
        await this.router.navigate(['/crm/conversions', res.conversion.id], {
          state: {
            claimToken: token,
            claimTokenNote: res.claim_token_note ?? null,
          },
        });
      } else {
        await this.router.navigate(['/crm/conversions', res.conversion.id]);
      }
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : this.i18n.t('crm.opportunityDetail.prepareError'));
      this.saving.set(false);
    }
  }

  async createActivity(): Promise<void> {
    if (!this.actForm.subject) return;
    this.saving.set(true);
    this.error.set(null);
    try {
      await firstValueFrom(this.api.createActivity({ ...this.actForm }));
      this.actForm = { activity_type: 'call', subject: '', body: '', opportunity_id: this.oppId };
      this.showActivityForm = false;
      this.success.set('Actividad registrada.');
      const acts = await firstValueFrom(this.api.listActivities(1, 25, this.oppId));
      this.activities.set(acts.items);
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al registrar actividad');
    } finally {
      this.saving.set(false);
    }
  }
}
