import { CommonModule } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import {
  PersonalAccountApiService,
  PersonalSubscription,
} from '../services/personal-account-api.service';

@Component({
  selector: 'app-personal-subscription-page',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  styleUrl: '../personal-account.css',
  template: `
    <div class="vx-enterprise personal-account-page">
      <app-enterprise-page-header
        [title]="'personal.subscription.title' | t:lang()"
        [subtitle]="'personal.subscription.subtitle' | t:lang()"
      >
        <a routerLink="/account/plans" class="btn btn--primary">{{
          'personal.nav.plans' | t:lang()
        }}</a>
      </app-enterprise-page-header>

      @if (loading()) {
        <app-enterprise-loading-skeleton [rows]="3" />
      } @else if (error()) {
        <app-enterprise-error-state [message]="error()!" (retry)="load()" />
      } @else if (sub()) {
        <app-enterprise-section-card [title]="sub()!.plan_name">
          <app-enterprise-status-badge [status]="sub()!.status" />
          <dl class="meta">
            <dt>{{ 'common.status' | t:lang() }}</dt>
            <dd>{{ sub()!.status }}</dd>
            <dt>{{ 'personal.subscription.periodEnd' | t:lang() }}</dt>
            <dd>{{ sub()!.current_period_end || ('common.notAvailable' | t:lang()) }}</dd>
            <dt>{{ 'personal.subscription.ownerType' | t:lang() }}</dt>
            <dd>{{ sub()!.owner_type }}</dd>
          </dl>
          @if (!sub()!.is_free && canManageBilling()) {
            <app-enterprise-action-bar>
              <button type="button" class="btn btn--secondary" [disabled]="busy()" (click)="cancel(true)">
                {{ 'personal.subscription.cancelPeriodEnd' | t:lang() }}
              </button>
              <button type="button" class="btn btn--danger" [disabled]="busy()" (click)="cancel(false)">
                {{ 'personal.subscription.cancelNow' | t:lang() }}
              </button>
            </app-enterprise-action-bar>
          }
        </app-enterprise-section-card>
      }

      @if (success()) {
        <div class="alert alert--ok">{{ success() }}</div>
      }
    </div>
  `,
})
export class PersonalSubscriptionPage implements OnInit {
  private api = inject(PersonalAccountApiService);
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;
  sub = signal<PersonalSubscription | null>(null);
  loading = signal(true);
  busy = signal(false);
  error = signal<string | null>(null);
  success = signal<string | null>(null);

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.api.getSubscription().subscribe({
      next: (s) => {
        this.sub.set(s);
        this.loading.set(false);
      },
      error: () => {
        this.error.set(this.i18n.t('common.loadFailed'));
        this.loading.set(false);
      },
    });
  }

  cancel(atPeriodEnd: boolean): void {
    if (!this.canManageBilling()) return;
    this.busy.set(true);
    this.api.cancel(atPeriodEnd).subscribe({
      next: (s) => {
        this.sub.set(s);
        this.success.set(this.i18n.t('personal.subscription.canceled'));
        this.busy.set(false);
      },
      error: () => {
        this.error.set(this.i18n.t('common.actionFailed'));
        this.busy.set(false);
      },
    });
  }

  canManageBilling(): boolean {
    const sub = this.sub();
    return !!sub && sub.can_manage_billing !== false && sub.household_role !== 'member';
  }
}
