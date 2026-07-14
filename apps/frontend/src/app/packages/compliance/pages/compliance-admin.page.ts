import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ComplianceApiService } from '../services/compliance-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { DataRequest, TermsVersion } from '../models/compliance.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-compliance-admin',
  standalone: true,
  imports: [CommonModule, RouterLink, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise compliance-admin">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <app-enterprise-page-header
          [title]="'compliance.admin.title' | t:lang()"
          [subtitle]="'compliance.admin.subtitle' | t:lang()"
        >
          <a routerLink="/compliance" class="btn btn--secondary">
            {{ 'compliance.privacy.title' | t:lang() }}
          </a>
        </app-enterprise-page-header>

        <app-enterprise-section-card [title]="'compliance.admin.terms' | t:lang()">
          @if (terms.length === 0) {
            <app-enterprise-empty-state
              [title]="'compliance.admin.noTermsTitle' | t:lang()"
              [description]="'compliance.admin.noTerms' | t:lang()"
            />
          } @else {
            <app-enterprise-data-table>
              <table class="data-table">
                <thead>
                  <tr>
                    <th>{{ 'compliance.admin.code' | t:lang() }}</th>
                    <th>{{ 'common.name' | t:lang() }}</th>
                    <th>{{ 'common.status' | t:lang() }}</th>
                  </tr>
                </thead>
                <tbody>
                  @for (t of terms; track t.id) {
                    <tr>
                      <td>{{ t.version_code }}</td>
                      <td>{{ t.title }}</td>
                      <td><app-enterprise-status-badge [status]="t.status" /></td>
                    </tr>
                  }
                </tbody>
              </table>
            </app-enterprise-data-table>
          }
        </app-enterprise-section-card>

        <app-enterprise-section-card [title]="'compliance.admin.dsr' | t:lang()">
          @if (dsr.length === 0) {
            <app-enterprise-empty-state
              [title]="'compliance.admin.noDsrTitle' | t:lang()"
              [description]="'compliance.admin.noDsr' | t:lang()"
            />
          } @else {
            <app-enterprise-data-table>
              <table class="data-table">
                <thead>
                  <tr>
                    <th>{{ 'common.id' | t:lang() }}</th>
                    <th>{{ 'common.type' | t:lang() }}</th>
                    <th>{{ 'common.status' | t:lang() }}</th>
                  </tr>
                </thead>
                <tbody>
                  @for (d of dsr; track d.id) {
                    <tr>
                      <td>{{ d.id }}</td>
                      <td>{{ d.request_type }}</td>
                      <td><app-enterprise-status-badge [status]="d.status" /></td>
                    </tr>
                  }
                </tbody>
              </table>
            </app-enterprise-data-table>
          }
        </app-enterprise-section-card>

        @if (error) {
          <app-enterprise-error-state [message]="error" (retry)="load()" />
        }
      }
    </div>
  `,
})
export class ComplianceAdminPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(ComplianceApiService);
  private orgCtx = inject(OrganizationContextService);

  terms: TermsVersion[] = [];
  dsr: DataRequest[] = [];
  error: string | null = null;
  orgId: number | null = null;

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    if (this.orgId) this.load();
  }

  load(): void {
    const orgId = this.orgId;
    if (!orgId) {
      this.error = this.i18n.t('common.orgRequired');
      return;
    }
    this.error = null;
    this.api.listTerms(orgId).subscribe({
      next: (r) => {
        this.terms = r.items;
      },
      error: (e) => {
        this.error = e?.error?.message || this.i18n.t('common.failed');
      },
    });
    this.api.listDsr(orgId).subscribe({
      next: (r) => {
        this.dsr = r.items;
      },
      error: (e) => {
        this.error = e?.error?.message || this.i18n.t('common.failed');
      },
    });
  }
}
