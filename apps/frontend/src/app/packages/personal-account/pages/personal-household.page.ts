import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import { PersonalAccountApiService } from '../services/personal-account-api.service';

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
      </app-enterprise-page-header>

      @if (loading()) {
        <app-enterprise-loading-skeleton [rows]="3" />
      } @else if (error()) {
        <app-enterprise-error-state [message]="error()!" (retry)="load()" />
      } @else if (!household()) {
        <app-enterprise-empty-state
          [title]="'personal.household.emptyTitle' | t:lang()"
          [description]="'personal.household.emptyBody' | t:lang()"
          [ctaLabel]="'personal.nav.plans' | t:lang()"
          ctaLink="/account/plans"
        />
      } @else {
        <app-enterprise-section-card [title]="'personal.household.membersTitle' | t:lang()">
          <p class="muted">
            {{ 'personal.household.seats' | t:lang() }}:
            {{ household()!['seats_used'] }} / {{ household()!['max_members'] }}
          </p>
          <app-enterprise-data-table>
            <table class="data-table">
              <thead>
                <tr>
                  <th>{{ 'common.name' | t:lang() }}</th>
                  <th>{{ 'common.email' | t:lang() }}</th>
                  <th>{{ 'common.role' | t:lang() }}</th>
                  <th>{{ 'common.actions' | t:lang() }}</th>
                </tr>
              </thead>
              <tbody>
                @for (m of members(); track m.user_id) {
                  <tr>
                    <td>{{ m.username || ('common.notAvailable' | t:lang()) }}</td>
                    <td>{{ m.email }}</td>
                    <td>{{ m.role }}</td>
                    <td>
                      @if (household()!['my_role'] === 'owner' && m.role === 'member') {
                        <button type="button" class="btn btn--sm btn--danger" (click)="remove(m.user_id)">
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

        @if (household()!['my_role'] === 'owner') {
          <app-enterprise-section-card [title]="'personal.household.inviteTitle' | t:lang()">
            <div class="form-grid">
              <app-enterprise-form-field [label]="'common.email' | t:lang()">
                <input class="input" [(ngModel)]="inviteEmail" name="inviteEmail" />
              </app-enterprise-form-field>
              <div class="form-grid__actions">
                <button type="button" class="btn btn--primary" [disabled]="busy()" (click)="invite()">
                  {{ 'personal.household.invite' | t:lang() }}
                </button>
              </div>
            </div>
          </app-enterprise-section-card>
        }
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
  household = signal<Record<string, unknown> | null>(null);
  members = signal<Array<{ user_id: number; username?: string; email?: string; role: string }>>([]);
  loading = signal(true);
  busy = signal(false);
  error = signal<string | null>(null);
  success = signal<string | null>(null);
  inviteEmail = '';

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.api.getHousehold().subscribe({
      next: (h) => {
        if (!h || h['household'] === null || !h['id']) {
          this.household.set(null);
          this.members.set([]);
        } else {
          this.household.set(h);
          this.members.set(
            (h['members'] as Array<{
              user_id: number;
              username?: string;
              email?: string;
              role: string;
            }>) || [],
          );
        }
        this.loading.set(false);
      },
      error: () => {
        this.error.set(this.i18n.t('common.loadFailed'));
        this.loading.set(false);
      },
    });
  }

  invite(): void {
    if (!this.inviteEmail.trim()) return;
    this.busy.set(true);
    this.api.invite(this.inviteEmail.trim()).subscribe({
      next: () => {
        this.success.set(this.i18n.t('personal.household.invited'));
        this.inviteEmail = '';
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
      error: () => {
        this.error.set(this.i18n.t('common.actionFailed'));
        this.busy.set(false);
      },
    });
  }
}
