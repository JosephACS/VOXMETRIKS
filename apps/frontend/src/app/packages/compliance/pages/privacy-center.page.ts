import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { ComplianceApiService } from '../services/compliance-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { ConsentRecord, DataRequest } from '../models/compliance.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-privacy-center',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    TranslatePipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  template: `
    <div class="vx-enterprise privacy-center-page">
      <app-enterprise-page-header
        [title]="'compliance.privacy.title' | t:lang()"
        [subtitle]="'compliance.privacy.subtitle' | t:lang()"
      />

      <app-enterprise-section-card [title]="'compliance.privacy.consents' | t:lang()">
        @if (loading) {
          <app-enterprise-loading-skeleton [rows]="2" />
        } @else if (consents.length === 0) {
          <app-enterprise-empty-state
            [title]="'compliance.privacy.emptyTitle' | t:lang()"
            [description]="'compliance.privacy.emptyBody' | t:lang()"
          />
        } @else {
          <app-enterprise-data-table>
            <table class="data-table">
              <thead>
                <tr>
                  <th>{{ 'common.id' | t:lang() }}</th>
                  <th>{{ 'common.status' | t:lang() }}</th>
                </tr>
              </thead>
              <tbody>
                @for (c of consents; track c.id) {
                  <tr>
                    <td>{{ c.id }}</td>
                    <td><app-enterprise-status-badge [status]="c.status" /></td>
                  </tr>
                }
              </tbody>
            </table>
          </app-enterprise-data-table>
        }
      </app-enterprise-section-card>

      <app-enterprise-section-card [title]="'compliance.privacy.submitRequest' | t:lang()">
        <form [formGroup]="dsrForm" (ngSubmit)="submitDsr()" class="form-grid">
          <app-enterprise-form-field
            [label]="'compliance.privacy.requestType' | t:lang()"
            [required]="true"
          >
            <select formControlName="request_type" class="select">
              <option value="access">{{ 'compliance.privacy.type.access' | t:lang() }}</option>
              <option value="export">{{ 'compliance.privacy.type.export' | t:lang() }}</option>
              <option value="correction">{{ 'compliance.privacy.type.correction' | t:lang() }}</option>
              <option value="deletion">{{ 'compliance.privacy.type.deletion' | t:lang() }}</option>
            </select>
          </app-enterprise-form-field>
          <app-enterprise-form-field [label]="'common.reason' | t:lang()">
            <input
              formControlName="reason"
              class="input"
              [placeholder]="'compliance.privacy.reasonPlaceholder' | t:lang()"
            />
          </app-enterprise-form-field>
          <div class="form-grid__actions">
            <button type="submit" class="btn btn--primary" [disabled]="dsrForm.invalid">
              {{ 'common.submit' | t:lang() }}
            </button>
          </div>
        </form>
        @if (dsrSuccess) {
          <div class="alert alert--success" role="status">
            {{ 'compliance.privacy.requestSubmitted' | t:lang() }} (ID: {{ dsrSuccess.id }})
          </div>
        }
      </app-enterprise-section-card>

      @if (error) {
        <app-enterprise-error-state [message]="error" (retry)="load()" />
      }
    </div>
  `,
})
export class PrivacyCenterPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(ComplianceApiService);
  private orgCtx = inject(OrganizationContextService);
  private fb = inject(FormBuilder);

  consents: ConsentRecord[] = [];
  loading = false;
  error: string | null = null;
  dsrSuccess: DataRequest | null = null;

  dsrForm = this.fb.group({ request_type: ['access', Validators.required], reason: [''] });

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    const orgId = this.orgCtx.organizationId();
    this.loading = true;
    this.api.myConsentRecords(orgId ?? undefined).subscribe({
      next: (r) => {
        this.consents = r;
        this.loading = false;
      },
      error: (e) => {
        this.error = e?.error?.message || this.i18n.t('common.loadFailed');
        this.loading = false;
      },
    });
  }

  submitDsr(): void {
    const orgId = this.orgCtx.organizationId();
    if (!orgId || this.dsrForm.invalid) {
      this.error = this.i18n.t('common.orgRequired');
      return;
    }
    const v = this.dsrForm.value;
    this.api.submitDsr(orgId, { request_type: v.request_type!, reason: v.reason || undefined }).subscribe({
      next: (r) => {
        this.dsrSuccess = r;
        this.error = null;
      },
      error: (e) => {
        this.error = e?.error?.message || this.i18n.t('common.actionFailed');
      },
    });
  }
}
