import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
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
      <p class="lede">
        Solo perfil básico e invitación opcional. Sin plan, pago, billing, artista ni campaña.
        Puedes salir y seguir usando la app en modo personal.
      </p>

      <div class="org-steps" aria-label="Pasos de onboarding">
        @for (s of steps; track s.id; let i = $index) {
          <span class="org-step" [class.org-step--active]="step() === i">{{ s.label }}</span>
        }
      </div>

      @if (error()) {
        <div class="org-alert org-alert--error" role="alert">{{ error() }}</div>
      }
      @if (tokenOnce()) {
        <div class="org-alert org-alert--warn" role="status">
          <strong>Modo académico:</strong> el email no fue enviado. Copia el token ahora; no se podrá consultar después.
          <div class="org-token-box" data-testid="invite-token-once">{{ tokenOnce() }}</div>
          <button type="button" class="org-btn org-btn--ghost" (click)="copyToken()">Copiar token</button>
        </div>
      }

      @if (step() === 0) {
        <div class="org-card">
          <h2>Organización creada</h2>
          @if (ctx.activeOrganization(); as org) {
            <p><strong>{{ org.display_name }}</strong> · {{ org.slug }} · {{ org.status }}</p>
          } @else {
            <p class="org-muted">Sin organización activa. Crea o activa una primero.</p>
          }
          <div class="org-actions">
            <button type="button" class="org-btn" (click)="next()" [disabled]="!ctx.activeOrganization()">Continuar</button>
            <a class="org-btn org-btn--ghost" routerLink="/discover">Salir al modo personal</a>
          </div>
        </div>
      }

      @if (step() === 1) {
        <div class="org-card org-form">
          <h2>Perfil básico</h2>
          <label>
            Nombre visible
            <input [(ngModel)]="displayName" name="display_name" />
          </label>
          <label>
            Nombre legal
            <input [(ngModel)]="legalName" name="legal_name" />
          </label>
          <div class="org-actions">
            <button type="button" class="org-btn" (click)="saveProfile()" [disabled]="saving()">
              {{ saving() ? 'Guardando…' : 'Guardar y continuar' }}
            </button>
            <button type="button" class="org-btn org-btn--ghost" (click)="next()">Omitir</button>
          </div>
        </div>
      }

      @if (step() === 2) {
        <div class="org-card org-form">
          <h2>Invitar primer miembro (opcional)</h2>
          <label>
            Email
            <input type="email" [(ngModel)]="inviteEmail" name="invite_email" />
          </label>
          <label>
            Rol inicial
            <select [(ngModel)]="inviteRole" name="invite_role">
              <option value="viewer">viewer</option>
              <option value="analyst">analyst</option>
              <option value="administrator">administrator</option>
            </select>
          </label>
          <div class="org-actions">
            <button type="button" class="org-btn" (click)="invite()" [disabled]="saving() || !inviteEmail.trim()">
              Crear invitación
            </button>
            <button type="button" class="org-btn org-btn--ghost" (click)="next()">Omitir</button>
          </div>
        </div>
      }

      @if (step() === 3) {
        <div class="org-card">
          <h2>Revisar miembros</h2>
          @if (membersLoading()) {
            <p class="org-muted">Cargando miembros…</p>
          } @else if (!members().length) {
            <p class="org-muted">Sin miembros listados (o sin permiso member.view).</p>
          } @else {
            <ul>
              @for (m of members(); track m.id) {
                <li>user #{{ m.user_id }} · {{ m.status }}</li>
              }
            </ul>
          }
          <div class="org-actions">
            <button type="button" class="org-btn" (click)="next()">Continuar</button>
          </div>
        </div>
      }

      @if (step() === 4) {
        <div class="org-card">
          <h2>Onboarding completo</h2>
          <p>Puedes gestionar la organización desde el menú y el selector del shell.</p>
          <div class="org-actions">
            <a class="org-btn" [routerLink]="settingsLink()">Ir a configuración</a>
            <a class="org-btn org-btn--ghost" routerLink="/discover">Ir a inicio</a>
          </div>
        </div>
      }
    </section>
  `,
})
export class OrgOnboardingPageComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  readonly ctx = inject(OrganizationContextService);
  private readonly api = inject(OrganizationsApiService);

  readonly steps = [
    { id: 'created', label: '1. Creada' },
    { id: 'profile', label: '2. Perfil' },
    { id: 'invite', label: '3. Invitar' },
    { id: 'members', label: '4. Miembros' },
    { id: 'done', label: '5. Listo' },
  ];

  readonly step = signal(0);
  readonly error = signal<string | null>(null);
  readonly saving = signal(false);
  readonly tokenOnce = signal<string | null>(null);
  readonly members = signal<{ id: number; user_id: number; status: string }[]>([]);
  readonly membersLoading = signal(false);

  displayName = '';
  legalName = '';
  inviteEmail = '';
  inviteRole = 'viewer';

  async ngOnInit(): Promise<void> {
    if (this.ctx.status() === 'idle') await this.ctx.bootstrap();
    const org = this.ctx.activeOrganization();
    if (org) {
      this.displayName = org.display_name;
      this.legalName = org.legal_name ?? '';
    }
  }

  next(): void {
    this.error.set(null);
    const n = this.step() + 1;
    this.step.set(Math.min(n, 4));
    if (n === 3) void this.loadMembers();
  }

  settingsLink(): string[] {
    const id = this.ctx.activeOrganization()?.id;
    return id ? ['/organizations', String(id), 'settings'] : ['/organizations', 'none'];
  }

  async saveProfile(): Promise<void> {
    const org = this.ctx.activeOrganization();
    if (!org) return;
    this.saving.set(true);
    this.error.set(null);
    try {
      await firstValueFrom(
        this.api.update(org.id, {
          display_name: this.displayName.trim(),
          legal_name: this.legalName.trim() || undefined,
        }),
      );
      await this.ctx.bootstrap();
      this.next();
    } catch (e) {
      this.error.set(e instanceof OrganizationsApiError ? e.message : 'No se pudo guardar');
    } finally {
      this.saving.set(false);
    }
  }

  async invite(): Promise<void> {
    const org = this.ctx.activeOrganization();
    if (!org) return;
    this.saving.set(true);
    this.error.set(null);
    this.tokenOnce.set(null);
    try {
      const res = await firstValueFrom(
        this.api.createInvitation(org.id, this.inviteEmail.trim(), [this.inviteRole], 7),
      );
      if (res.invite_token && res.returned_once) {
        this.tokenOnce.set(res.invite_token);
      }
      this.next();
    } catch (e) {
      this.error.set(e instanceof OrganizationsApiError ? e.message : 'No se pudo invitar');
    } finally {
      this.saving.set(false);
    }
  }

  async loadMembers(): Promise<void> {
    const org = this.ctx.activeOrganization();
    if (!org) return;
    this.membersLoading.set(true);
    try {
      const page = await firstValueFrom(this.api.listMembers(org.id));
      this.members.set(page.items);
    } catch {
      this.members.set([]);
    } finally {
      this.membersLoading.set(false);
    }
  }

  async copyToken(): Promise<void> {
    const t = this.tokenOnce();
    if (!t) return;
    try {
      await navigator.clipboard.writeText(t);
    } catch {
      /* ignore */
    }
  }
}
