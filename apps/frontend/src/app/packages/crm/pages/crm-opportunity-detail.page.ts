import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { CrmApiError, CrmApiService } from '../services/crm-api.service';
import { Opportunity, OpportunityStageHistory, Quotation, SalesActivity, CommercialContract, CustomerConversion, OPPORTUNITY_STAGES } from '../models/crm.models';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
@Component({
  selector: 'app-crm-opportunity-detail-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, TranslatePipe],
  styleUrls: ['../styles/crm.css'],
  template: `
    <section class="crm-page" data-testid="crm-opportunity-detail-page">
      <div style="display:flex;align-items:center;gap:0.75rem;flex-wrap:wrap;margin-bottom:0.5rem">
        <a class="crm-btn crm-btn--ghost" routerLink="/crm/opportunities">← Pipeline</a>
        <h1 style="margin:0">{{ opp()?.name || 'Oportunidad #' + oppId }}</h1>
        @if (opp()) {
          <span class="crm-badge crm-badge--{{ opp()!.stage }}">{{ opp()!.stage }}</span>
        }
      </div>

      @if (error()) {
        <div class="crm-alert crm-alert--error" role="alert">{{ error() }}</div>
      }
      @if (success()) {
        <div class="crm-alert crm-alert--ok" role="status">{{ success() }}</div>
      }

      @if (loading()) {
        <p class="crm-muted">{{ 'common.loading' | t:lang() }}</p>
      } @else if (opp()) {
        <!-- Opportunity data -->
        <div class="crm-card">
          <h2>Datos</h2>
          <form class="crm-form" (ngSubmit)="saveOpp()">
            <label>Nombre *
              <input [(ngModel)]="editForm.name" name="name" required />
            </label>
            <label>Descripción
              <textarea [(ngModel)]="editForm.description" name="description" rows="2"></textarea>
            </label>
            <label>Valor esperado
              <input [(ngModel)]="editForm.expected_value" name="expected_value" type="number" min="0" />
            </label>
            <label>Moneda
              <input [(ngModel)]="editForm.currency" name="currency" maxlength="3" />
            </label>
            <label>Probabilidad (0–100)
              <input [(ngModel)]="editForm.probability" name="probability" type="number" min="0" max="100" />
            </label>
            <label>Fecha de cierre esperada
              <input [(ngModel)]="editForm.expected_close_date" name="expected_close_date" type="date" />
            </label>
            <div class="crm-actions">
              <button type="submit" class="crm-btn" [disabled]="saving()">
                {{ saving() ? 'Guardando…' : 'Guardar' }}
              </button>
            </div>
          </form>
        </div>

        <!-- Stage advance -->
        @if (!isClosedStage()) {
          <div class="crm-card">
            <h2>Avanzar etapa</h2>
            <div class="crm-form">
              <label>Nueva etapa
                <select [(ngModel)]="newStage" name="newStage">
                  @for (s of stages; track s) {
                    <option [value]="s" [disabled]="s === opp()!.stage">{{ s }}</option>
                  }
                </select>
              </label>
              <label>Motivo (opcional)
                <input [(ngModel)]="stageReason" name="stageReason" />
              </label>
              <div class="crm-actions">
                <button type="button" class="crm-btn crm-btn--ghost"
                  [disabled]="!newStage || newStage === opp()!.stage || saving()"
                  (click)="advanceStage()">Avanzar etapa</button>
                <button type="button" class="crm-btn crm-btn--danger"
                  [disabled]="saving()"
                  (click)="showCloseForm = !showCloseForm">
                  Cerrar oportunidad
                </button>
              </div>
            </div>

            @if (showCloseForm) {
              <div style="margin-top:1rem;border-top:1px solid var(--border,#30363d);padding-top:1rem">
                <h3 style="font-size:0.95rem;margin:0 0 0.6rem">Cerrar oportunidad</h3>
                <div class="crm-form">
                  <label>Resultado *
                    <select [(ngModel)]="closeOutcome" name="closeOutcome">
                      <option value="won">won — ganada</option>
                      <option value="lost">lost — perdida</option>
                      <option value="canceled">canceled — cancelada</option>
                    </select>
                  </label>
                  <label>Etapa final *
                    <select [(ngModel)]="closeStage" name="closeStage">
                      <option value="won">won</option>
                      <option value="lost">lost</option>
                      <option value="canceled">canceled</option>
                    </select>
                  </label>
                  <label>Motivo
                    <input [(ngModel)]="closeReason" name="closeReason" />
                  </label>
                  <div class="crm-actions">
                    <button type="button" class="crm-btn crm-btn--danger"
                      [disabled]="saving()" (click)="closeOpp()">
                      Confirmar cierre
                    </button>
                  </div>
                </div>
              </div>
            }
          </div>
        }

        <!-- Stage history -->
        @if (history().length) {
          <div class="crm-card">
            <h2>Historial de etapas</h2>
            <table class="crm-table">
              <thead><tr><th>Desde</th><th>Hacia</th><th>Motivo</th><th>Fecha</th></tr></thead>
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

        <!-- Quotations -->
        <div class="crm-card">
          <h2>Cotizaciones</h2>
          @if (quotations().length) {
            <table class="crm-table">
              <thead><tr><th>#</th><th>Estado</th><th>Moneda</th><th>Versión actual</th></tr></thead>
              <tbody>
                @for (q of quotations(); track q.id) {
                  <tr>
                    <td><a [routerLink]="['/crm/quotations', q.id]">Q-{{ q.id }}</a></td>
                    <td><span class="crm-badge crm-badge--{{ q.status }}">{{ q.status }}</span></td>
                    <td>{{ q.currency || '—' }}</td>
                    <td>v{{ q.current_version_no ?? '—' }}</td>
                  </tr>
                }
              </tbody>
            </table>
          } @else {
            <p class="crm-muted">Sin cotizaciones.</p>
          }
          <div class="crm-actions" style="margin-top:0.6rem">
            <button type="button" class="crm-btn crm-btn--ghost" [disabled]="saving()"
              (click)="createQuotation()">+ Crear cotización</button>
          </div>
        </div>

        <!-- Contracts -->
        <div class="crm-card">
          <h2>Contratos</h2>
          @if (contracts().length) {
            <table class="crm-table">
              <thead><tr><th>#</th><th>Razón social</th><th>Estado</th></tr></thead>
              <tbody>
                @for (c of contracts(); track c.id) {
                  <tr>
                    <td><a [routerLink]="['/crm/contracts', c.id]">C-{{ c.id }}</a></td>
                    <td>{{ c.legal_name || ('common.notAvailable' | t:lang()) }}</td>
                    <td><span class="crm-badge">{{ c.status }}</span></td>
                  </tr>
                }
              </tbody>
            </table>
          } @else {
            <p class="crm-muted">Sin contratos. Créalos desde una cotización aceptada/enviada.</p>
          }
        </div>

        <!-- Conversion -->
        <div class="crm-card">
          <h2>Conversión a organización</h2>
          <p class="crm-muted">
            Prepara la conversión comercial. La suscripción/facturación se gestionan después en sus módulos.
          </p>
          @if (conversions().length) {
            <table class="crm-table">
              <thead><tr><th>#</th><th>Modo</th><th>Estado</th><th>Org</th></tr></thead>
              <tbody>
                @for (cv of conversions(); track cv.id) {
                  <tr>
                    <td><a [routerLink]="['/crm/conversions', cv.id]">CV-{{ cv.id }}</a></td>
                    <td>{{ cv.mode }}</td>
                    <td><span class="crm-badge">{{ cv.status }}</span></td>
                    <td>{{ cv.organization_id ?? ('common.notAvailable' | t:lang()) }}</td>
                  </tr>
                }
              </tbody>
            </table>
          } @else {
            <p class="crm-muted">Sin conversiones aún.</p>
          }
          <div class="crm-actions" style="margin-top:0.6rem">
            <button type="button" class="crm-btn" [disabled]="saving()"
              (click)="prepareConversion('link_existing')">Preparar conversión (vincular org)</button>
            <button type="button" class="crm-btn crm-btn--ghost" [disabled]="saving()"
              (click)="prepareConversion('create_org')">Preparar conversión (crear org)</button>
          </div>
        </div>

        <!-- Activities -->
        <div class="crm-card">
          <h2>Actividades recientes</h2>
          @if (activities().length) {
            <table class="crm-table">
              <thead><tr><th>Tipo</th><th>Asunto</th><th>Estado</th><th>Fecha</th></tr></thead>
              <tbody>
                @for (a of activities(); track a.id) {
                  <tr>
                    <td>{{ a.activity_type }}</td>
                    <td>{{ a.subject }}</td>
                    <td><span class="crm-badge crm-badge--{{ a.status }}">{{ a.status }}</span></td>
                    <td class="crm-muted">{{ a.created_at | date:'shortDate' }}</td>
                  </tr>
                }
              </tbody>
            </table>
          } @else {
            <p class="crm-muted">Sin actividades.</p>
          }
          <button type="button" class="crm-btn crm-btn--ghost" style="margin-top:0.6rem"
            (click)="showActivityForm = !showActivityForm">
            {{ showActivityForm ? 'Cancelar' : '+ Registrar actividad' }}
          </button>
          @if (showActivityForm) {
            <form class="crm-form" style="margin-top:0.75rem" (ngSubmit)="createActivity()">
              <label>Tipo *
                <select [(ngModel)]="actForm.activity_type" name="activity_type" required>
                  <option value="call">Llamada</option>
                  <option value="email">Correo</option>
                  <option value="meeting">Reunión</option>
                  <option value="demo">Demo</option>
                  <option value="note">Nota</option>
                </select>
              </label>
              <label>Asunto *
                <input [(ngModel)]="actForm.subject" name="subject" required />
              </label>
              <label>Detalle
                <textarea [(ngModel)]="actForm.body" name="body" rows="2"></textarea>
              </label>
              <div class="crm-actions">
                <button type="submit" class="crm-btn" [disabled]="!actForm.subject || saving()">
                  Guardar actividad
                </button>
              </div>
            </form>
          }
        </div>

        <!-- Metadata -->
        <div class="crm-card crm-muted" style="font-size:0.8rem">
          <p>Prospecto: #{{ opp()!.prospect_id }}</p>
          <p>Creada: {{ opp()!.created_at | date:'medium' }}</p>
          <p>Actualizada: {{ opp()!.updated_at | date:'medium' }}</p>
          @if (opp()!.actual_close_date) {
            <p>Cierre real: {{ opp()!.actual_close_date | date:'shortDate' }}</p>
          }
        </div>
      }
    </section>
  `,
})
export class CrmOpportunityDetailPageComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private readonly api = inject(CrmApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  readonly stages = [...OPPORTUNITY_STAGES];

  oppId = 0;
  showCloseForm = false;
  showActivityForm = false;
  newStage = '';
  stageReason = '';
  closeOutcome = 'won';
  closeStage = 'won';
  closeReason = '';

  editForm = { name: '', description: '', expected_value: 0, currency: 'USD', probability: 50, expected_close_date: '' };
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

  isClosedStage(): boolean {
    const s = this.opp()?.stage;
    return s === 'won' || s === 'lost' || s === 'canceled';
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
    try {
      const res = await firstValueFrom(
        this.api.prepareConversion({ opportunity_id: this.oppId, mode }),
      );
      this.success.set(`Conversión #${res.conversion.id} preparada.`);
      await this.router.navigate(['/crm/conversions', res.conversion.id]);
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al preparar conversión');
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
