import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { CrmApiError, CrmApiService } from '../services/crm-api.service';
import { CommercialContract } from '../models/crm.models';

@Component({
  selector: 'app-crm-contract-detail-page',
  standalone: true,
  imports: [CommonModule, RouterLink],
  styleUrls: ['../styles/crm.css'],
  template: `
    <section class="crm-page" data-testid="crm-contract-detail-page">
      <div style="display:flex;align-items:center;gap:0.75rem;flex-wrap:wrap;margin-bottom:0.5rem">
        <a class="crm-btn crm-btn--ghost" routerLink="/crm/opportunities">← Oportunidades</a>
        <h1 style="margin:0">Contrato #{{ contractId }}</h1>
        @if (contract()) {
          <span class="crm-badge crm-badge--{{ contract()!.status }}">{{ contract()!.status }}</span>
        }
      </div>

      @if (error()) {
        <div class="crm-alert crm-alert--error" role="alert">{{ error() }}</div>
      }
      @if (success()) {
        <div class="crm-alert crm-alert--ok" role="status">{{ success() }}</div>
      }

      @if (loading()) {
        <p class="crm-muted">Cargando…</p>
      } @else if (contract()) {
        <div class="crm-card">
          <h2>Información del contrato</h2>
          <dl style="display:grid;grid-template-columns:auto 1fr;gap:0.3rem 1rem;font-size:0.875rem">
            <dt class="crm-muted">Oportunidad</dt><dd>#{{ contract()!.opportunity_id }}</dd>
            <dt class="crm-muted">Versión cotización</dt><dd>#{{ contract()!.quotation_version_id }}</dd>
            @if (contract()!.organization_id) {
              <dt class="crm-muted">Organización</dt><dd>#{{ contract()!.organization_id }}</dd>
            }
            @if (contract()!.legal_name) {
              <dt class="crm-muted">Razón social</dt><dd>{{ contract()!.legal_name }}</dd>
            }
            @if (contract()!.signatory_user_id) {
              <dt class="crm-muted">Firmante (usuario)</dt><dd>#{{ contract()!.signatory_user_id }}</dd>
            }
            @if (contract()!.signatory_contact_id) {
              <dt class="crm-muted">Firmante (contacto)</dt><dd>#{{ contract()!.signatory_contact_id }}</dd>
            }
            @if (contract()!.approved_by) {
              <dt class="crm-muted">Aprobado por</dt><dd>#{{ contract()!.approved_by }}</dd>
            }
            @if (contract()!.approval_notes) {
              <dt class="crm-muted">Notas aprobación</dt><dd>{{ contract()!.approval_notes }}</dd>
            }
            @if (contract()!.accepted_at) {
              <dt class="crm-muted">Aceptado</dt><dd>{{ contract()!.accepted_at | date:'medium' }}</dd>
            }
            @if (contract()!.rejected_at) {
              <dt class="crm-muted">Rechazado</dt><dd>{{ contract()!.rejected_at | date:'medium' }}</dd>
            }
            @if (contract()!.terminated_at) {
              <dt class="crm-muted">Terminado</dt><dd>{{ contract()!.terminated_at | date:'medium' }}</dd>
            }
            @if (contract()!.termination_reason) {
              <dt class="crm-muted">Motivo terminación</dt><dd>{{ contract()!.termination_reason }}</dd>
            }
            <dt class="crm-muted">Creado</dt><dd>{{ contract()!.created_at | date:'medium' }}</dd>
            <dt class="crm-muted">Actualizado</dt><dd>{{ contract()!.updated_at | date:'medium' }}</dd>
          </dl>

          @if (contract()!.acceptance_evidence) {
            <div style="margin-top:0.75rem">
              <p class="crm-muted" style="font-size:0.8rem">
                Evidencia de aceptación académica (referencia interna, no constituye firma legal certificada):
              </p>
              <div style="font-family:monospace;font-size:0.8rem;word-break:break-all;
                          padding:0.5rem;border:1px dashed var(--border,#30363d);border-radius:6px">
                {{ contract()!.acceptance_evidence }}
              </div>
            </div>
          }
        </div>

        <!-- Actions by status -->
        <div class="crm-card">
          <h2>Acciones disponibles</h2>
          <div class="crm-actions">
            @if (contract()!.status === 'draft') {
              <button type="button" class="crm-btn" [disabled]="saving()" (click)="submit()">
                Enviar para aprobación
              </button>
            }
            @if (contract()!.status === 'pending_approval') {
              <button type="button" class="crm-btn" [disabled]="saving()" (click)="approve()">
                Aprobar contrato
              </button>
              <button type="button" class="crm-btn crm-btn--danger" [disabled]="saving()" (click)="reject()">
                Rechazar
              </button>
            }
            @if (contract()!.status === 'approved') {
              <button type="button" class="crm-btn" [disabled]="saving()" (click)="send()">
                Enviar al cliente
              </button>
            }
            @if (contract()!.status === 'sent') {
              <button type="button" class="crm-btn" [disabled]="saving()" (click)="accept()">
                Registrar aceptación académica
              </button>
              <button type="button" class="crm-btn crm-btn--danger" [disabled]="saving()" (click)="reject()">
                Rechazar
              </button>
            }
            @if (['approved', 'sent', 'active'].includes(contract()!.status)) {
              <button type="button" class="crm-btn crm-btn--danger" [disabled]="saving()" (click)="terminate()">
                Terminar contrato
              </button>
            }
          </div>
          @if (['draft', 'sent', 'pending_approval'].includes(contract()!.status)) {
            <div class="crm-actions" style="margin-top:0.5rem">
              <button type="button" class="crm-btn crm-btn--ghost" [disabled]="saving()" (click)="expire()">
                Marcar expirado
              </button>
            </div>
          }
        </div>
      }
    </section>
  `,
})
export class CrmContractDetailPageComponent implements OnInit {
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
