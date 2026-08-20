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
import { captureReturnUrl } from '../../../core/spaces/return-url';

@Component({
  selector: 'app-org-accept-invite-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, TranslatePipe],
  styleUrls: ['../styles/organizations.css'],
  template: `
    <section class="org-page" data-testid="org-accept-invite-page">
      <h1>{{ 'organizations.acceptInvite.title' | t: lang() }}</h1>
      <p class="lede">{{ 'organizations.acceptInvite.lede' | t: lang() }}</p>

      @if (!auth.isAuthenticated()) {
        <div class="org-alert org-alert--warn" role="status">
          {{ 'organizations.acceptInvite.needLogin' | t: lang() }}
          <div class="org-actions" style="margin-top: 0.75rem">
            <a class="org-btn" [routerLink]="['/login']" [queryParams]="loginQuery()" (click)="captureLoginReturn()">
              {{ 'organizations.acceptInvite.login' | t: lang() }}
            </a>
          </div>
        </div>
        @if (token.trim()) {
          <p class="org-muted">{{ 'organizations.acceptInvite.tokenReady' | t: lang() }}</p>
        }
      } @else {
        @if (error()) {
          <div class="org-alert org-alert--error" role="alert">{{ error() }}</div>
        }
        @if (success()) {
          <div class="org-alert org-alert--ok" role="status">
            {{ 'organizations.acceptInvite.joined' | t: { name: successOrg() }: lang() }}
          </div>
          <div class="org-actions">
            <button
              type="button"
              class="org-btn"
              (click)="activate()"
              [disabled]="!successOrgId() || activating()"
              data-testid="invite-activate"
            >
              {{ 'organizations.acceptInvite.enterSpace' | t: lang() }}
            </button>
          </div>
        } @else {
          <form class="org-card org-form" (ngSubmit)="accept()">
            <label>
              {{ 'organizations.acceptInvite.tokenLabel' | t: lang() }}
              <input
                name="token"
                [(ngModel)]="token"
                autocomplete="off"
                required
                [disabled]="busy()"
                data-testid="invite-token-input"
              />
            </label>
            <button
              class="org-btn"
              type="submit"
              [disabled]="busy() || !token.trim()"
              data-testid="invite-accept-submit"
            >
              {{
                busy()
                  ? ('organizations.acceptInvite.accepting' | t: lang())
                  : ('organizations.acceptInvite.submit' | t: lang())
              }}
            </button>
          </form>
        }
      }
    </section>
  `,
})
export class OrgAcceptInvitePageComponent implements OnInit {
  private readonly i18n = inject(I18nService);
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

  private autoAcceptStarted = false;

  ngOnInit(): void {
    // Prefer history.state; query token is stripped immediately (deep-link / email).
    const state = window.history.state as { invitationToken?: unknown } | null;
    const memoryToken =
      typeof state?.invitationToken === 'string' ? state.invitationToken.trim() : '';
    const q = this.route.snapshot.queryParamMap.get('token');
    this.token = memoryToken || q || '';
    if (q) {
      void this.router.navigate([], {
        relativeTo: this.route,
        queryParams: { token: null },
        queryParamsHandling: 'merge',
        replaceUrl: true,
      });
    }
    if (this.auth.isAuthenticated() && this.token.trim() && !this.autoAcceptStarted) {
      this.autoAcceptStarted = true;
      void this.accept();
    }
  }

  loginQuery(): { returnUrl: string } {
    const t = this.token.trim();
    const returnUrl = t
      ? `/invitations/accept?token=${encodeURIComponent(t)}`
      : '/invitations/accept';
    return { returnUrl };
  }

  captureLoginReturn(): void {
    captureReturnUrl(this.loginQuery().returnUrl);
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
    if (!(e instanceof OrganizationsApiError)) {
      return this.i18n.t('organizations.acceptInvite.errorGeneric');
    }
    const code = e.code || '';
    if (code.includes('email') || e.message.toLowerCase().includes('email')) {
      return this.i18n.t('organizations.acceptInvite.errorEmail', { message: e.message });
    }
    if (code.includes('expired') || e.status === 410) {
      return this.i18n.t('organizations.acceptInvite.errorExpired', { message: e.message });
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
      await this.router.navigate(['/organizations/onboarding'], {
        queryParams: { organization_id: id },
      });
    } catch (e) {
      this.error.set(
        e instanceof OrganizationsApiError
          ? e.message
          : this.i18n.t('organizations.acceptInvite.errorActivate'),
      );
    } finally {
      this.activating.set(false);
    }
  }
}
