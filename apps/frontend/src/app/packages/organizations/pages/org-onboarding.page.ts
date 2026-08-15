import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink, ActivatedRoute } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import {
  InvitationRoleOption,
  Membership,
  OrganizationJourney,
} from '../models/organization.models';
import { OrganizationsApiError, OrganizationsApiService } from '../services/organizations-api.service';
import { OrganizationContextService } from '../services/organization-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';

@Component({
  selector: 'app-org-onboarding-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, TranslatePipe],
  styleUrls: ['../styles/organizations.css'],
  template: `
    <section class="org-page" data-testid="org-onboarding-page">
      <h1>{{ 'organizations.onboarding.title' | t:lang() }}</h1>
      <p class="lede">{{ 'organizations.onboarding.lede' | t:lang() }}</p>

      @if (loading()) {
        <p class="org-muted" data-testid="journey-loading">Cargando recorrido…</p>
      }

      @if (error()) {
        <div class="org-alert org-alert--error" role="alert" data-testid="journey-error">{{ error() }}</div>
      }

      @if (journey(); as j) {
        <div class="org-steps" aria-label="Progreso" data-testid="journey-progress">
          <span class="org-step" [class.org-step--active]="j.next_action === 'review_profile'">Perfil</span>
          <span class="org-step" [class.org-step--active]="isPlanStep(j)">Plan</span>
          <span class="org-step" [class.org-step--active]="j.next_action === 'invite_team'">Equipo</span>
          <span class="org-step" [class.org-step--active]="j.next_action === 'complete' || j.next_action === 'enter_workspace'">Espacio</span>
        </div>

        @if (j.next_action === 'organization_unavailable') {
          <div class="org-card" data-testid="journey-unavailable">
            <h2>Organización no disponible</h2>
            <p>Esta organización no puede continuar el recorrido en este momento.</p>
            <a class="org-btn" routerLink="/discover">Volver</a>
          </div>
        } @else if (j.next_action === 'wait_for_owner') {
          <div class="org-card" data-testid="journey-wait-owner">
            <h2>Esperando configuración</h2>
            <p>Un administrador debe completar el plan y la configuración inicial.</p>
            <a class="org-btn" [routerLink]="hubLink()">Espacio de la organización</a>
          </div>
        } @else if (j.next_action === 'review_profile') {
          <div class="org-card org-form" data-testid="journey-profile">
            <h2>Revisar perfil</h2>
            <label>
              Nombre visible
              <input [(ngModel)]="displayName" name="display_name" />
            </label>
            <label>
              Nombre legal
              <input [(ngModel)]="legalName" name="legal_name" />
            </label>
            <div class="org-actions">
              <button type="button" class="org-btn" (click)="saveProfile()" [disabled]="saving() || !j.capabilities.update_profile">
                {{ saving() ? 'Guardando…' : 'Guardar y continuar' }}
              </button>
            </div>
          </div>
        } @else if (isPlanStep(j)) {
          <div class="org-card" data-testid="journey-plan">
            <h2>{{ 'organizations.onboarding.choosePlanTitle' | t:lang() }}</h2>
            <p>{{ 'organizations.onboarding.choosePlanBody' | t:lang() }}</p>
            @if (j.subscription.plan_name) {
              <p class="org-muted">Plan: {{ j.subscription.plan_name }}</p>
            }
            <div class="org-actions">
              @if (j.capabilities.resume_checkout && j.checkout) {
                <a
                  class="org-btn"
                  [routerLink]="['/subscriptions/checkout']"
                  [queryParams]="{ organization_id: orgId(), checkout_id: j.checkout.id }"
                  data-testid="journey-resume-checkout"
                  >Reanudar pago</a
                >
              }
              @if (j.capabilities.choose_plan) {
                <a
                  class="org-btn"
                  routerLink="/subscriptions/select-plan"
                  [queryParams]="{ organization_id: orgId() }"
                  data-testid="journey-choose-plan"
                >
                  {{ 'business.forEnterprises.ctaChoosePlan' | t:lang() }}
                </a>
                <a
                  class="org-btn org-btn--ghost"
                  routerLink="/subscriptions/trial"
                  [queryParams]="{ organization_id: orgId() }"
                  data-testid="journey-trial"
                >
                  {{ 'business.forEnterprises.ctaTrial' | t:lang() }}
                </a>
              }
              @if (j.next_action === 'await_payment') {
                <p class="org-muted" data-testid="journey-await-payment">Procesando el pago simulado…</p>
              }
            </div>
          </div>
        } @else if (j.next_action === 'invite_team') {
          <div class="org-card org-form" data-testid="journey-team">
            <h2>Equipo</h2>
            <p class="org-muted">
              Miembros activos: {{ j.team.active_members }} · Invitaciones pendientes: {{ j.team.pending_invitations }}
            </p>
            @if (j.capabilities.invite_team) {
              <label>
                Email
                <input type="email" [(ngModel)]="inviteEmail" name="invite_email" />
              </label>
              <label>
                Rol
                <select [(ngModel)]="inviteRole" name="invite_role">
                  @for (r of inviteRoles(); track r.code) {
                    <option [value]="r.code">{{ r.label }}</option>
                  }
                </select>
              </label>
              <div class="org-actions">
                <button type="button" class="org-btn" (click)="invite()" [disabled]="saving() || !inviteEmail.trim()">
                  Enviar invitación
                </button>
                <button
                  type="button"
                  class="org-btn org-btn--ghost"
                  (click)="skipTeam()"
                  [disabled]="saving()"
                  data-testid="journey-skip-team"
                >
                  Continuar sin invitar
                </button>
              </div>
            }
            @if (j.capabilities.view_members && members().length) {
              <ul data-testid="journey-member-list">
                @for (m of members(); track m.id) {
                  <li>
                    {{ memberLabel(m) }}
                    · {{ m.status_label || humanStatus(m.status) }}
                    @if (m.roles?.length) {
                      · {{ roleLabels(m) }}
                    }
                  </li>
                }
              </ul>
            }
          </div>
        } @else if (j.next_action === 'complete') {
          <div class="org-card" data-testid="journey-complete">
            <h2>Listo para el espacio empresarial</h2>
            <p>Confirma para cerrar el recorrido inicial. Podrás editar equipo y permisos después.</p>
            <div class="org-actions">
              <button
                type="button"
                class="org-btn"
                (click)="complete()"
                [disabled]="saving()"
                data-testid="journey-complete-submit"
              >
                Completar recorrido
              </button>
            </div>
          </div>
        } @else if (j.next_action === 'enter_workspace') {
          <div class="org-card" data-testid="journey-enter-workspace">
            <h2>Espacio listo</h2>
            <p>Puedes entrar al espacio de la organización.</p>
            <div class="org-actions">
              <a class="org-btn" [routerLink]="hubLink()" data-testid="journey-enter-hub">Entrar</a>
              @if (j.allowed_destinations.includes('team') && j.capabilities.view_members) {
                <a class="org-btn org-btn--ghost" [routerLink]="['/organizations', orgId(), 'members']">Equipo</a>
              }
            </div>
          </div>
        }
      }
    </section>
  `,
})
export class OrgOnboardingPageComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;
  readonly ctx = inject(OrganizationContextService);
  private readonly api = inject(OrganizationsApiService);
  private readonly router = inject(Router);
  private readonly route = inject(ActivatedRoute);

  readonly journey = signal<OrganizationJourney | null>(null);
  readonly loading = signal(true);
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);
  readonly inviteRoles = signal<InvitationRoleOption[]>([]);
  readonly members = signal<Membership[]>([]);
  readonly orgId = signal<number | null>(null);

  displayName = '';
  legalName = '';
  inviteEmail = '';
  inviteRole = 'viewer';

  async ngOnInit(): Promise<void> {
    if (this.ctx.status() === 'idle') await this.ctx.bootstrap();
    const qOrg = Number(this.route.snapshot.queryParamMap.get('organization_id') || 0);
    if (qOrg > 0 && this.ctx.organizationId() !== qOrg) {
      await this.ctx.activate(qOrg);
      if (this.ctx.organizationId() !== qOrg) {
        this.error.set('No se pudo activar la organización solicitada.');
        this.loading.set(false);
        return;
      }
    }
    await this.reload();
  }

  isPlanStep(j: OrganizationJourney): boolean {
    return (
      j.next_action === 'choose_plan' ||
      j.next_action === 'resume_checkout' ||
      j.next_action === 'await_payment'
    );
  }

  hubLink(): string[] {
    const id = this.orgId();
    return id ? ['/organizations', String(id)] : ['/organizations', 'none'];
  }

  memberLabel(m: Membership): string {
    return m.user?.display_name?.trim() || 'Miembro';
  }

  roleLabels(m: Membership): string {
    return (m.roles || []).map((r) => r.label).join(', ');
  }

  humanStatus(status: string): string {
    const map: Record<string, string> = {
      active: 'Activo',
      suspended: 'Suspendido',
      left: 'Salió',
      removed: 'Eliminado',
    };
    return map[status] || status;
  }

  async reload(): Promise<void> {
    this.loading.set(true);
    this.error.set(null);
    try {
      const org = this.ctx.activeOrganization();
      if (!org) {
        this.error.set('Activa una organización para continuar.');
        this.journey.set(null);
        return;
      }
      this.orgId.set(org.id);
      const j = await firstValueFrom(this.api.getJourney(org.id));
      this.journey.set(j);
      this.displayName = j.organization.display_name || org.display_name;
      this.legalName = j.organization.legal_name || '';
      if (j.next_action === 'invite_team') {
        await this.loadTeamExtras(org.id, j);
      }
      if (j.next_action === 'enter_workspace' && j.capabilities.enter_workspace) {
        // Soft land: stay on page with CTA (user confirms).
      }
    } catch (e) {
      this.error.set(this.mapError(e));
      this.journey.set(null);
    } finally {
      this.loading.set(false);
    }
  }

  private async loadTeamExtras(orgId: number, j: OrganizationJourney): Promise<void> {
    if (j.capabilities.invite_team) {
      try {
        const roles = await firstValueFrom(this.api.invitationRoles(orgId));
        this.inviteRoles.set(roles.items);
        if (roles.items.length && !roles.items.some((r) => r.code === this.inviteRole)) {
          this.inviteRole = roles.items[0].code;
        }
      } catch {
        this.inviteRoles.set([{ code: 'viewer', label: 'Solo lectura' }]);
      }
    }
    if (j.capabilities.view_members) {
      try {
        const page = await firstValueFrom(this.api.listMembers(orgId));
        this.members.set(page.items);
      } catch {
        this.members.set([]);
      }
    }
  }

  async saveProfile(): Promise<void> {
    const id = this.orgId();
    if (!id) return;
    this.saving.set(true);
    this.error.set(null);
    try {
      await firstValueFrom(
        this.api.update(id, {
          display_name: this.displayName.trim(),
          legal_name: this.legalName.trim() || undefined,
        }),
      );
      await this.ctx.bootstrap();
      await this.reload();
    } catch (e) {
      this.error.set(this.mapError(e));
    } finally {
      this.saving.set(false);
    }
  }

  async invite(): Promise<void> {
    const id = this.orgId();
    if (!id) return;
    this.saving.set(true);
    this.error.set(null);
    try {
      await firstValueFrom(
        this.api.createInvitation(id, this.inviteEmail.trim(), [this.inviteRole], 7),
      );
      this.inviteEmail = '';
      await this.reload();
    } catch (e) {
      this.error.set(this.mapError(e));
    } finally {
      this.saving.set(false);
    }
  }

  async skipTeam(): Promise<void> {
    const id = this.orgId();
    if (!id) return;
    this.saving.set(true);
    this.error.set(null);
    try {
      const j = await firstValueFrom(this.api.skipJourneyTeam(id));
      this.journey.set(j);
      await this.reload();
    } catch (e) {
      this.error.set(this.mapError(e));
    } finally {
      this.saving.set(false);
    }
  }

  async complete(): Promise<void> {
    const id = this.orgId();
    if (!id) return;
    this.saving.set(true);
    this.error.set(null);
    try {
      const key = `journey-complete-${id}-${Date.now()}`;
      const j = await firstValueFrom(
        this.api.completeJourney(id, { idempotency_key: key, team_step_skipped: true }),
      );
      this.journey.set(j);
      if (j.next_action === 'enter_workspace' && j.capabilities.enter_workspace) {
        await this.ctx.bootstrap({ force: true });
        await this.router.navigate(this.hubLink());
        return;
      }
      await this.reload();
    } catch (e) {
      this.error.set(this.mapError(e));
    } finally {
      this.saving.set(false);
    }
  }

  private mapError(e: unknown): string {
    if (!(e instanceof OrganizationsApiError)) return 'No se pudo continuar';
    if (e.code === 'journey_prerequisite_missing') {
      return 'Aún faltan pasos antes de completar el recorrido.';
    }
    if (e.code === 'permission_denied' || e.status === 403) {
      return 'No tienes permiso para esta acción.';
    }
    if (e.code === 'network_error') return 'Sin conexión. Reintenta.';
    return e.message || 'No se pudo continuar';
  }
}
