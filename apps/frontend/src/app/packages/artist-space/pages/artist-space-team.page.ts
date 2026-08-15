import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ArtistContextService } from '../services/artist-context.service';
import { ArtistSpaceApiService } from '../services/artist-space-api.service';
import { artistJourneyError } from '../services/artist-space-error';
import {
  ARTIST_ASSIGNABLE_ROLES,
  ArtistAccessRequest,
  ArtistInvitation,
  ArtistTeamMember,
  artistRelationshipLabelKey,
  artistRequestStatusLabelKey,
  artistRoleLabelKey,
} from '../models/artist-space.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import { ConfirmDialogService } from '../../../shared/services/confirm-dialog.service';
import { SpaceContextService } from '../../../core/spaces/space-context.service';

@Component({
  selector: 'app-artist-space-team',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise artist-space-team-page">
      <app-enterprise-page-header
        [title]="'artistSpace.team.title' | t: lang()"
        [subtitle]="'artistSpace.team.subtitle' | t: lang()"
      />

      @if (feedback()) {
        <p class="ok" role="status" data-testid="team-feedback">{{ feedback() }}</p>
      }
      @if (actionError()) {
        <app-enterprise-error-state [message]="actionError()!" />
      }

      @if (canInvite()) {
        <app-enterprise-section-card
          [title]="'artistSpace.team.invite' | t: lang()"
          [subtitle]="'artistSpace.team.inviteHint' | t: lang()"
        >
          <form [formGroup]="inviteForm" (ngSubmit)="invite()" class="form-grid">
            <app-enterprise-form-field [label]="'common.email' | t: lang()" [required]="true">
              <input class="input" formControlName="email" type="email" data-testid="invite-email" />
            </app-enterprise-form-field>
            <app-enterprise-form-field
              [label]="'artistSpace.team.role' | t: lang()"
              [required]="true"
              [hint]="roleHint(inviteForm.controls.role.value)"
            >
              <select class="input" formControlName="role" data-testid="invite-role">
                @for (role of assignableRoles; track role) {
                  <option [value]="role">{{ roleLabel(role) }}</option>
                }
              </select>
            </app-enterprise-form-field>
            <div class="form-actions">
              <button
                type="submit"
                class="btn btn--primary"
                [disabled]="inviteForm.invalid || busy()"
              >
                {{ 'artistSpace.team.invite' | t: lang() }}
              </button>
            </div>
          </form>
        </app-enterprise-section-card>

        <app-enterprise-section-card [title]="'artistSpace.team.pendingInvites' | t: lang()">
          @if (invitesError()) {
            <app-enterprise-error-state [message]="invitesError()!" (retry)="load()" />
          } @else if (!pendingInvites().length) {
            <p class="muted">{{ 'artistSpace.team.noPendingInvites' | t: lang() }}</p>
          } @else {
            <ul class="row-list" data-testid="pending-invites">
              @for (inv of pendingInvites(); track inv.id) {
                <li>
                  <div class="row-list__main">
                    <strong>{{ inv.email_normalized }}</strong>
                    <span class="muted">{{ roleLabel(inv.role) }}</span>
                    <span class="muted">
                      {{ 'artistSpace.team.expiresAt' | t: lang() }}: {{ inv.expires_at }}
                    </span>
                  </div>
                  <div class="row-list__actions">
                    <button
                      type="button"
                      class="btn btn--secondary"
                      [disabled]="busy()"
                      (click)="resendInvite(inv)"
                    >
                      {{ 'artistSpace.team.resendInvite' | t: lang() }}
                    </button>
                    <button
                      type="button"
                      class="btn btn--secondary"
                      [disabled]="busy()"
                      (click)="revokeInvite(inv)"
                    >
                      {{ 'artistSpace.team.revokeInvite' | t: lang() }}
                    </button>
                  </div>
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
        <app-enterprise-section-card [title]="'artistSpace.team.members' | t: lang()">
          @if (!members().length) {
            <p class="muted">{{ 'artistSpace.team.noMembers' | t: lang() }}</p>
          } @else {
            <ul class="row-list" data-testid="team-members">
              @for (m of members(); track m.id) {
                <li>
                  <div class="row-list__main">
                    <strong>{{ memberLabel(m) }}</strong>
                    <span class="muted" [attr.data-role]="m.role">{{ roleLabel(m.role) }}</span>
                  </div>
                  @if (canManage() && m.role !== 'owner') {
                    <div class="row-list__actions">
                      <label class="inline-field">
                        <span class="sr-only">{{ 'artistSpace.team.changeRole' | t: lang() }}</span>
                        <select
                          class="input"
                          [value]="m.role"
                          [disabled]="busy()"
                          (change)="changeRole(m, $event)"
                        >
                          @for (role of assignableRoles; track role) {
                            <option [value]="role">{{ roleLabel(role) }}</option>
                          }
                        </select>
                      </label>
                      <button
                        type="button"
                        class="btn btn--secondary"
                        [disabled]="busy()"
                        (click)="revokeMember(m)"
                      >
                        {{ 'artistSpace.team.revoke' | t: lang() }}
                      </button>
                    </div>
                  }
                </li>
              }
            </ul>
          }
        </app-enterprise-section-card>
      }

      @if (canReview()) {
        <app-enterprise-section-card [title]="'artistSpace.team.accessRequests' | t: lang()">
          @if (requestsError()) {
            <app-enterprise-error-state [message]="requestsError()!" (retry)="load()" />
          } @else if (!accessRequests().length) {
            <p class="muted">{{ 'artistSpace.team.noAccessRequests' | t: lang() }}</p>
          } @else {
            <ul class="row-list" data-testid="access-requests">
              @for (r of accessRequests(); track r.id) {
                <li>
                  <div class="row-list__main">
                    <strong>{{ requestApplicant(r) }}</strong>
                    <span class="muted">
                      {{ 'artistSpace.team.requestedRole' | t: lang() }}:
                      {{ roleLabel(r.proposed_role) }}
                    </span>
                    @if (r.relationship_type) {
                      <span class="muted">{{ relationshipLabel(r.relationship_type) }}</span>
                    }
                    @if (r.evidence_note) {
                      <span class="muted">{{ r.evidence_note }}</span>
                    }
                    <app-enterprise-status-badge
                      status="pending"
                      [label]="statusLabel(r.status)"
                    />
                  </div>
                  <div class="row-list__actions">
                    <button
                      type="button"
                      class="btn btn--primary"
                      [disabled]="busy()"
                      (click)="approveRequest(r)"
                    >
                      {{ 'common.approve' | t: lang() }}
                    </button>
                    <button
                      type="button"
                      class="btn btn--secondary"
                      [disabled]="busy()"
                      (click)="rejectRequest(r)"
                    >
                      {{ 'common.reject' | t: lang() }}
                    </button>
                  </div>
                </li>
              }
            </ul>
          }
        </app-enterprise-section-card>
      }
    </div>
  `,
  styles: [
    `
      .artist-space-team-page {
        --team-border: var(--vx-border, rgba(255, 255, 255, 0.12));
        --team-muted: var(--vx-text-secondary, rgba(255, 255, 255, 0.6));
      }
      .form-grid {
        display: grid;
        gap: 0.85rem;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 16rem), 1fr));
      }
      .form-actions {
        grid-column: 1 / -1;
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
      }
      .row-list {
        list-style: none;
        margin: 0;
        padding: 0;
      }
      .row-list li {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        align-items: center;
        justify-content: space-between;
        padding: 0.75rem 0;
        border-bottom: 1px solid var(--team-border);
      }
      .row-list li:last-child {
        border-bottom: none;
      }
      .row-list__main {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 0.5rem;
        min-width: 0;
      }
      .row-list__actions {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        align-items: center;
      }
      .inline-field .input {
        min-width: 10rem;
      }
      .muted {
        color: var(--team-muted);
        font-size: 0.85rem;
      }
      .ok {
        color: var(--vx-success, #6fd3a0);
      }
      .sr-only {
        position: absolute;
        width: 1px;
        height: 1px;
        overflow: hidden;
        clip: rect(0 0 0 0);
        white-space: nowrap;
      }
      @media (max-width: 640px) {
        .row-list li {
          flex-direction: column;
          align-items: flex-start;
        }
        .row-list__actions .btn,
        .inline-field .input {
          width: 100%;
        }
      }
    `,
  ],
})
export class ArtistSpaceTeamPage implements OnInit {
  private readonly api = inject(ArtistSpaceApiService);
  private readonly artistCtx = inject(ArtistContextService);
  private readonly i18n = inject(I18nService);
  private readonly fb = inject(FormBuilder);
  private readonly confirmDialog = inject(ConfirmDialogService);
  private readonly spaces = inject(SpaceContextService);

  readonly lang = this.i18n.lang;
  readonly assignableRoles = ARTIST_ASSIGNABLE_ROLES;

  readonly loading = signal(true);
  readonly busy = signal(false);
  readonly error = signal<string | null>(null);
  readonly actionError = signal<string | null>(null);
  readonly invitesError = signal<string | null>(null);
  readonly requestsError = signal<string | null>(null);
  readonly feedback = signal<string | null>(null);
  readonly members = signal<ArtistTeamMember[]>([]);
  readonly accessRequests = signal<ArtistAccessRequest[]>([]);
  readonly pendingInvites = signal<ArtistInvitation[]>([]);

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

  roleLabel(role: string): string {
    return this.i18n.t(artistRoleLabelKey(role));
  }

  roleHint(role: string): string {
    return this.i18n.t(`artistSpace.role.hint.${role}`);
  }

  relationshipLabel(relationship: string): string {
    return this.i18n.t(artistRelationshipLabelKey(relationship));
  }

  statusLabel(status: string): string {
    return this.i18n.t(artistRequestStatusLabelKey(status));
  }

  memberLabel(member: ArtistTeamMember): string {
    return (
      member.email ||
      member.display_name ||
      `${this.i18n.t('artistSpace.team.userFallback')} #${member.user_id}`
    );
  }

  requestApplicant(request: ArtistAccessRequest): string {
    return `${this.i18n.t('artistSpace.team.userFallback')} #${request.applicant_user_id}`;
  }

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    const id = this.artistCtx.artistProfileId();
    if (id == null) {
      this.loading.set(false);
      this.error.set(this.i18n.t('artistSpace.error.noActiveArtist'));
      return;
    }
    this.loading.set(true);
    this.error.set(null);
    this.api.team(id).subscribe({
      next: (rows) => {
        this.members.set(rows ?? []);
        this.loading.set(false);
      },
      error: (e) => {
        this.error.set(artistJourneyError(this.i18n, e));
        this.loading.set(false);
      },
    });

    if (this.canInvite()) {
      this.invitesError.set(null);
      this.api.listInvitations(id, 'pending').subscribe({
        next: (rows) => this.pendingInvites.set(rows ?? []),
        error: (e) => this.invitesError.set(artistJourneyError(this.i18n, e)),
      });
    }

    if (this.canReview()) {
      this.requestsError.set(null);
      this.api.listAccessRequests(id).subscribe({
        next: (rows) => this.accessRequests.set(rows ?? []),
        error: (e) => this.requestsError.set(artistJourneyError(this.i18n, e)),
      });
    }
  }

  invite(): void {
    const id = this.artistCtx.artistProfileId();
    if (id == null || !this.canInvite() || this.inviteForm.invalid) return;
    const v = this.inviteForm.getRawValue();
    this.startAction();
    this.api.invite(id, { email: v.email.trim(), role: v.role }).subscribe({
      next: (result) => {
        this.busy.set(false);
        // Tokens are secrets: only delivery status is ever surfaced.
        this.feedback.set(
          `${this.i18n.t('artistSpace.team.inviteCreated')} (${this.deliveryLabel(
            result.email_delivery_status,
          )})`,
        );
        this.inviteForm.reset({ email: '', role: 'member' });
        this.load();
      },
      error: (e) => this.failAction(e),
    });
  }

  async revokeInvite(invitation: ArtistInvitation): Promise<void> {
    const id = this.artistCtx.artistProfileId();
    if (id == null || !this.canInvite()) return;
    const confirmed = await this.confirmDialog.open({
      title: this.i18n.t('artistSpace.team.revokeInvite'),
      message: `${this.i18n.t('artistSpace.team.confirmRevokeInvite')} ${invitation.email_normalized}`,
      danger: true,
    });
    if (!confirmed) return;
    this.startAction();
    this.api.revokeInvitation(id, invitation.id).subscribe({
      next: () => {
        this.busy.set(false);
        this.feedback.set(this.i18n.t('artistSpace.team.inviteRevoked'));
        this.load();
      },
      error: (e) => this.failAction(e),
    });
  }

  resendInvite(invitation: ArtistInvitation): void {
    const id = this.artistCtx.artistProfileId();
    if (id == null || !this.canInvite()) return;
    this.startAction();
    this.api.resendInvitation(id, invitation.id).subscribe({
      next: (result) => {
        this.busy.set(false);
        this.feedback.set(
          `${this.i18n.t('artistSpace.team.inviteResent')} (${this.deliveryLabel(
            result.email_delivery_status,
          )})`,
        );
        this.load();
      },
      error: (e) => this.failAction(e),
    });
  }

  async revokeMember(member: ArtistTeamMember): Promise<void> {
    const id = this.artistCtx.artistProfileId();
    if (id == null || !this.canManage()) return;
    const confirmed = await this.confirmDialog.open({
      title: this.i18n.t('artistSpace.team.revoke'),
      message: `${this.i18n.t('artistSpace.team.confirmRevokeMember')} ${this.memberLabel(member)}`,
      danger: true,
    });
    if (!confirmed) return;
    this.startAction();
    this.api.revokeMember(id, member.id).subscribe({
      next: () => {
        this.busy.set(false);
        this.feedback.set(this.i18n.t('artistSpace.team.memberRevoked'));
        this.refreshAfterMembershipChange();
      },
      error: (e) => this.failAction(e),
    });
  }

  async changeRole(member: ArtistTeamMember, event: Event): Promise<void> {
    const id = this.artistCtx.artistProfileId();
    const select = event.target as HTMLSelectElement;
    const nextRole = select.value;
    if (id == null || !this.canManage() || !nextRole || nextRole === member.role) return;
    const confirmed = await this.confirmDialog.open({
      title: this.i18n.t('artistSpace.team.changeRole'),
      message: `${this.memberLabel(member)}: ${this.roleLabel(member.role)} → ${this.roleLabel(
        nextRole,
      )}`,
    });
    if (!confirmed) {
      select.value = String(member.role);
      return;
    }
    this.startAction();
    this.api.changeRole(id, member.id, nextRole).subscribe({
      next: () => {
        this.busy.set(false);
        this.feedback.set(this.i18n.t('artistSpace.team.roleChanged'));
        this.refreshAfterMembershipChange();
      },
      error: (e) => {
        select.value = String(member.role);
        this.failAction(e);
      },
    });
  }

  async approveRequest(request: ArtistAccessRequest): Promise<void> {
    const id = this.artistCtx.artistProfileId();
    if (id == null || !this.canReview()) return;
    const confirmed = await this.confirmDialog.open({
      title: this.i18n.t('common.approve'),
      message: `${this.i18n.t('artistSpace.team.confirmApprove')} ${this.requestApplicant(request)}`,
    });
    if (!confirmed) return;
    this.startAction();
    this.api.approveAccessRequest(id, request.id).subscribe({
      next: () => {
        this.busy.set(false);
        this.feedback.set(this.i18n.t('artistSpace.team.requestApproved'));
        this.refreshAfterMembershipChange();
      },
      error: (e) => this.failAction(e),
    });
  }

  async rejectRequest(request: ArtistAccessRequest): Promise<void> {
    const id = this.artistCtx.artistProfileId();
    if (id == null || !this.canReview()) return;
    const confirmed = await this.confirmDialog.open({
      title: this.i18n.t('common.reject'),
      message: `${this.i18n.t('artistSpace.team.confirmReject')} ${this.requestApplicant(request)}`,
      danger: true,
    });
    if (!confirmed) return;
    this.startAction();
    this.api.rejectAccessRequest(id, request.id).subscribe({
      next: () => {
        this.busy.set(false);
        this.feedback.set(this.i18n.t('artistSpace.team.requestRejected'));
        this.load();
      },
      error: (e) => this.failAction(e),
    });
  }

  private deliveryLabel(status: string): string {
    return this.i18n.t(
      status === 'sent'
        ? 'artistSpace.team.deliverySent'
        : 'artistSpace.team.deliveryPending',
    );
  }

  private startAction(): void {
    this.busy.set(true);
    this.actionError.set(null);
    this.feedback.set(null);
  }

  private failAction(err: unknown): void {
    this.busy.set(false);
    this.actionError.set(artistJourneyError(this.i18n, err));
  }

  /** Membership changed: refresh the session manifest without forcing a logout. */
  private refreshAfterMembershipChange(): void {
    this.load();
    void this.spaces.bootstrap({ force: true });
  }
}
