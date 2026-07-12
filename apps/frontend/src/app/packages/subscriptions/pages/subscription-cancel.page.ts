import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { SubscriptionsApiService } from '../services/subscriptions-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';

@Component({
  selector: 'app-subscription-cancel',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  template: `
    <div class="subscription-cancel">
      <h1 i18n="subscriptions.cancel.title">Cancelar Suscripción</h1>

      <p class="warning" i18n="subscriptions.cancel.warning">
        ¿Estás seguro que deseas cancelar tu suscripción?
      </p>

      <form [formGroup]="form" (ngSubmit)="onSubmit()">
        <div class="form-field">
          <label i18n="subscriptions.cancel.mode">Modo</label>
          <select formControlName="mode">
            <option value="period_end" i18n="subscriptions.cancel.periodEnd">Al final del periodo</option>
            <option value="immediate" i18n="subscriptions.cancel.immediate">Inmediato</option>
          </select>
        </div>

        <div class="form-field">
          <label i18n="subscriptions.cancel.reason">Razón (opcional)</label>
          <input formControlName="reason" />
        </div>

        <div class="form-actions">
          <button type="submit" [disabled]="saving" class="btn btn--danger"
                  i18n="subscriptions.cancel.confirm">Confirmar cancelación</button>
          <button type="button" (click)="goBack()" class="btn"
                  i18n="common.cancel">Volver</button>
        </div>

        @if (error) {
          <div class="error">{{ error }}</div>
        }
      </form>
    </div>
  `,
})
export class SubscriptionCancelPageComponent implements OnInit {
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
      this.error = 'Select an organization context.';
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
