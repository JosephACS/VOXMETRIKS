import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { firstValueFrom } from 'rxjs';
import { OrganizationsApiError, OrganizationsApiService } from '../services/organizations-api.service';
import { OrganizationContextService } from '../services/organization-context.service';
import { AuthService } from '../../../core/services/auth.service';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { StatusLabelPipe } from '../../../shared/pipes/status-label.pipe';
import { LocaleDatePipe, LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';

@Component({
  selector: 'app-org-accept-invite-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, TranslatePipe, StatusLabelPipe, LocaleMoneyPipe, LocaleDatePipe],
  styleUrls: ['../styles/organizations.css'],
  template: `
    <section class="org-page" data-testid="org-accept-invite-page">
      <h1>{{ 'organizations.acceptInvite.title' | t:lang() }}</h1>
      <p class="lede">
        Debes estar autenticado. El token solo se conserva en memoria durante este flujo y no se guarda en localStorage.
      </p>

      @if (!auth.isAuthenticated()) {
        <div class="org-alert org-alert--warn">
          Inicia sesión para aceptar la invitación.
          <a routerLink="/login">Ir a login</a>
        </div>
      } @else {
        @if (error()) {
          <div class="org-alert org-alert--error" role="alert">{{ error() }}</div>
        }
        @if (success()) {
          <div class="org-alert org-alert--ok" role="status">
            Invitación aceptada. Organización: {{ successOrg() }}
          </div>
          <div class="org-actions">
            <button type="button" class="org-btn" (click)="activate()" [disabled]="!successOrgId() || activating()">
              Activar organización
            </button>
            <a class="org-btn org-btn--ghost" routerLink="/discover">Continuar</a>
          </div>
        } @else {
          <form class="org-card org-form" (ngSubmit)="accept()">
            <label>
              Token de invitación
              <input name="token" [(ngModel)]="token" autocomplete="off" required [disabled]="busy()" />
            </label>
            <button class="org-btn" type="submit" [disabled]="busy() || !token.trim()">
              {{ busy() ? 'Aceptando…' : 'Aceptar' }}
            </button>
          </form>
        }
      }
    </section>
  `,
})
export class OrgAcceptInvitePageComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private readonly api = inject(OrganizationsApiService);
  private readonly ctx = inject(OrganizationContextService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  readonly auth = inject(AuthService);

  /** In-memory only for the accept flow. */
  token = '';

  readonly busy = signal(false);
  readonly activating = signal(false);
  readonly error = signal<string | null>(null);
  readonly success = signal(false);
  readonly successOrg = signal('');
  readonly successOrgId = signal<number | null>(null);

  ngOnInit(): void {
    // Prefer query token only — never path params (Referer/history leakage).
    const q = this.route.snapshot.queryParamMap.get('token');
    this.token = q || '';
  }

  async accept(): Promise<void> {
    if (this.busy() || !this.token.trim()) return;
    this.busy.set(true);
    this.error.set(null);
    const token = this.token.trim();
    try {
      const res = await firstValueFrom(this.api.acceptInvitation(token));
      this.success.set(true);
      this.successOrg.set(res.organization.display_name);
      this.successOrgId.set(res.organization.id);
      this.token = '';
      await this.ctx.refreshList();
    } catch (e) {
      this.error.set(this.mapAcceptError(e));
    } finally {
      this.busy.set(false);
    }
  }

  private mapAcceptError(e: unknown): string {
    if (!(e instanceof OrganizationsApiError)) return 'No se pudo aceptar la invitación';
    const code = e.code || '';
    if (code.includes('email') || e.message.toLowerCase().includes('email')) {
      return `Email incorrecto: ${e.message}`;
    }
    if (code.includes('expired') || e.status === 410) {
      return `Invitación no disponible (${e.status}): ${e.message}`;
    }
    if (code.includes('revoked') || code.includes('used')) {
      return e.message;
    }
    return e.message;
  }

  async activate(): Promise<void> {
    const id = this.successOrgId();
    if (!id) return;
    this.activating.set(true);
    try {
      await this.ctx.activate(id);
      await this.router.navigate(['/organizations', id, 'settings']);
    } catch (e) {
      this.error.set(e instanceof OrganizationsApiError ? e.message : 'No se pudo activar');
    } finally {
      this.activating.set(false);
    }
  }
}
