import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { SubscriptionsApiService } from '../services/subscriptions-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { Subscription } from '../models/subscriptions.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-subscription-cancel',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    RouterLink,
    TranslatePipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  template: `
    <div class="vx-enterprise subscription-cancel-page">
      @if (!organizationId) {
        <app-enterprise-org-required />
      } @else {
        <app-enterprise-page-header
          [title]="'subscriptions.cancel.title' | t:lang()"
          [subtitle]="'subscriptions.cancel.subtitle' | t:lang()"
        >
          <a routerLink="/subscriptions/overview" class="btn btn--secondary">{{
            'common.back' | t:lang()
          }}</a>
        </app-enterprise-page-header>

        <app-enterprise-section-card [title]="'subscriptions.cancel.confirmTitle' | t:lang()">
          <ul class="cancel-points">
            <li>
              {{ 'subscriptions.cancel.pointEffective' | t:lang() }}:
              <strong>{{ effectiveDateLabel() }}</strong>
            </li>
            <li>{{ 'subscriptions.cancel.pointLose' | t:lang() }}</li>
            <li>{{ 'subscriptions.cancel.pointAccess' | t:lang() }}</li>
          </ul>

          <form [formGroup]="form" (ngSubmit)="onSubmit()" class="form-grid">
            <app-enterprise-form-field
              [label]="'subscriptions.cancel.mode' | t:lang()"
              [required]="true"
            >
              <select formControlName="mode" class="input">
                <option value="period_end">{{ 'subscriptions.cancel.modePeriodEnd' | t:lang() }}</option>
                <option value="immediate">{{ 'subscriptions.cancel.modeImmediate' | t:lang() }}</option>
              </select>
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'subscriptions.cancel.reason' | t:lang()">
              <input formControlName="reason" class="input" />
            </app-enterprise-form-field>
            <div class="form-grid__actions">
              <button type="submit" class="btn btn--danger" [disabled]="saving || form.invalid">
                {{ 'subscriptions.cancel.submit' | t:lang() }}
              </button>
              <a routerLink="/subscriptions/overview" class="btn btn--secondary">{{
                'common.cancel' | t:lang()
              }}</a>
            </div>
          </form>

          @if (error) {
            <app-enterprise-error-state [message]="error" />
          }
        </app-enterprise-section-card>
      }
    </div>
  `,
  styles: [
    `
      .cancel-points {
        margin: 0 0 1.1rem;
        padding-left: 1.15rem;
        color: var(--text-muted);
        line-height: 1.55;
      }
      .cancel-points strong {
        color: var(--text);
      }
    `,
  ],
})
export class SubscriptionCancelPageComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private readonly api = inject(SubscriptionsApiService);
  private readonly orgCtx = inject(OrganizationContextService);
  private readonly fb = inject(FormBuilder);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  organizationId: number | null = null;
  subscriptionId = 0;
  subscription: Subscription | null = null;
  saving = false;
  error: string | null = null;

  form = this.fb.group({
    mode: ['period_end', Validators.required],
    reason: [''],
  });

  ngOnInit(): void {
    this.organizationId = this.orgCtx.activeOrganization()?.id ?? null;
    if (!this.organizationId) return;
    this.subscriptionId = Number(this.route.snapshot.paramMap.get('id'));
    this.api.getSubscription(this.organizationId, this.subscriptionId).subscribe({
      next: (s) => (this.subscription = s),
      error: () => (this.subscription = null),
    });
  }

  effectiveDateLabel(): string {
    const mode = this.form.value.mode;
    if (mode === 'immediate') {
      return this.i18n.t('subscriptions.cancel.effectiveImmediate');
    }
    if (this.subscription?.current_period_end) {
      return this.subscription.current_period_end;
    }
    return this.i18n.t('subscriptions.cancel.effectivePeriodEndUnset');
  }

  onSubmit(): void {
    const orgId = this.organizationId;
    if (this.form.invalid || orgId == null) return;
    this.saving = true;
    this.error = null;
    const v = this.form.getRawValue();
    this.api
      .cancelSubscription(orgId, this.subscriptionId, {
        mode: v.mode!,
        reason: v.reason || undefined,
      })
      .subscribe({
        next: () => {
          this.saving = false;
          void this.router.navigate(['/subscriptions/overview']);
        },
        error: (e) => {
          this.saving = false;
          this.error = e?.error?.detail?.message ?? this.i18n.t('common.actionFailed');
        },
      });
  }
}
