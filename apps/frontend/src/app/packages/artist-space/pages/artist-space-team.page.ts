import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ArtistContextService } from '../services/artist-context.service';
import { ArtistSpaceApiService } from '../services/artist-space-api.service';
import { ArtistAccessRequest, ArtistInvitation } from '../models/artist-space.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-artist-space-team',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise">
      <app-enterprise-page-header
        [title]="'artistSpace.team.title' | t:lang()"
        [subtitle]="'artistSpace.team.subtitle' | t:lang()"
      />

      @if (canInvite()) {
        <app-enterprise-section-card [title]="'artistSpace.team.invite' | t:lang()">
          <form [formGroup]="inviteForm" (ngSubmit)="invite()" class="form-grid">
            <app-enterprise-form-field [label]="'common.email' | t:lang()" [required]="true">
              <input class="input" formControlName="email" type="email" />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'artistSpace.team.role' | t:lang()">
              <select class="input" formControlName="role">
                <option value="administrator">administrator</option>
                <option value="member">member</option>
                <option value="reader">reader</option>
              </select>
            </app-enterprise-form-field>
            <button type="submit" class="btn btn--primary" [disabled]="inviteForm.invalid">
              {{ 'artistSpace.team.invite' | t:lang() }}
            </button>
          </form>
          @if (inviteToken()) {
            <p class="token-box">
              {{ tokenHint() }}
              <code>{{ inviteToken() }}</code>
            </p>
          }
        </app-enterprise-section-card>

        <app-enterprise-section-card [title]="'artistSpace.team.pendingInvites' | t:lang()">
          @if (!pendingInvites().length) {
            <p>{{ 'artistSpace.team.noPendingInvites' | t:lang() }}</p>
          } @else {
            <ul class="invite-list">
              @for (inv of pendingInvites(); track inv.id) {
                <li>
                  <span>
                    {{ inv.email_normalized }} — {{ inv.role }} —
                    {{ inv.status }} —
                    {{ inv.expires_at }}
                  </span>
                  <button type="button" class="btn btn--secondary" (click)="resendInvite(inv)">
                    {{ 'artistSpace.team.resendInvite' | t:lang() }}
                  </button>
                  <button type="button" class="btn btn--secondary" (click)="revokeInvite(inv)">
                    {{ 'artistSpace.team.revokeInvite' | t:lang() }}
                  </button>
                </li>
              }
            </ul>
          }
        </app-enterprise-section-card>
      }

      @if (loading()) {
        <app-enterprise-loading-skeleton [rows]="3" />
      } @else if (error()) {
        <app-enterprise-error-state [message]="error()!" (retry)="load()" />
      } @else {
        <app-enterprise-section-card [title]="'artistSpace.team.members' | t:lang()">
          <ul class="member-list">
            @for (m of members(); track memberId(m)) {
              <li>
                <span>{{ memberLabel(m) }} — {{ memberRole(m) }}</span>
                @if (canManage() && memberRole(m) !== 'owner') {
                  <button type="button" class="btn btn--secondary" (click)="revoke(m)">
                    {{ 'artistSpace.team.revoke' | t:lang() }}
                  </button>
                }
              </li>
            }
          </ul>
        </app-enterprise-section-card>
      }

      @if (canReview() && accessRequests().length) {
        <app-enterprise-section-card [title]="'artistSpace.team.accessRequests' | t:lang()">
          @for (r of accessRequests(); track r.id) {
            <div class="req-row">
              <span>#{{ r.id }} user {{ r.applicant_user_id }} → {{ r.proposed_role }}</span>
              <button type="button" class="btn btn--primary" (click)="approveReq(r)">
                {{ 'common.approve' | t:lang() }}
              </button>
              <button type="button" class="btn btn--secondary" (click)="rejectReq(r)">
                {{ 'common.reject' | t:lang() }}
              </button>
            </div>
          }
        </app-enterprise-section-card>
      }
    </div>
  `,
  styles: [
    `
      .member-list,
      .invite-list,
      .req-row {
        list-style: none;
        padding: 0;
      }
      .member-list li,
      .invite-list li,
      .req-row {
        display: flex;
        gap: 0.75rem;
        align-items: center;
        padding: 0.5rem 0;
        flex-wrap: wrap;
      }
      .token-box {
        margin-top: 1rem;
        word-break: break-all;
      }
    `,
  ],
})
export class ArtistSpaceTeamPage implements OnInit {
  private readonly api = inject(ArtistSpaceApiService);
  private readonly artistCtx = inject(ArtistContextService);
  private readonly i18n = inject(I18nService);
  private readonly fb = inject(FormBuilder);

  readonly lang = this.i18n.lang;
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly members = signal<Record<string, unknown>[]>([]);
  readonly accessRequests = signal<ArtistAccessRequest[]>([]);
  readonly pendingInvites = signal<ArtistInvitation[]>([]);
  readonly inviteToken = signal<string | null>(null);
  readonly tokenHint = signal('');

  readonly inviteForm = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    role: ['member', Validators.required],
  });

  canInvite(): boolean {
    return this.artistCtx.can('artist_space.invite');
  }
  canManage(): boolean {
    return this.artistCtx.can('artist_space.team.manage');
  }
  canReview(): boolean {
    return this.artistCtx.can('artist_space.access.review');
  }

  ngOnInit(): void {
    this.load();
  }

  memberId(m: Record<string, unknown>): number {
    return Number(m['id'] ?? 0);
  }
  memberRole(m: Record<string, unknown>): string {
    return String(m['role'] ?? '');
  }
  memberLabel(m: Record<string, unknown>): string {
    return String(m['email'] || m['display_name'] || m['user_id'] || '—');
  }

  load(): void {
    const id = this.artistCtx.artistProfileId();
    if (id == null) return;
    this.loading.set(true);
    this.api.team(id).subscribe({
      next: (rows) => {
        this.members.set((rows || []) as Record<string, unknown>[]);
        this.loading.set(false);
      },
      error: (e) => {
        this.error.set(e?.message || 'load_failed');
        this.loading.set(false);
      },
    });
    if (this.canInvite()) {
      this.loadPendingInvites(id);
    }
    if (this.canReview()) {
      this.api.listAccessRequests(id).subscribe({
        next: (rows) => this.accessRequests.set(rows || []),
        error: () => undefined,
      });
    }
  }

  private loadPendingInvites(artistProfileId: number): void {
    this.api.listInvitations(artistProfileId, 'pending').subscribe({
      next: (rows) => this.pendingInvites.set(rows || []),
      error: () => undefined,
    });
  }

  invite(): void {
    const id = this.artistCtx.artistProfileId();
    if (id == null || !this.canInvite()) return;
    const v = this.inviteForm.getRawValue();
    this.api.invite(id, v).subscribe({
      next: (r) => {
        this.inviteToken.set(r.invite_token);
        this.tokenHint.set(this.i18n.t('artistSpace.team.tokenHint'));
        this.inviteForm.reset({ email: '', role: 'member' });
        this.loadPendingInvites(id);
      },
      error: (e) => this.error.set(e?.error?.detail?.message || e?.message || 'invite_failed'),
    });
  }

  revokeInvite(inv: ArtistInvitation): void {
    const id = this.artistCtx.artistProfileId();
    if (id == null || !this.canInvite()) return;
    this.api.revokeInvitation(id, inv.id).subscribe({
      next: () => {
        this.inviteToken.set(null);
        this.loadPendingInvites(id);
      },
      error: (e) =>
        this.error.set(e?.error?.detail?.message || e?.message || 'revoke_invite_failed'),
    });
  }

  resendInvite(inv: ArtistInvitation): void {
    const id = this.artistCtx.artistProfileId();
    if (id == null || !this.canInvite()) return;
    this.api.resendInvitation(id, inv.id).subscribe({
      next: (r) => {
        this.inviteToken.set(r.invite_token);
        this.tokenHint.set(this.i18n.t('artistSpace.team.newTokenHint'));
        this.loadPendingInvites(id);
      },
      error: (e) =>
        this.error.set(e?.error?.detail?.message || e?.message || 'resend_invite_failed'),
    });
  }

  revoke(m: Record<string, unknown>): void {
    const id = this.artistCtx.artistProfileId();
    if (id == null) return;
    this.api.revokeMember(id, this.memberId(m)).subscribe({
      next: () => this.load(),
      error: (e) => this.error.set(e?.error?.detail?.message || e?.message || 'revoke_failed'),
    });
  }

  approveReq(r: ArtistAccessRequest): void {
    const id = this.artistCtx.artistProfileId();
    if (id == null) return;
    this.api.approveAccessRequest(id, r.id).subscribe({ next: () => this.load() });
  }

  rejectReq(r: ArtistAccessRequest): void {
    const id = this.artistCtx.artistProfileId();
    if (id == null) return;
    this.api.rejectAccessRequest(id, r.id).subscribe({ next: () => this.load() });
  }
}
