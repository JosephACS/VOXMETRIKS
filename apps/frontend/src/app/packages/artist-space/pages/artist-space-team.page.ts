import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { ArtistContextService } from '../services/artist-context.service';
import { ArtistSpaceApiService } from '../services/artist-space-api.service';
import { ArtistAccessRequest } from '../models/artist-space.models';
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

      @if (canManage()) {
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
              {{ 'artistSpace.team.tokenHint' | t:lang() }}
              <code>{{ inviteToken() }}</code>
            </p>
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
      .req-row {
        list-style: none;
        padding: 0;
      }
      .member-list li,
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
  readonly inviteToken = signal<string | null>(null);

  readonly inviteForm = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    role: ['member', Validators.required],
  });

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
    if (this.canReview()) {
      this.api.listAccessRequests(id).subscribe({
        next: (rows) => this.accessRequests.set(rows || []),
        error: () => undefined,
      });
    }
  }

  invite(): void {
    const id = this.artistCtx.artistProfileId();
    if (id == null || !this.canManage()) return;
    const v = this.inviteForm.getRawValue();
    this.api.invite(id, v).subscribe({
      next: (r) => {
        this.inviteToken.set(r.invite_token);
        this.inviteForm.reset({ email: '', role: 'member' });
      },
      error: (e) => this.error.set(e?.error?.detail?.message || e?.message || 'invite_failed'),
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
