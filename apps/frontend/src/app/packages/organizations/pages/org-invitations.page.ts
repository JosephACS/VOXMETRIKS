import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { Invitation } from '../models/organization.models';
import { OrganizationsApiError, OrganizationsApiService } from '../services/organizations-api.service';
import { OrganizationContextService } from '../services/organization-context.service';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
@Component({
  selector: 'app-org-invitations-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, TranslatePipe],
  styleUrls: ['../styles/organizations.css'],
  template: `
    <section class="org-page" data-testid="org-invitations-page">
      <h1>{{ 'organizations.invitations.title' | t:lang() }}</h1>
      <p class="lede">
        Modo académico: el email no se envía. El token returned-once solo se muestra una vez y nunca se guarda en localStorage.
      </p>

      @if (error()) {
        <div class="org-alert org-alert--error" role="alert">{{ error() }}</div>
      }
      @if (tokenOnce()) {
        <div class="org-alert org-alert--warn" role="status" data-testid="invite-token-banner">
          <strong>Token disponible una sola vez.</strong> Cópialo ahora; no aparecerá en el listado ni en auditoría.
          <div class="org-token-box">{{ tokenOnce() }}</div>
          <p class="org-muted">Enlace sugerido: /invitations/accept?token=…</p>
          <button type="button" class="org-btn org-btn--ghost" (click)="copyToken()">Copiar token</button>
          <button type="button" class="org-btn org-btn--ghost" (click)="tokenOnce.set(null)">Ocultar</button>
        </div>
      }

      @if (ctx.hasPermission('member.invite')) {
        <form class="org-card org-form" (ngSubmit)="create()">
          <h2>Nueva invitación</h2>
          <label>
            Email *
            <input type="email" name="email" [(ngModel)]="email" required [disabled]="busy()" />
          </label>
          <label>
            Rol inicial *
            <select name="role" [(ngModel)]="roleCode" [disabled]="busy()">
              <option value="viewer">viewer</option>
              <option value="analyst">analyst</option>
              <option value="administrator">administrator</option>
              <option value="artist_manager">artist_manager</option>
              <option value="marketing_manager">marketing_manager</option>
            </select>
          </label>
          <label>
            Expiración (días, 1–30)
            <input type="number" name="ttl" [(ngModel)]="ttlDays" min="1" max="30" [disabled]="busy()" />
          </label>
          <button class="org-btn" type="submit" [disabled]="busy() || !email.trim()">
            {{ busy() ? 'Creando…' : 'Crear invitación' }}
          </button>
        </form>
      }

      @if (loading()) {
        <p class="org-muted">{{ 'common.loading' | t:lang() }}</p>
      } @else {
        <div class="org-card" style="overflow-x:auto">
          <table class="org-table">
            <thead>
              <tr>
                <th>Email</th>
                <th>Rol</th>
                <th>Estado</th>
                <th>Expira</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              @for (inv of items(); track inv.id) {
                <tr>
                  <td>{{ inv.email_normalized }}</td>
                  <td>{{ inv.initial_role_code }}</td>
                  <td>{{ inv.status }}</td>
                  <td>{{ inv.expires_at | date: 'short' }}</td>
                  <td>
                    <div class="org-actions">
                      @if (canRevoke() && inv.status === 'pending') {
                        <button type="button" class="org-btn org-btn--ghost" (click)="revoke(inv)">Revocar</button>
                      }
                      @if (ctx.hasPermission('member.invite') && (inv.status === 'pending' || inv.status === 'revoked')) {
                        <button type="button" class="org-btn org-btn--ghost" (click)="resend(inv)">Reenviar</button>
                      }
                    </div>
                  </td>
                </tr>
              } @empty {
                <tr><td colspan="5" class="org-muted">Sin invitaciones</td></tr>
              }
            </tbody>
          </table>
        </div>
      }

      <div class="org-actions">
        <a class="org-btn org-btn--ghost" [routerLink]="['/organizations', orgId, 'members']">Volver a miembros</a>
      </div>
    </section>
  `,
})
export class OrgInvitationsPageComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private readonly api = inject(OrganizationsApiService);
  readonly ctx = inject(OrganizationContextService);
  private readonly route = inject(ActivatedRoute);

  orgId = 0;
  email = '';
  roleCode = 'viewer';
  ttlDays = 7;

  readonly items = signal<Invitation[]>([]);
  readonly loading = signal(true);
  readonly busy = signal(false);
  readonly error = signal<string | null>(null);
  readonly tokenOnce = signal<string | null>(null);

  canRevoke(): boolean {
    return this.ctx.hasPermission('invitation.revoke');
  }

  async ngOnInit(): Promise<void> {
    this.orgId = Number(this.route.snapshot.paramMap.get('id'));
    await this.load();
  }

  async load(): Promise<void> {
    this.loading.set(true);
    this.error.set(null);
    try {
      const res = await firstValueFrom(this.api.listInvitations(this.orgId));
      this.items.set(res.items);
    } catch (e) {
      this.error.set(e instanceof OrganizationsApiError ? e.message : 'Error al listar invitaciones');
    } finally {
      this.loading.set(false);
    }
  }

  async create(): Promise<void> {
    if (this.busy()) return;
    this.busy.set(true);
    this.error.set(null);
    this.tokenOnce.set(null);
    try {
      const res = await firstValueFrom(
        this.api.createInvitation(this.orgId, this.email.trim(), [this.roleCode], this.ttlDays),
      );
      if (res.invite_token && res.returned_once) {
        this.tokenOnce.set(res.invite_token);
      }
      this.email = '';
      await this.load();
    } catch (e) {
      this.error.set(e instanceof OrganizationsApiError ? e.message : 'No se pudo crear');
    } finally {
      this.busy.set(false);
    }
  }

  async revoke(inv: Invitation): Promise<void> {
    if (!confirm(`¿Revocar invitación a ${inv.email_normalized}?`)) return;
    try {
      await firstValueFrom(this.api.revokeInvitation(this.orgId, inv.id));
      await this.load();
    } catch (e) {
      this.error.set(e instanceof OrganizationsApiError ? e.message : 'No se pudo revocar');
    }
  }

  async resend(inv: Invitation): Promise<void> {
    this.tokenOnce.set(null);
    try {
      const res = await firstValueFrom(this.api.resendInvitation(this.orgId, inv.id));
      if (res.invite_token) this.tokenOnce.set(res.invite_token);
      await this.load();
    } catch (e) {
      this.error.set(e instanceof OrganizationsApiError ? e.message : 'No se pudo reenviar');
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
