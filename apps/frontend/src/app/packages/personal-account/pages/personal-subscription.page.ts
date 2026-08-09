import { CommonModule } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { StatusLabelPipe } from '../../../shared/pipes/status-label.pipe';
import { LocaleDatePipe } from '../../../shared/pipes/locale-format.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import {
  PersonalAccountApiService,
  PersonalSubscription,
} from '../services/personal-account-api.service';
import { personalOwnerTypeLabelKey } from '../personal-subscription.presentation';

@Component({
  selector: 'app-personal-subscription-page',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    TranslatePipe,
    StatusLabelPipe,
    LocaleDatePipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
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
          <div class="plan-summary">
            <app-enterprise-status-badge [status]="sub()!.status" />
            <dl class="meta plan-meta">
              <div class="plan-meta__row">
                <dt>{{ 'common.status' | t:lang() }}</dt>
                <dd>{{ sub()!.status | statusLabel }}</dd>
              </div>
              <div class="plan-meta__row">
                <dt>{{ 'personal.subscription.periodEnd' | t:lang() }}</dt>
                <dd>
                  @if (sub()!.current_period_end) {
                    {{ sub()!.current_period_end | localeDate }}
                  } @else {
                    {{ 'personal.subscription.periodEndUnset' | t:lang() }}
                  }
                </dd>
              </div>
              <div class="plan-meta__row">
                <dt>{{ 'personal.subscription.ownerType' | t:lang() }}</dt>
                <dd>{{ ownerTypeKey() | t:lang() }}</dd>
              </div>
            </dl>
          </div>
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

  readonly ownerTypeKey = computed(() => personalOwnerTypeLabelKey(this.sub()?.owner_type));

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
