import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { CrmApiError, CrmApiService } from '../services/crm-api.service';
import { CustomerConversion } from '../models/crm.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
type WizardStep = 'view' | 'confirm-link' | 'claim';

@Component({
  selector: 'app-crm-conversion-wizard-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, TranslatePipe],
  styleUrls: ['../styles/crm.css'],
  template: `
    <section class="crm-page" data-testid="crm-conversion-wizard-page">
      <div style="display:flex;align-items:center;gap:0.75rem;flex-wrap:wrap;margin-bottom:0.5rem">
        <a class="crm-btn crm-btn--ghost" routerLink="/crm/opportunities">← Oportunidades</a>
        <h1 style="margin:0">Conversión de cliente #{{ conversionId }}</h1>
        @if (conv()) {
          <span class="crm-badge crm-badge--{{ conv()!.status }}">{{ conv()!.status }}</span>
        }
      </div>

      @if (error()) {
        <div class="crm-alert crm-alert--error" role="alert">{{ error() }}</div>
      }
      @if (success()) {
        <div class="crm-alert crm-alert--ok" role="status">{{ success() }}</div>
      }

      <!-- Wizard steps indicator -->
      <div class="crm-wizard-steps">
        <span class="crm-wizard-step" [class.crm-wizard-step--active]="step === 'view'">1. Estado</span>
        <span class="crm-wizard-step" [class.crm-wizard-step--active]="step === 'confirm-link'"
          [class.crm-wizard-step--done]="step !== 'confirm-link'">2. Confirmar enlace</span>
        <span class="crm-wizard-step" [class.crm-wizard-step--active]="step === 'claim'"
          [class.crm-wizard-step--done]="step !== 'claim'">3. Reclamar token</span>
      </div>

      @if (loading()) {
        <p class="crm-muted">{{ 'common.loading' | t:lang() }}</p>
      } @else if (conv()) {

        <!-- Step 1: View conversion state -->
        @if (step === 'view') {
          <div class="crm-card">
            <h2>Estado de la conversión</h2>
            <dl style="display:grid;grid-template-columns:auto 1fr;gap:0.3rem 1rem;font-size:0.875rem">
              <dt class="crm-muted">Oportunidad</dt><dd>#{{ conv()!.opportunity_id }}</dd>
              <dt class="crm-muted">Modo</dt><dd>{{ conv()!.mode }}</dd>
              <dt class="crm-muted">Estado</dt>
              <dd><span class="crm-badge crm-badge--{{ conv()!.status }}">{{ conv()!.status }}</span></dd>
              @if (conv()!.organization_id) {
                <dt class="crm-muted">Organización vinculada</dt><dd>#{{ conv()!.organization_id }}</dd>
              }
              @if (conv()!.contact_id) {
                <dt class="crm-muted">Contacto</dt><dd>#{{ conv()!.contact_id }}</dd>
              }
              @if (conv()!.claim_token_expires_at) {
                <dt class="crm-muted">Token expira</dt><dd>{{ conv()!.claim_token_expires_at | date:'medium' }}</dd>
              }
              @if (conv()!.completed_at) {
                <dt class="crm-muted">Completado</dt><dd>{{ conv()!.completed_at | date:'medium' }}</dd>
              }
              @if (conv()!.failure_reason) {
                <dt class="crm-muted">Motivo falla</dt><dd>{{ conv()!.failure_reason }}</dd>
              }
              <dt class="crm-muted">Creado</dt><dd>{{ conv()!.created_at | date:'medium' }}</dd>
            </dl>
          </div>

          @if (conv()!.status === 'completed' && conv()!.organization_id) {
            <div class="crm-card">
              <h2>Siguiente paso comercial</h2>
              <p class="crm-muted">
                La conversión está completa. Continúa con la selección explícita de plan
                (no se crea suscripción automáticamente).
              </p>
              <div class="crm-actions">
                <button type="button" class="crm-btn" [disabled]="saving()"
                  (click)="continueToPlan()">
                  Continuar con plan y suscripción
                </button>
              </div>
            </div>
          }

          @if (conv()!.status === 'pending' || conv()!.status === 'prepared') {
            <div class="crm-card">
              <h2>Continuar proceso</h2>
              <div class="crm-actions">
                @if (conv()!.mode === 'link_existing') {
                  <button type="button" class="crm-btn" (click)="step = 'confirm-link'">
                    Confirmar enlace (soy el propietario de la org)
                  </button>
                }
                @if (conv()!.mode === 'create_org') {
                  <button type="button" class="crm-btn" (click)="step = 'claim'">
                    Reclamar con token
                  </button>
                }
              </div>
            </div>
          }
        }

        <!-- Step 2: Confirm link (Path A - org owner) -->
        @if (step === 'confirm-link') {
          <div class="crm-card">
            <h2>Confirmar enlace de organización</h2>
            <p class="crm-muted">
              Confirma que eres el propietario activo de la organización y autoriza el enlace.
            </p>
            <div class="crm-form">
              <label>ID de organización *
                <input [(ngModel)]="linkOrgId" name="linkOrgId" type="number" min="1"
                  placeholder="ID de tu organización" />
              </label>
              <div class="crm-actions">
                <button type="button" class="crm-btn" [disabled]="!linkOrgId || saving()"
                  (click)="confirmLink()">
                  {{ saving() ? 'Procesando…' : 'Confirmar enlace' }}
                </button>
                <button type="button" class="crm-btn crm-btn--ghost" (click)="step = 'view'">
                  Cancelar
                </button>
              </div>
            </div>
          </div>
        }

        <!-- Step 3: Claim with token (Path B - signatory) -->
        @if (step === 'claim') {
          <div class="crm-card">
            <h2>Reclamar conversión con token</h2>
            <div class="crm-alert crm-alert--warn">
              El token de reclamación debe haberte sido entregado por el agente de ventas de forma segura.
              No almacenes tokens en localStorage ni compartas por correo.
            </div>
            <div class="crm-form">
              <label>Token de reclamación *
                <input [(ngModel)]="claimToken" name="claimToken" type="password"
                  placeholder="Pega el token aquí" autocomplete="off" />
              </label>
              <label>Nombre de la nueva organización *
                <input [(ngModel)]="claimOrgName" name="claimOrgName" required />
              </label>
              <label>Slug de la organización *
                <input [(ngModel)]="claimOrgSlug" name="claimOrgSlug" required
                  placeholder="mi-empresa" pattern="[a-z0-9-]+" />
              </label>
              <label>Tipo de organización
                <select [(ngModel)]="claimOrgType" name="claimOrgType">
                  <option value="business">Empresa</option>
                  <option value="individual">Particular</option>
                  <option value="nonprofit">Sin ánimo de lucro</option>
                </select>
              </label>
              <label>Zona horaria
                <input [(ngModel)]="claimTimezone" name="claimTimezone" placeholder="America/Guayaquil" />
              </label>
              <label>Moneda
                <input [(ngModel)]="claimCurrency" name="claimCurrency" maxlength="3" placeholder="USD" />
              </label>
              <div class="crm-actions">
                <button type="button" class="crm-btn"
                  [disabled]="!claimToken || !claimOrgName || !claimOrgSlug || saving()"
                  (click)="claim()">
                  {{ saving() ? 'Procesando…' : 'Reclamar' }}
                </button>
                <button type="button" class="crm-btn crm-btn--ghost" (click)="step = 'view'">
                  Cancelar
                </button>
              </div>
            </div>
          </div>
        }
      }
    </section>
  `,
})
export class CrmConversionWizardPageComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private readonly api = inject(CrmApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly orgCtx = inject(OrganizationContextService);

  conversionId = 0;
  step: WizardStep = 'view';

  linkOrgId: number | null = null;
  claimToken = '';
  claimOrgName = '';
  claimOrgSlug = '';
  claimOrgType = 'business';
  claimTimezone = 'UTC';
  claimCurrency = 'USD';

  readonly conv = signal<CustomerConversion | null>(null);
  readonly loading = signal(true);
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);
  readonly success = signal<string | null>(null);

  async ngOnInit(): Promise<void> {
    this.conversionId = Number(this.route.snapshot.paramMap.get('id'));
    await this.load();
  }

  async load(): Promise<void> {
    this.loading.set(true);
    this.error.set(null);
    this.success.set(null);
    try {
      const c = await firstValueFrom(this.api.getConversion(this.conversionId));
      this.conv.set(c);
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al cargar conversión');
    } finally {
      this.loading.set(false);
    }
  }

  async confirmLink(): Promise<void> {
    if (!this.linkOrgId) return;
    this.saving.set(true);
    this.error.set(null);
    try {
      const c = await firstValueFrom(this.api.confirmLinkConversion(this.conversionId, this.linkOrgId));
      this.conv.set(c);
      this.step = 'view';
      this.success.set('Enlace confirmado. Conversión completada.');
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al confirmar enlace');
    } finally {
      this.saving.set(false);
    }
  }

  async claim(): Promise<void> {
    if (!this.claimToken || !this.claimOrgName || !this.claimOrgSlug) return;
    this.saving.set(true);
    this.error.set(null);
    try {
      const c = await firstValueFrom(
        this.api.claimConversion(
          this.conversionId,
          this.claimToken,
          this.claimOrgName,
          this.claimOrgSlug,
          this.claimOrgType,
          this.claimTimezone,
          this.claimCurrency,
        ),
      );
      this.conv.set(c);
      this.claimToken = '';
      this.step = 'view';
      this.success.set('Conversión reclamada. Organización creada.');
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al reclamar conversión');
    } finally {
      this.saving.set(false);
    }
  }

  async continueToPlan(): Promise<void> {
    const c = this.conv();
    const orgId = c?.organization_id;
    if (!orgId) {
      this.error.set('La conversión no tiene organización vinculada.');
      return;
    }
    this.saving.set(true);
    this.error.set(null);
    try {
      await this.orgCtx.activate(orgId);
      await this.router.navigate(['/subscriptions/select-plan'], {
        queryParams: { organizationId: orgId, conversionId: this.conversionId },
      });
    } catch (e) {
      this.error.set(e instanceof Error ? e.message : 'No se pudo activar la organización');
    } finally {
      this.saving.set(false);
    }
  }
}
