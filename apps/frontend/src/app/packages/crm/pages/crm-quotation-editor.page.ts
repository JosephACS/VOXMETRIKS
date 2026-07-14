import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { CrmApiError, CrmApiService } from '../services/crm-api.service';
import { Quotation, QuotationVersion, QuotationItem, QuotationItemCreateRequest } from '../models/crm.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { LocaleDatePipe, LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-crm-quotation-editor-page',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink,
    TranslatePipe,
    LocaleDatePipe,
    LocaleMoneyPipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  styleUrls: ['../styles/crm.css'],
  template: `
    <div class="vx-enterprise crm-page" data-testid="crm-quotation-editor-page">
      <app-enterprise-page-header [title]="('crm.quotation.title' | t:lang()) + ' #' + quotationId">
        <a class="btn btn--ghost" routerLink="/crm/opportunities">
          ← {{ 'crm.quotation.backOpportunities' | t:lang() }}
        </a>
        @if (quotation()) {
          <app-enterprise-status-badge [status]="quotation()!.status" />
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
      } @else if (quotation()) {
        <app-enterprise-section-card [title]="'crm.quotation.summary' | t:lang()">
          <p class="muted">
            {{ 'crm.contract.opportunity' | t:lang() }}: #{{ quotation()!.opportunity_id }} ·
            {{ 'common.currency' | t:lang() }}: {{ quotation()!.currency || ('common.notAvailable' | t:lang()) }} ·
            {{ 'crm.opportunityDetail.currentVersion' | t:lang() }}: v{{ quotation()!.current_version_no ?? ('common.notAvailable' | t:lang()) }}
          </p>
          @if (quotation()!.notes) {
            <p>{{ quotation()!.notes }}</p>
          }
          <app-enterprise-action-bar>
            <button type="button" class="btn btn--secondary" [disabled]="saving()" (click)="createVersion()">
              + {{ 'crm.quotation.newVersion' | t:lang() }}
            </button>
          </app-enterprise-action-bar>
        </app-enterprise-section-card>

        @if (versions().length) {
          @for (v of versions(); track v.id) {
            <app-enterprise-section-card [title]="('crm.quotation.version' | t:lang()) + ' ' + v.version_no">
              <app-enterprise-status-badge [status]="v.status" />
              @if (v.is_immutable) {
                <span class="muted">{{ 'crm.quotation.readOnly' | t:lang() }}</span>
              }

              <p class="muted">
                {{ 'crm.quotation.subtotal' | t:lang() }}: {{ v.subtotal ?? 0 | localeMoney:quotation()!.currency || 'USD' }} ·
                {{ 'crm.quotation.discount' | t:lang() }}: {{ v.discount_pct ?? 0 }}% ·
                {{ 'common.total' | t:lang() }}: {{ v.total ?? 0 | localeMoney:quotation()!.currency || 'USD' }}
                @if (v.discount_requires_approval) {
                  <app-enterprise-status-badge [status]="'pending'" [label]="'crm.quotation.needsApproval' | t:lang()" />
                }
              </p>

              @if (v.sent_at) {
                <p class="muted">{{ 'crm.quotation.sentAt' | t:lang() }}: {{ v.sent_at | localeDate:true }}</p>
              }
              @if (v.accepted_at) {
                <p class="muted">{{ 'crm.quotation.acceptedAt' | t:lang() }}: {{ v.accepted_at | localeDate:true }}</p>
              }
              @if (v.rejected_at) {
                <p class="muted">{{ 'crm.quotation.rejectedAt' | t:lang() }}: {{ v.rejected_at | localeDate:true }}</p>
              }

              @if (itemsMap()[v.id]?.length) {
                <app-enterprise-data-table>
                  <table class="data-table">
                    <thead>
                      <tr>
                        <th>{{ 'common.description' | t:lang() }}</th>
                        <th>{{ 'crm.quotation.qty' | t:lang() }}</th>
                        <th>{{ 'crm.quotation.price' | t:lang() }}</th>
                        <th>{{ 'crm.quotation.discount' | t:lang() }}</th>
                        <th>{{ 'crm.quotation.lineTotal' | t:lang() }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      @for (item of itemsMap()[v.id]; track item.id) {
                        <tr>
                          <td>{{ item.description }}</td>
                          <td>{{ item.quantity }}</td>
                          <td>{{ item.unit_price | localeMoney:quotation()!.currency || 'USD' }}</td>
                          <td>{{ item.discount_pct ?? 0 }}%</td>
                          <td>{{ item.line_total ?? 0 | localeMoney:quotation()!.currency || 'USD' }}</td>
                        </tr>
                      }
                    </tbody>
                  </table>
                </app-enterprise-data-table>
              } @else {
                <app-enterprise-empty-state [title]="'crm.quotation.noItems' | t:lang()" />
              }

              @if (!v.is_immutable) {
                <app-enterprise-action-bar>
                  <button type="button" class="btn btn--ghost" (click)="toggleItemForm(v.id)">
                    {{ (activeItemForm === v.id ? 'common.cancel' : 'crm.quotation.addItem') | t:lang() }}
                  </button>
                </app-enterprise-action-bar>
                @if (activeItemForm === v.id) {
                  <form class="form-grid" style="margin-top: 0.75rem" (ngSubmit)="addItem(v.id)">
                    <app-enterprise-form-field [label]="'common.description' | t:lang()" [required]="true">
                      <input class="input" [(ngModel)]="itemForm.description" name="description" required />
                    </app-enterprise-form-field>
                    <app-enterprise-form-field [label]="'crm.quotation.quantity' | t:lang()" [required]="true">
                      <input class="input" [(ngModel)]="itemForm.quantity" name="quantity" type="number" min="1" required />
                    </app-enterprise-form-field>
                    <app-enterprise-form-field [label]="'crm.quotation.unitPrice' | t:lang()" [required]="true">
                      <input class="input" [(ngModel)]="itemForm.unit_price" name="unit_price" type="number" min="0" step="0.01" required />
                    </app-enterprise-form-field>
                    <app-enterprise-form-field [label]="'crm.quotation.discount' | t:lang()">
                      <input class="input" [(ngModel)]="itemForm.discount_pct" name="discount_pct" type="number" min="0" max="100" step="0.01" />
                    </app-enterprise-form-field>
                    <div class="form-grid__actions">
                      <button type="submit" class="btn btn--primary" [disabled]="!itemForm.description || !itemForm.quantity || saving()">
                        {{ 'crm.quotation.addItem' | t:lang() }}
                      </button>
                    </div>
                  </form>
                }

                <app-enterprise-action-bar>
                  <button type="button" class="btn btn--primary" [disabled]="saving()" (click)="send(v.id)">
                    {{ 'crm.quotation.send' | t:lang() }}
                  </button>
                  <button type="button" class="btn btn--secondary" [disabled]="saving()" (click)="requestApproval(v.id)">
                    {{ 'crm.quotation.requestApproval' | t:lang() }}
                  </button>
                </app-enterprise-action-bar>
              }

              @if (v.status === 'sent' || v.status === 'approved') {
                <app-enterprise-action-bar>
                  <button type="button" class="btn btn--primary" [disabled]="saving()" (click)="accept(v.id)">
                    {{ 'crm.quotation.accept' | t:lang() }}
                  </button>
                  <button type="button" class="btn btn--secondary" [disabled]="saving()" (click)="createContractFrom(v.id)">
                    {{ 'crm.quotation.createContract' | t:lang() }}
                  </button>
                </app-enterprise-action-bar>
              }
            </app-enterprise-section-card>
          }
        } @else {
          <app-enterprise-empty-state
            [title]="'crm.quotation.noVersions' | t:lang()"
            [ctaLabel]="'crm.quotation.newVersion' | t:lang()"
            (ctaClick)="createVersion()"
          />
        }
      }
    </div>
  `,
})
export class CrmQuotationEditorPageComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private readonly api = inject(CrmApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  quotationId = 0;
  activeItemForm: number | null = null;
  approvalReason = '';

  itemForm: QuotationItemCreateRequest = { description: '', quantity: 1, unit_price: 0 };

  readonly quotation = signal<Quotation | null>(null);
  readonly versions = signal<QuotationVersion[]>([]);
  readonly itemsMap = signal<Record<number, QuotationItem[]>>({});
  readonly loading = signal(true);
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);
  readonly success = signal<string | null>(null);

  async ngOnInit(): Promise<void> {
    this.quotationId = Number(this.route.snapshot.paramMap.get('id'));
    await this.load();
  }

  async load(): Promise<void> {
    this.loading.set(true);
    this.error.set(null);
    this.success.set(null);
    try {
      const [q, vers] = await Promise.all([
        firstValueFrom(this.api.getQuotation(this.quotationId)),
        firstValueFrom(this.api.listQuotationVersions(this.quotationId)),
      ]);
      this.quotation.set(q);
      this.versions.set(vers);
      const map: Record<number, QuotationItem[]> = {};
      await Promise.all(
        vers.map(async (v) => {
          try {
            map[v.id] = await firstValueFrom(this.api.listQuotationItems(v.id));
          } catch {
            map[v.id] = [];
          }
        }),
      );
      this.itemsMap.set(map);
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al cargar cotización');
    } finally {
      this.loading.set(false);
    }
  }

  async createVersion(): Promise<void> {
    this.saving.set(true);
    this.error.set(null);
    try {
      await firstValueFrom(this.api.createQuotationVersion(this.quotationId));
      this.success.set('Nueva versión creada.');
      await this.load();
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al crear versión');
    } finally {
      this.saving.set(false);
    }
  }

  toggleItemForm(versionId: number): void {
    this.activeItemForm = this.activeItemForm === versionId ? null : versionId;
    this.itemForm = { description: '', quantity: 1, unit_price: 0 };
  }

  async addItem(versionId: number): Promise<void> {
    if (!this.itemForm.description || !this.itemForm.quantity) return;
    this.saving.set(true);
    this.error.set(null);
    try {
      const item = await firstValueFrom(this.api.addQuotationItem(versionId, this.itemForm));
      const map = { ...this.itemsMap() };
      map[versionId] = [...(map[versionId] ?? []), item];
      this.itemsMap.set(map);
      this.activeItemForm = null;
      this.success.set('Ítem añadido.');
      await this.load();
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al añadir ítem');
    } finally {
      this.saving.set(false);
    }
  }

  async send(versionId: number): Promise<void> {
    this.saving.set(true);
    this.error.set(null);
    try {
      await firstValueFrom(this.api.sendQuotationVersion(versionId));
      this.success.set('Versión enviada. Ya no es editable.');
      await this.load();
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al enviar versión');
    } finally {
      this.saving.set(false);
    }
  }

  async requestApproval(versionId: number): Promise<void> {
    const reason = prompt('Motivo de la solicitud de aprobación de descuento:') ?? '';
    if (!reason) return;
    this.saving.set(true);
    this.error.set(null);
    try {
      await firstValueFrom(this.api.requestDiscountApproval(versionId, reason));
      this.success.set('Solicitud de aprobación enviada.');
      await this.load();
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al solicitar aprobación');
    } finally {
      this.saving.set(false);
    }
  }

  async accept(versionId: number): Promise<void> {
    if (!confirm(this.i18n.t('crm.quotation.acceptConfirm'))) return;
    this.saving.set(true);
    this.error.set(null);
    try {
      await firstValueFrom(this.api.acceptQuotationVersion(versionId));
      this.success.set('Cotización aceptada.');
      await this.load();
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al aceptar cotización');
    } finally {
      this.saving.set(false);
    }
  }

  async createContractFrom(versionId: number): Promise<void> {
    const q = this.quotation();
    if (!q) return;
    const legalName = prompt('Razón social del contrato:')?.trim();
    if (!legalName) return;
    this.saving.set(true);
    this.error.set(null);
    try {
      const c = await firstValueFrom(
        this.api.createContract({
          quotation_version_id: versionId,
          opportunity_id: q.opportunity_id,
          legal_name: legalName,
          terms_snapshot: { source: 'quotation_ui', synthetic_note: 'created_from_quotation_editor' },
        }),
      );
      this.success.set(`Contrato #${c.id} creado.`);
      await this.router.navigate(['/crm/contracts', c.id]);
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al crear contrato');
    } finally {
      this.saving.set(false);
    }
  }
}
