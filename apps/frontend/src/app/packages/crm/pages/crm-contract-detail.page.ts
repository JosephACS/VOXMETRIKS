import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { CrmApiError, CrmApiService } from '../services/crm-api.service';
import { CommercialContract } from '../models/crm.models';
import { I18nService } from '../../../core/services/i18n.service';
import { NotificationService } from '../../../core/services/notification.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { LocaleDatePipe } from '../../../shared/pipes/locale-format.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import { ConfirmDialogService } from '../../../shared/services/confirm-dialog.service';

type ContractPending = 'reject' | 'accept' | 'terminate';

@Component({
  selector: 'app-crm-contract-detail-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, TranslatePipe, LocaleDatePipe, ...ENTERPRISE_UI_IMPORTS],
  styleUrls: ['../styles/crm.css'],
  template: `
    <div class="vx-enterprise crm-page" data-testid="crm-contract-detail-page">
      <app-enterprise-page-header [title]="('crm.contract.title' | t:lang()) + ' #' + contractId">
        <a class="btn btn--ghost" routerLink="/crm/opportunities">
          ← {{ 'crm.contract.backOpportunities' | t:lang() }}
        </a>
        @if (contract()) {
          <app-enterprise-status-badge [status]="contract()!.status" />
        }
      </app-enterprise-page-header>

      @if (error()) {
        <app-enterprise-error-state [message]="error()!" (retry)="load()" />
      }
      @if (success()) {
        <div class="alert alert--success" role="status">{{ success() }}</div>
      }

      @if (pendingAction()) {
        <app-enterprise-section-card [title]="'common.confirm' | t:lang()">
          <form class="form-grid" (ngSubmit)="confirmPendingAction()">
            <app-enterprise-form-field
              [label]="pendingAction() === 'accept' ? ('crm.contract.evidenceNote' | t:lang()) : ('common.notes' | t:lang())"
              [required]="pendingAction() === 'accept' || pendingAction() === 'terminate' || pendingAction() === 'reject'"
            >
              <textarea
                class="input"
                rows="3"
                [(ngModel)]="actionNote"
                name="actionNote"
                [disabled]="saving()"
                required
              ></textarea>
            </app-enterprise-form-field>
            <app-enterprise-action-bar>
              <button type="button" class="btn btn--ghost" (click)="cancelPendingAction()" [disabled]="saving()">
                {{ 'common.cancel' | t:lang() }}
              </button>
              <button type="submit" class="btn btn--primary" [disabled]="saving() || !actionNote.trim()">
                {{ (saving() ? 'common.saving' : 'common.confirm') | t:lang() }}
              </button>
            </app-enterprise-action-bar>
          </form>
        </app-enterprise-section-card>
      }

      @if (loading()) {
        <app-enterprise-loading-skeleton [rows]="3" />
      } @else if (contract()) {
        <app-enterprise-section-card [title]="'crm.contract.info' | t:lang()">
          <div class="form-grid" style="font-size: 0.875rem">
            <div>
              <dt class="muted">{{ 'crm.contract.opportunity' | t:lang() }}</dt>
              <dd>#{{ contract()!.opportunity_id }}</dd>
            </div>
            <div>
              <dt class="muted">{{ 'crm.contract.quotationVersion' | t:lang() }}</dt>
              <dd>#{{ contract()!.quotation_version_id }}</dd>
            </div>
            @if (contract()!.organization_id) {
              <div>
                <dt class="muted">{{ 'crm.contract.organization' | t:lang() }}</dt>
                <dd>#{{ contract()!.organization_id }}</dd>
              </div>
            }
            @if (contract()!.legal_name) {
              <div>
                <dt class="muted">{{ 'crm.contract.legalName' | t:lang() }}</dt>
                <dd>{{ contract()!.legal_name }}</dd>
              </div>
            }
            @if (contract()!.signatory_user_id) {
              <div>
                <dt class="muted">{{ 'crm.contract.signatoryUser' | t:lang() }}</dt>
                <dd>#{{ contract()!.signatory_user_id }}</dd>
              </div>
            }
            @if (contract()!.signatory_contact_id) {
              <div>
                <dt class="muted">{{ 'crm.contract.signatoryContact' | t:lang() }}</dt>
                <dd>#{{ contract()!.signatory_contact_id }}</dd>
              </div>
            }
            @if (contract()!.approved_by) {
              <div>
                <dt class="muted">{{ 'crm.contract.approvedBy' | t:lang() }}</dt>
                <dd>#{{ contract()!.approved_by }}</dd>
              </div>
            }
            @if (contract()!.approval_notes) {
              <div>
                <dt class="muted">{{ 'crm.contract.approvalNotes' | t:lang() }}</dt>
                <dd>{{ contract()!.approval_notes }}</dd>
              </div>
            }
            @if (contract()!.accepted_at) {
              <div>
                <dt class="muted">{{ 'crm.contract.acceptedAt' | t:lang() }}</dt>
                <dd>{{ contract()!.accepted_at | localeDate:true }}</dd>
              </div>
            }
            @if (contract()!.rejected_at) {
              <div>
                <dt class="muted">{{ 'crm.contract.rejectedAt' | t:lang() }}</dt>
                <dd>{{ contract()!.rejected_at | localeDate:true }}</dd>
              </div>
            }
            @if (contract()!.terminated_at) {
              <div>
                <dt class="muted">{{ 'crm.contract.terminatedAt' | t:lang() }}</dt>
                <dd>{{ contract()!.terminated_at | localeDate:true }}</dd>
              </div>
            }
            @if (contract()!.termination_reason) {
              <div>
                <dt class="muted">{{ 'crm.contract.terminationReason' | t:lang() }}</dt>
                <dd>{{ contract()!.termination_reason }}</dd>
              </div>
            }
            <div>
              <dt class="muted">{{ 'common.created' | t:lang() }}</dt>
              <dd>{{ contract()!.created_at | localeDate:true }}</dd>
            </div>
            <div>
              <dt class="muted">{{ 'common.updated' | t:lang() }}</dt>
              <dd>{{ contract()!.updated_at | localeDate:true }}</dd>
            </div>
          </div>

          @if (contract()!.acceptance_evidence) {
            <div style="margin-top: 0.75rem">
              <p class="muted" style="font-size: 0.8rem">{{ 'crm.contract.evidenceNote' | t:lang() }}</p>
              <div
                style="font-family: monospace; font-size: 0.8rem; word-break: break-all; padding: 0.5rem; border: 1px dashed var(--border, #30363d); border-radius: 6px"
              >
                {{ contract()!.acceptance_evidence }}
              </div>
            </div>
          }
        </app-enterprise-section-card>

        <app-enterprise-section-card [title]="'crm.contract.actions' | t:lang()">
          <app-enterprise-action-bar>
            @if (contract()!.status === 'draft') {
              <button type="button" class="btn btn--primary" [disabled]="saving()" (click)="submit()">
                {{ 'crm.contract.submitApproval' | t:lang() }}
              </button>
            }
            @if (contract()!.status === 'pending_approval') {
              <button type="button" class="btn btn--primary" [disabled]="saving()" (click)="approve()">
                {{ 'crm.contract.approveContract' | t:lang() }}
              </button>
              <button type="button" class="btn btn--danger" [disabled]="saving()" (click)="reject()">
                {{ 'common.reject' | t:lang() }}
              </button>
            }
            @if (contract()!.status === 'approved') {
              <button type="button" class="btn btn--primary" [disabled]="saving()" (click)="send()">
                {{ 'crm.contract.sendToClient' | t:lang() }}
              </button>
            }
            @if (contract()!.status === 'sent') {
              <button type="button" class="btn btn--primary" [disabled]="saving()" (click)="accept()">
                {{ 'crm.contract.registerAcceptance' | t:lang() }}
              </button>
              <button type="button" class="btn btn--danger" [disabled]="saving()" (click)="reject()">
                {{ 'common.reject' | t:lang() }}
              </button>
            }
            @if (['approved', 'sent', 'active'].includes(contract()!.status)) {
              <button type="button" class="btn btn--danger" [disabled]="saving()" (click)="terminate()">
                {{ 'crm.contract.terminateContract' | t:lang() }}
              </button>
            }
          </app-enterprise-action-bar>
          @if (['draft', 'sent', 'pending_approval'].includes(contract()!.status)) {
            <app-enterprise-action-bar>
              <button type="button" class="btn btn--ghost" [disabled]="saving()" (click)="expire()">
                {{ 'crm.contract.markExpired' | t:lang() }}
              </button>
            </app-enterprise-action-bar>
          }
        </app-enterprise-section-card>
      }
    </div>
  `,
})
export class CrmContractDetailPageComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private readonly api = inject(CrmApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly confirmDlg = inject(ConfirmDialogService);
  private readonly notifications = inject(NotificationService);

  contractId = 0;
  actionNote = '';

  readonly contract = signal<CommercialContract | null>(null);
  readonly loading = signal(true);
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);
  readonly success = signal<string | null>(null);
  readonly pendingAction = signal<ContractPending | null>(null);

  async ngOnInit(): Promise<void> {
    this.contractId = Number(this.route.snapshot.paramMap.get('id'));
    await this.load();
  }

  async load(): Promise<void> {
    this.loading.set(true);
    this.error.set(null);
    this.success.set(null);
    try {
      const c = await firstValueFrom(this.api.getContract(this.contractId));
      this.contract.set(c);
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al cargar contrato');
    } finally {
      this.loading.set(false);
    }
  }

  async submit(): Promise<void> {
    if (this.saving()) return;
    this.saving.set(true);
    this.error.set(null);
    try {
      const c = await firstValueFrom(this.api.submitContract(this.contractId));
      this.contract.set(c);
      this.success.set('Contrato enviado para aprobación.');
      this.notifications.success(this.i18n.t('crm.contract.submitApproval'));
    } catch (e) {
      const msg = e instanceof CrmApiError ? e.message : 'Error al enviar';
      this.error.set(msg);
      this.notifications.error(this.i18n.t('crm.contract.submitApproval'), msg);
    } finally {
      this.saving.set(false);
    }
  }

  async approve(): Promise<void> {
    if (this.saving()) return;
    const ok = await this.confirmDlg.open({
      title: this.i18n.t('crm.contract.approveContract'),
      message: this.i18n.t('common.confirm'),
      confirmLabel: this.i18n.t('crm.contract.approveContract'),
    });
    if (!ok) return;
    this.saving.set(true);
    this.error.set(null);
    try {
      const c = await firstValueFrom(this.api.approveContract(this.contractId));
      this.contract.set(c);
      this.success.set('Contrato aprobado.');
      this.notifications.success(this.i18n.t('crm.contract.approveContract'));
    } catch (e) {
      const msg = e instanceof CrmApiError ? e.message : 'Error al aprobar';
      this.error.set(msg);
      this.notifications.error(this.i18n.t('crm.contract.approveContract'), msg);
    } finally {
      this.saving.set(false);
    }
  }

  async send(): Promise<void> {
    if (this.saving()) return;
    this.saving.set(true);
    this.error.set(null);
    try {
      const c = await firstValueFrom(this.api.sendContract(this.contractId));
      this.contract.set(c);
      this.success.set('Contrato enviado al cliente.');
      this.notifications.success(this.i18n.t('crm.contract.sendToClient'));
    } catch (e) {
      const msg = e instanceof CrmApiError ? e.message : 'Error al enviar';
      this.error.set(msg);
      this.notifications.error(this.i18n.t('crm.contract.sendToClient'), msg);
    } finally {
      this.saving.set(false);
    }
  }

  accept(): void {
    if (this.saving()) return;
    this.actionNote = '';
    this.pendingAction.set('accept');
  }

  reject(): void {
    if (this.saving()) return;
    this.actionNote = '';
    this.pendingAction.set('reject');
  }

  terminate(): void {
    if (this.saving()) return;
    this.actionNote = '';
    this.pendingAction.set('terminate');
  }

  cancelPendingAction(): void {
    this.pendingAction.set(null);
    this.actionNote = '';
  }

  async confirmPendingAction(): Promise<void> {
    const action = this.pendingAction();
    const note = this.actionNote.trim();
    if (!action || !note || this.saving()) return;
    this.saving.set(true);
    this.error.set(null);
    try {
      let c: CommercialContract;
      if (action === 'accept') {
        c = await firstValueFrom(this.api.acceptContract(this.contractId, note));
        this.success.set('Aceptación registrada.');
      } else if (action === 'reject') {
        c = await firstValueFrom(this.api.rejectContract(this.contractId, note));
        this.success.set('Contrato rechazado.');
      } else {
        c = await firstValueFrom(this.api.terminateContract(this.contractId, note));
        this.success.set('Contrato terminado.');
      }
      this.contract.set(c);
      this.notifications.success(this.i18n.t('common.confirm'));
      this.cancelPendingAction();
    } catch (e) {
      const msg = e instanceof CrmApiError ? e.message : 'Error al confirmar la acción';
      this.error.set(msg);
      this.notifications.error(this.i18n.t('common.confirm'), msg);
    } finally {
      this.saving.set(false);
    }
  }

  async expire(): Promise<void> {
    if (this.saving()) return;
    const ok = await this.confirmDlg.open({
      title: this.i18n.t('crm.contract.markExpired'),
      message: this.i18n.t('common.confirm'),
      confirmLabel: this.i18n.t('crm.contract.markExpired'),
      danger: true,
    });
    if (!ok) return;
    this.saving.set(true);
    this.error.set(null);
    try {
      const c = await firstValueFrom(this.api.expireContract(this.contractId));
      this.contract.set(c);
      this.success.set('Contrato marcado como expirado.');
      this.notifications.success(this.i18n.t('crm.contract.markExpired'));
    } catch (e) {
      const msg = e instanceof CrmApiError ? e.message : 'Error al expirar';
      this.error.set(msg);
      this.notifications.error(this.i18n.t('crm.contract.markExpired'), msg);
    } finally {
      this.saving.set(false);
    }
  }
}
