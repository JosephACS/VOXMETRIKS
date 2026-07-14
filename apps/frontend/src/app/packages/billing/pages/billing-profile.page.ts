import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { BillingApiService } from '../services/billing-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { BillingProfile } from '../models/billing.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-billing-profile',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    TranslatePipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  template: `
    <div class="vx-enterprise billing-profile-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <app-enterprise-page-header
          [title]="'billing.profile.title' | t:lang()"
          [subtitle]="'billing.profile.subtitle' | t:lang()"
        >
          @if (profile) {
            <button type="button" class="btn btn--secondary" (click)="editMode = !editMode">
              {{ 'billing.profile.edit' | t:lang() }}
            </button>
          }
        </app-enterprise-page-header>

        @if (error) {
          <app-enterprise-error-state [message]="error" (retry)="loadProfile()" />
        }

        @if (profile) {
          <app-enterprise-section-card>
            <dl class="meta form-grid">
              <div>
                <dt>{{ 'common.currency' | t:lang() }}</dt>
                <dd>{{ profile.default_currency }}</dd>
              </div>
              <div>
                <dt>{{ 'billing.profile.legalName' | t:lang() }}</dt>
                <dd>{{ profile.legal_name ?? ('common.notAvailable' | t:lang()) }}</dd>
              </div>
              <div>
                <dt>{{ 'billing.profile.taxId' | t:lang() }}</dt>
                <dd>{{ profile.tax_id ?? ('common.notAvailable' | t:lang()) }}</dd>
              </div>
              <div>
                <dt>{{ 'common.email' | t:lang() }}</dt>
                <dd>{{ profile.email ?? ('common.notAvailable' | t:lang()) }}</dd>
              </div>
              <div>
                <dt>{{ 'common.status' | t:lang() }}</dt>
                <dd><app-enterprise-status-badge [status]="profile.status" /></dd>
              </div>
            </dl>
          </app-enterprise-section-card>

          @if (editMode) {
            <app-enterprise-section-card [title]="'billing.profile.edit' | t:lang()">
              <form [formGroup]="editForm" (ngSubmit)="saveProfile()" class="form-grid">
                <app-enterprise-form-field [label]="'billing.profile.legalName' | t:lang()">
                  <input formControlName="legal_name" class="input" />
                </app-enterprise-form-field>
                <app-enterprise-form-field [label]="'billing.profile.taxId' | t:lang()">
                  <input formControlName="tax_id" class="input" />
                </app-enterprise-form-field>
                <app-enterprise-form-field [label]="'billing.profile.address' | t:lang()">
                  <input formControlName="billing_address" class="input" />
                </app-enterprise-form-field>
                <app-enterprise-form-field [label]="'common.email' | t:lang()">
                  <input formControlName="email" class="input" />
                </app-enterprise-form-field>
                <div class="form-grid__actions">
                  <button type="submit" class="btn btn--primary">
                    {{ 'billing.profile.save' | t:lang() }}
                  </button>
                </div>
              </form>
            </app-enterprise-section-card>
          }
        } @else if (!error) {
          <app-enterprise-empty-state
            [title]="'billing.profile.emptyTitle' | t:lang()"
            [description]="'billing.profile.emptyBody' | t:lang()"
          />
          <app-enterprise-section-card [title]="'billing.profile.create' | t:lang()">
            <form [formGroup]="createForm" (ngSubmit)="createProfile()" class="form-grid">
              <app-enterprise-form-field [label]="'common.currency' | t:lang()" [required]="true">
                <input formControlName="default_currency" maxlength="3" class="input" />
              </app-enterprise-form-field>
              <app-enterprise-form-field [label]="'billing.profile.legalName' | t:lang()">
                <input formControlName="legal_name" class="input" />
              </app-enterprise-form-field>
              <app-enterprise-form-field [label]="'common.email' | t:lang()">
                <input formControlName="email" class="input" />
              </app-enterprise-form-field>
              <div class="form-grid__actions">
                <button type="submit" class="btn btn--primary" [disabled]="createForm.invalid">
                  {{ 'billing.profile.create' | t:lang() }}
                </button>
              </div>
            </form>
          </app-enterprise-section-card>
        }
      }
    </div>
  `,
})
export class BillingProfilePage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(BillingApiService);
  private orgCtx = inject(OrganizationContextService);
  private fb = inject(FormBuilder);

  profile: BillingProfile | null = null;
  error: string | null = null;
  editMode = false;
  orgId: number | null = null;

  createForm = this.fb.group({
    default_currency: ['', [Validators.required, Validators.maxLength(3), Validators.minLength(3)]],
    legal_name: [''],
    email: [''],
  });

  editForm = this.fb.group({
    legal_name: [''],
    tax_id: [''],
    billing_address: [''],
    email: [''],
  });

  ngOnInit(): void {
    this.orgId = this.orgCtx.activeOrganization()?.id ?? null;
    if (!this.orgId) return;
    this.loadProfile();
  }

  loadProfile(): void {
    this.api.getProfile(this.orgId!).subscribe({
      next: (p) => (this.profile = p),
      error: (e) => {
        if (e.status === 404) this.profile = null;
        else this.error = e.error?.message ?? 'Error loading profile';
      },
    });
  }

  createProfile(): void {
    if (this.createForm.invalid) return;
    this.api.createProfile(this.orgId!, this.createForm.value as Partial<BillingProfile>).subscribe({
      next: (p) => {
        this.profile = p;
        this.error = null;
      },
      error: (e) => (this.error = e.error?.message ?? 'Error creating profile'),
    });
  }

  saveProfile(): void {
    this.api.updateProfile(this.orgId!, this.editForm.value as Partial<BillingProfile>).subscribe({
      next: (p) => {
        this.profile = p;
        this.editMode = false;
      },
      error: (e) => (this.error = e.error?.message ?? 'Error updating profile'),
    });
  }
}
