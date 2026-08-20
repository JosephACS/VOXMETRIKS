import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { Invitation, InvitationRoleOption } from '../models/organization.models';
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
      <p class="lede">Invita personas al equipo. El correo se entrega cuando el canal esté configurado.</p>

      @if (error()) {
        <div class="org-alert org-alert--error" role="alert">{{ error() }}</div>
      }
      @if (feedback()) {
        <div class="org-alert org-alert--ok" role="status">{{ feedback() }}</div>
      }
      @if (tokenOnce()) {
        <div class="org-alert org-alert--warn" role="status" data-testid="invite-token-banner">
          <p>{{ 'organizations.invitations.tokenOnce' | t: lang() }}</p>
          <p class="org-muted">{{ 'organizations.invitations.tokenOnceBody' | t: lang() }}</p>
          <div class="org-token-box" data-testid="invite-deep-link">{{ inviteDeepLink() }}</div>
          <div class="org-actions" style="margin-top: 0.5rem">
            <button type="button" class="org-btn org-btn--ghost" (click)="copyDeepLink()">
              {{ 'organizations.invitations.copyLink' | t: lang() }}
            </button>
            <button type="button" class="org-btn org-btn--ghost" (click)="copyToken()">
              {{ 'organizations.invitations.copyToken' | t: lang() }}
            </button>
            <button type="button" class="org-btn" (click)="openAccept()">
              {{ 'organizations.invitations.openAccept' | t: lang() }}
            </button>
            <button type="button" class="org-btn org-btn--ghost" (click)="tokenOnce.set(null)">
              {{ 'organizations.invitations.hideToken' | t: lang() }}
            </button>
          </div>
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
              @for (r of roleOptions(); track r.code) {
                <option [value]="r.code">{{ r.label }}</option>
              }
            </select>
          </label>
          <label>
            Validez (días)
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
        <div class="org-card" style="overflow-x: auto">
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
                  <td>{{ roleLabel(inv.initial_role_code) }}</td>
                  <td>{{ statusLabel(inv.status) }}</td>
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
                <tr>
                  <td colspan="5" class="org-muted">Sin invitaciones</td>
                </tr>
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
  private readonly router = inject(Router);

  orgId = 0;
  email = '';
  roleCode = 'viewer';
  ttlDays = 7;

  readonly items = signal<Invitation[]>([]);
  readonly roleOptions = signal<InvitationRoleOption[]>([]);
  readonly loading = signal(true);
  readonly busy = signal(false);
  readonly error = signal<string | null>(null);
  readonly feedback = signal<string | null>(null);
  readonly tokenOnce = signal<string | null>(null);

  canRevoke(): boolean {
    return this.ctx.hasPermission('invitation.revoke');
  }

  statusLabel(status: string): string {
    const map: Record<string, string> = {
      pending: 'Pendiente',
      accepted: 'Aceptada',
      expired: 'Expirada',
      revoked: 'Revocada',
    };
    return map[status] || status;
  }

  roleLabel(code: string): string {
    return this.roleOptions().find((r) => r.code === code)?.label || code;
  }

  async ngOnInit(): Promise<void> {
    this.orgId = Number(this.route.snapshot.paramMap.get('id'));
    await Promise.all([this.loadRoles(), this.load()]);
  }

  async loadRoles(): Promise<void> {
    if (!this.ctx.hasPermission('member.invite')) return;
    try {
      const res = await firstValueFrom(this.api.invitationRoles(this.orgId));
      this.roleOptions.set(res.items);
      if (res.items.length && !res.items.some((r) => r.code === this.roleCode)) {
        this.roleCode = res.items[0].code;
      }
    } catch {
      this.roleOptions.set([{ code: 'viewer', label: 'Solo lectura' }]);
    }
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
    this.feedback.set(null);
    this.tokenOnce.set(null);
    try {
      const res = await firstValueFrom(
        this.api.createInvitation(this.orgId, this.email.trim(), [this.roleCode], this.ttlDays),
      );
      if (res.invite_token && res.returned_once) {
        this.tokenOnce.set(res.invite_token);
      }
      this.feedback.set(this.i18n.t('organizations.invitations.created'));
      this.email = '';
      await this.load();
    } catch (e) {
      this.error.set(e instanceof OrganizationsApiError ? e.message : this.i18n.t('organizations.invitations.createFailed'));
    } finally {
      this.busy.set(false);
    }
  }

  async revoke(inv: Invitation): Promise<void> {
    if (!confirm(this.i18n.t('organizations.invitations.revokeConfirm', { email: inv.email_normalized }))) {
      return;
    }
    try {
      await firstValueFrom(this.api.revokeInvitation(this.orgId, inv.id));
      this.feedback.set(this.i18n.t('organizations.invitations.revoked'));
      await this.load();
    } catch (e) {
      this.error.set(e instanceof OrganizationsApiError ? e.message : this.i18n.t('organizations.invitations.revokeFailed'));
    }
  }

  async resend(inv: Invitation): Promise<void> {
    this.tokenOnce.set(null);
    this.feedback.set(null);
    try {
      const res = await firstValueFrom(this.api.resendInvitation(this.orgId, inv.id));
      if (res.invite_token) this.tokenOnce.set(res.invite_token);
      this.feedback.set(this.i18n.t('organizations.invitations.resent'));
      await this.load();
    } catch (e) {
      this.error.set(e instanceof OrganizationsApiError ? e.message : this.i18n.t('organizations.invitations.resendFailed'));
    }
  }

  inviteDeepLink(): string {
    const t = this.tokenOnce();
    if (!t) return '';
    const origin = typeof window !== 'undefined' ? window.location.origin : '';
    return `${origin}/invitations/accept?token=${encodeURIComponent(t)}`;
  }

  async copyDeepLink(): Promise<void> {
    const link = this.inviteDeepLink();
    if (!link) return;
    try {
      await navigator.clipboard.writeText(link);
      this.feedback.set(this.i18n.t('organizations.invitations.linkCopied'));
    } catch {
      this.error.set(this.i18n.t('organizations.invitations.copyFailed'));
    }
  }

  async copyToken(): Promise<void> {
    const t = this.tokenOnce();
    if (!t) return;
    try {
      await navigator.clipboard.writeText(t);
      this.feedback.set(this.i18n.t('organizations.invitations.tokenCopied'));
    } catch {
      this.error.set(this.i18n.t('organizations.invitations.copyFailed'));
    }
  }

  openAccept(): void {
    const t = this.tokenOnce();
    if (!t) return;
    void this.router.navigate(['/invitations/accept'], {
      state: { invitationToken: t },
    });
  }
}
