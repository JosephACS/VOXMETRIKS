import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { CrmApiError, CrmApiService } from '../services/crm-api.service';
import { CommercialContract } from '../models/crm.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { LocaleDatePipe } from '../../../shared/pipes/locale-format.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-crm-contract-detail-page',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe, LocaleDatePipe, ...ENTERPRISE_UI_IMPORTS],
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

  contractId = 0;

  readonly contract = signal<CommercialContract | null>(null);
  readonly loading = signal(true);
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);
  readonly success = signal<string | null>(null);

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
    this.saving.set(true);
    this.error.set(null);
    try {
      const c = await firstValueFrom(this.api.submitContract(this.contractId));
      this.contract.set(c);
      this.success.set('Contrato enviado para aprobación.');
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al enviar');
    } finally {
      this.saving.set(false);
    }
  }

  async approve(): Promise<void> {
    const notes = prompt('Notas de aprobación (opcional):') ?? '';
    this.saving.set(true);
    this.error.set(null);
    try {
      const c = await firstValueFrom(this.api.approveContract(this.contractId, notes || undefined));
      this.contract.set(c);
      this.success.set('Contrato aprobado.');
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al aprobar');
    } finally {
      this.saving.set(false);
    }
  }

  async send(): Promise<void> {
    this.saving.set(true);
    this.error.set(null);
    try {
      const c = await firstValueFrom(this.api.sendContract(this.contractId));
      this.contract.set(c);
      this.success.set('Contrato enviado al cliente.');
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al enviar');
    } finally {
      this.saving.set(false);
    }
  }

  async accept(): Promise<void> {
    const evidence = prompt(
      'Referencia de aceptación académica (ej: "Aprobado en reunión 2026-07-11").\nNota: esta referencia no constituye firma legal certificada.',
    );
    if (!evidence) return;
    this.saving.set(true);
    this.error.set(null);
    try {
      const c = await firstValueFrom(this.api.acceptContract(this.contractId, evidence));
      this.contract.set(c);
      this.success.set('Aceptación académica registrada.');
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al registrar aceptación');
    } finally {
      this.saving.set(false);
    }
  }

  async reject(): Promise<void> {
    const reason = prompt('Motivo de rechazo:') ?? '';
    this.saving.set(true);
    this.error.set(null);
    try {
      const c = await firstValueFrom(this.api.rejectContract(this.contractId, reason || undefined));
      this.contract.set(c);
      this.success.set('Contrato rechazado.');
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al rechazar');
    } finally {
      this.saving.set(false);
    }
  }

  async expire(): Promise<void> {
    this.saving.set(true);
    this.error.set(null);
    try {
      const c = await firstValueFrom(this.api.expireContract(this.contractId));
      this.contract.set(c);
      this.success.set('Contrato marcado como expirado.');
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al expirar');
    } finally {
      this.saving.set(false);
    }
  }

  async terminate(): Promise<void> {
    const reason = prompt('Motivo de terminación:');
    if (!reason) return;
    this.saving.set(true);
    this.error.set(null);
    try {
      const c = await firstValueFrom(this.api.terminateContract(this.contractId, reason));
      this.contract.set(c);
      this.success.set('Contrato terminado.');
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al terminar');
    } finally {
      this.saving.set(false);
    }
  }
}
