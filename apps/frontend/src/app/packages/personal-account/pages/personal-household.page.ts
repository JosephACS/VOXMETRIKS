import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import {
  HouseholdInvitation,
  HouseholdMemberCard,
  HouseholdSummary,
  PersonalAccountApiService,
} from '../services/personal-account-api.service';

@Component({
  selector: 'app-personal-household-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  styleUrl: '../personal-account.css',
  template: `
    <div class="vx-enterprise personal-account-page">
      <app-enterprise-page-header
        [title]="'personal.household.title' | t:lang()"
        [subtitle]="'personal.household.subtitle' | t:lang()"
      >
        <a routerLink="/account/plans" class="btn btn--secondary">{{
          'personal.nav.plans' | t:lang()
        }}</a>
        @if (household()?.my_role === 'owner') {
          <a routerLink="/account/billing" class="btn btn--secondary">{{
            'personal.nav.billing' | t:lang()
          }}</a>
        }
      </app-enterprise-page-header>

      @if (loading()) {
        <app-enterprise-loading-skeleton [rows]="4" />
      } @else if (error()) {
        <app-enterprise-error-state [message]="error()!" (retry)="load()" />
      } @else if (!household()) {
        <app-enterprise-empty-state
          [title]="'personal.household.emptyTitle' | t:lang()"
          [description]="'personal.household.emptyBody' | t:lang()"
          [ctaLabel]="'personal.nav.plans' | t:lang()"
          ctaLink="/account/plans"
        />
        <div class="accept-invite-box glass-panel">
          <h3>{{ 'personal.household.acceptTitle' | t:lang() }}</h3>
          <p class="muted">{{ 'personal.household.acceptHint' | t:lang() }}</p>
          <div class="form-grid">
            <app-enterprise-form-field [label]="'personal.household.token' | t:lang()">
              <input class="input" [(ngModel)]="acceptToken" name="acceptToken" autocomplete="off" />
            </app-enterprise-form-field>
            <div class="form-grid__actions">
              <button type="button" class="btn btn--primary" [disabled]="busy()" (click)="accept()">
                {{ 'personal.household.accept' | t:lang() }}
              </button>
              <button type="button" class="btn btn--secondary" [disabled]="busy()" (click)="reject()">
                {{ 'personal.household.reject' | t:lang() }}
              </button>
            </div>
          </div>
        </div>
      } @else {
        <section class="household-summary glass-panel">
          <div class="household-summary__main">
            <h2>{{ household()!.plan_name }}</h2>
            <p class="muted">
              {{ household()!.seats_used }}
              {{ 'personal.household.of' | t:lang() }}
              {{ household()!.max_members }}
              {{ 'personal.household.membersLabel' | t:lang() }}
            </p>
          </div>
          <dl class="household-summary__meta">
            <div>
              <dt>{{ 'personal.household.owner' | t:lang() }}</dt>
              <dd>{{ household()!.owner_display_name }}</dd>
            </div>
            <div>
              <dt>{{ 'personal.household.renewal' | t:lang() }}</dt>
              <dd>
                {{
                  formatDate(household()!.current_period_end) ||
                    ('common.notAvailable' | t:lang())
                }}
              </dd>
            </div>
            <div>
              <dt>{{ 'common.status' | t:lang() }}</dt>
              <dd><app-enterprise-status-badge [status]="household()!.status" /></dd>
            </div>
            <div>
              <dt>{{ 'personal.household.seatsAvailable' | t:lang() }}</dt>
              <dd>{{ household()!.seats_available }}</dd>
            </div>
          </dl>
        </section>

        <app-enterprise-section-card [title]="'personal.household.membersTitle' | t:lang()">
          <app-enterprise-data-table>
            <table class="data-table">
              <thead>
                <tr>
                  <th>{{ 'personal.household.col.profile' | t:lang() }}</th>
                  <th>{{ 'common.name' | t:lang() }}</th>
                  <th>{{ 'common.role' | t:lang() }}</th>
                  <th>{{ 'common.status' | t:lang() }}</th>
                  <th>{{ 'personal.household.col.joined' | t:lang() }}</th>
                  <th>{{ 'common.actions' | t:lang() }}</th>
                </tr>
              </thead>
              <tbody>
                @for (m of members(); track m.user_id) {
                  <tr>
                    <td>
                      <span
                        class="profile-avatar profile-avatar--sm"
                        [style.background]="'hsl(' + m.avatar_hue + ' 55% 38%)'"
                        >{{ m.initials }}</span
                      >
                    </td>
                    <td>
                      {{ m.display_name }}
                      @if (m.is_me) {
                        <span class="badge badge--soft">{{ 'personal.household.you' | t:lang() }}</span>
                      }
                    </td>
                    <td>{{ roleLabel(m.role) }}</td>
                    <td><app-enterprise-status-badge [status]="m.status" /></td>
                    <td>{{ formatDate(m.joined_at) || ('common.notAvailable' | t:lang()) }}</td>
                    <td>
                      @if (household()!.my_role === 'owner' && m.role === 'member') {
                        <button
                          type="button"
                          class="btn btn--sm btn--danger"
                          [disabled]="busy()"
                          (click)="remove(m.user_id)"
                        >
                          {{ 'personal.household.remove' | t:lang() }}
                        </button>
                      }
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </app-enterprise-data-table>
        </app-enterprise-section-card>

        @if (household()!.my_role === 'owner') {
          <app-enterprise-section-card [title]="'personal.household.pendingTitle' | t:lang()">
            @if (!invitations().length) {
              <p class="muted">{{ 'personal.household.pendingEmpty' | t:lang() }}</p>
            } @else {
              <app-enterprise-data-table>
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>{{ 'common.name' | t:lang() }}</th>
                      <th>{{ 'common.email' | t:lang() }}</th>
                      <th>{{ 'personal.household.col.sent' | t:lang() }}</th>
                      <th>{{ 'personal.household.col.expires' | t:lang() }}</th>
                      <th>{{ 'common.actions' | t:lang() }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    @for (inv of invitations(); track inv.id) {
                      <tr>
                        <td>{{ inv.display_name || inv.email.split('@')[0] }}</td>
                        <td>{{ inv.email }}</td>
                        <td>{{ formatDate(inv.created_at) }}</td>
                        <td>{{ formatDate(inv.expires_at) }}</td>
                        <td class="actions-inline">
                          <button
                            type="button"
                            class="btn btn--sm btn--secondary"
                            [disabled]="busy()"
                            (click)="resend(inv.id)"
                          >
                            {{ 'personal.household.resend' | t:lang() }}
                          </button>
                          <button
                            type="button"
                            class="btn btn--sm btn--danger"
                            [disabled]="busy()"
                            (click)="cancelInvite(inv.id)"
                          >
                            {{ 'personal.household.cancelInvite' | t:lang() }}
                          </button>
                        </td>
                      </tr>
                    }
                  </tbody>
                </table>
              </app-enterprise-data-table>
            }

            <div class="form-grid invite-form">
              <app-enterprise-form-field [label]="'common.name' | t:lang()">
                <input class="input" [(ngModel)]="inviteName" name="inviteName" autocomplete="name" />
              </app-enterprise-form-field>
              <app-enterprise-form-field [label]="'common.email' | t:lang()">
                <input
                  class="input"
                  [(ngModel)]="inviteEmail"
                  name="inviteEmail"
                  type="email"
                  autocomplete="email"
                />
              </app-enterprise-form-field>
              <div class="form-grid__actions">
                <button
                  type="button"
                  class="btn btn--primary"
                  [disabled]="busy() || household()!.seats_available <= 0"
                  (click)="invite()"
                >
                  {{ 'personal.household.invite' | t:lang() }}
                </button>
              </div>
            </div>
            @if (household()!.seats_available <= 0) {
              <p class="muted">{{ 'personal.household.full' | t:lang() }}</p>
            }
          </app-enterprise-section-card>
        }

        <app-enterprise-section-card [title]="'personal.household.actionsTitle' | t:lang()">
          <app-enterprise-action-bar>
            <a routerLink="/account/profiles" class="btn btn--secondary">{{
              'personal.profiles.change' | t:lang()
            }}</a>
            @if (household()!.my_role === 'owner') {
              <a routerLink="/account/plans" class="btn btn--secondary">{{
                'personal.household.managePlan' | t:lang()
              }}</a>
            } @else {
              <button type="button" class="btn btn--danger" [disabled]="busy()" (click)="leave()">
                {{ 'personal.household.leave' | t:lang() }}
              </button>
            }
          </app-enterprise-action-bar>
        </app-enterprise-section-card>
      }

      @if (success()) {
        <div class="alert alert--ok">{{ success() }}</div>
      }
    </div>
  `,
})
export class PersonalHouseholdPage implements OnInit {
  private api = inject(PersonalAccountApiService);
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;
  household = signal<HouseholdSummary | null>(null);
  members = signal<HouseholdMemberCard[]>([]);
  invitations = signal<HouseholdInvitation[]>([]);
  loading = signal(true);
  busy = signal(false);
  error = signal<string | null>(null);
  success = signal<string | null>(null);
  inviteEmail = '';
  inviteName = '';
  acceptToken = '';

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.error.set(null);
    this.api.getHousehold().subscribe({
      next: (h) => {
        if (!h || (h as { household?: null }).household === null || !(h as HouseholdSummary).id) {
          this.household.set(null);
          this.members.set([]);
          this.invitations.set([]);
        } else {
          const summary = h as HouseholdSummary;
          this.household.set(summary);
          this.members.set(summary.members || []);
          this.invitations.set(summary.pending_invitations || []);
        }
        this.loading.set(false);
      },
      error: () => {
        this.error.set(this.i18n.t('common.loadFailed'));
        this.loading.set(false);
      },
    });
  }

  roleLabel(role: string): string {
    return role === 'owner'
      ? this.i18n.t('personal.household.role.owner')
      : this.i18n.t('personal.household.role.member');
  }

  formatDate(value?: string | null): string {
    if (!value) return '';
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return value;
    return d.toLocaleDateString(this.lang() === 'en' ? 'en-US' : 'es-ES', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    });
  }

  invite(): void {
    if (!this.inviteEmail.trim()) return;
    this.busy.set(true);
    this.error.set(null);
    this.api.invite(this.inviteEmail.trim(), this.inviteName.trim() || undefined).subscribe({
      next: () => {
        this.success.set(this.i18n.t('personal.household.invited'));
        this.inviteEmail = '';
        this.inviteName = '';
        this.busy.set(false);
        this.load();
      },
      error: (e) => {
        this.error.set(e?.error?.detail?.message || this.i18n.t('common.actionFailed'));
        this.busy.set(false);
      },
    });
  }

  resend(id: number): void {
    this.busy.set(true);
    this.api.resendInvite(id).subscribe({
      next: () => {
        this.success.set(this.i18n.t('personal.household.resent'));
        this.busy.set(false);
        this.load();
      },
      error: (e) => {
        this.error.set(e?.error?.detail?.message || this.i18n.t('common.actionFailed'));
        this.busy.set(false);
      },
    });
  }

  cancelInvite(id: number): void {
    this.busy.set(true);
    this.api.cancelInvite(id).subscribe({
      next: () => {
        this.success.set(this.i18n.t('personal.household.inviteCancelled'));
        this.busy.set(false);
        this.load();
      },
      error: (e) => {
        this.error.set(e?.error?.detail?.message || this.i18n.t('common.actionFailed'));
        this.busy.set(false);
      },
    });
  }

  remove(userId: number): void {
    this.busy.set(true);
    this.api.removeMember(userId).subscribe({
      next: () => {
        this.busy.set(false);
        this.load();
      },
      error: (e) => {
        this.error.set(e?.error?.detail?.message || this.i18n.t('common.actionFailed'));
        this.busy.set(false);
      },
    });
  }

  leave(): void {
    this.busy.set(true);
    this.api.leaveHousehold().subscribe({
      next: () => {
        this.busy.set(false);
        this.success.set(this.i18n.t('personal.household.left'));
        this.load();
      },
      error: (e) => {
        this.error.set(e?.error?.detail?.message || this.i18n.t('common.actionFailed'));
        this.busy.set(false);
      },
    });
  }

  accept(): void {
    if (!this.acceptToken.trim()) return;
    this.busy.set(true);
    this.api.acceptInvite(this.acceptToken.trim()).subscribe({
      next: () => {
        this.acceptToken = '';
        this.success.set(this.i18n.t('personal.household.accepted'));
        this.busy.set(false);
        this.load();
      },
      error: (e) => {
        this.error.set(e?.error?.detail?.message || this.i18n.t('common.actionFailed'));
        this.busy.set(false);
      },
    });
  }

  reject(): void {
    if (!this.acceptToken.trim()) return;
    this.busy.set(true);
    this.api.rejectInvite(this.acceptToken.trim()).subscribe({
      next: () => {
        this.acceptToken = '';
        this.success.set(this.i18n.t('personal.household.rejected'));
        this.busy.set(false);
      },
      error: (e) => {
        this.error.set(e?.error?.detail?.message || this.i18n.t('common.actionFailed'));
        this.busy.set(false);
      },
    });
  }
}
