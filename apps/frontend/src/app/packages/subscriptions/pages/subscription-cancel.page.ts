import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { SubscriptionsApiService } from '../services/subscriptions-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { StatusLabelPipe } from '../../../shared/pipes/status-label.pipe';
import { LocaleDatePipe, LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';

@Component({
  selector: 'app-subscription-cancel',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, TranslatePipe, StatusLabelPipe, LocaleMoneyPipe, LocaleDatePipe],
  template: `
    <div class="subscription-cancel">
      <h1>{{ 'subscriptions.cancel.title' | t:lang() }}</h1>

      <p class="warning">
        ¿Estás seguro que deseas cancelar tu suscripción?
      </p>

      <form [formGroup]="form" (ngSubmit)="onSubmit()">
        <div class="form-field">
          <label>Modo</label>
          <select formControlName="mode">
            <option value="period_end">Al final del periodo</option>
            <option value="immediate">Inmediato</option>
          </select>
        </div>

        <div class="form-field">
          <label>Razón (opcional)</label>
          <input formControlName="reason" />
        </div>

        <div class="form-actions">
          <button type="submit" [disabled]="saving" class="btn btn--danger">Confirmar cancelación</button>
          <button type="button" (click)="goBack()" class="btn">Volver</button>
        </div>

        @if (error) {
          <div class="error">{{ error }}</div>
        }
      </form>
    </div>
  `,
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
  saving = false;
  error: string | null = null;

  form = this.fb.group({
    mode: ['period_end', Validators.required],
    reason: [''],
  });

  ngOnInit(): void {
    this.organizationId = this.orgCtx.activeOrganization()?.id ?? null;
    if (!this.organizationId) {
      this.error = this.i18n.t('common.orgRequiredContext');
      return;
    }
    this.subscriptionId = Number(this.route.snapshot.paramMap.get('id'));
  }

  onSubmit(): void {
    const orgId = this.organizationId;
    if (this.form.invalid || orgId == null) return;
    this.saving = true;
    const { mode, reason } = this.form.value;
    this.api.cancelSubscription(orgId, this.subscriptionId, {
      mode: mode!,
      reason: reason ?? undefined,
    }).subscribe({
      next: () => this.router.navigate(['/subscriptions']),
      error: (e) => {
        this.error = e?.error?.detail?.message ?? 'Error al cancelar';
        this.saving = false;
      },
    });
  }

  goBack(): void {
    this.router.navigate(['/subscriptions']);
  }
}
