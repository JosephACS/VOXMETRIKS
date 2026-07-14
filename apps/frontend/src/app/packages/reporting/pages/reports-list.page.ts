import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ReportingApiService } from '../services/reporting-api.service';
import { ExecutiveReport, ReportDefinition } from '../models/reporting.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-reports-list',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink,
    TranslatePipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  template: `
    <div class="vx-enterprise reports-list-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <app-enterprise-page-header
          [title]="'reporting.list.title' | t:lang()"
          [subtitle]="'reporting.list.subtitle' | t:lang()"
        >
          <a routerLink="/business-decisions" class="btn btn--secondary">
            {{ 'decisions.list.title' | t:lang() }}
          </a>
        </app-enterprise-page-header>

        <app-enterprise-section-card [title]="'reporting.list.newDefinition' | t:lang()">
          <form class="form-grid" (ngSubmit)="createAndGenerate()">
            <app-enterprise-form-field [label]="'reporting.list.code' | t:lang()" [required]="true">
              <input [(ngModel)]="code" name="code" class="input" />
            </app-enterprise-form-field>
            <app-enterprise-form-field
              [label]="'reporting.list.reportTitle' | t:lang()"
              [required]="true"
            >
              <input [(ngModel)]="title" name="title" class="input" />
            </app-enterprise-form-field>
            <div class="form-grid__actions">
              <button type="submit" class="btn btn--primary" [disabled]="busy">
                {{ 'reporting.list.create' | t:lang() }}
              </button>
            </div>
          </form>
        </app-enterprise-section-card>

        @if (loading) {
          <app-enterprise-loading-skeleton [rows]="3" />
        } @else if (error) {
          <app-enterprise-error-state [message]="error" (retry)="reload()" />
        } @else if (!reports.length) {
          <app-enterprise-empty-state
            [title]="'reporting.list.emptyTitle' | t:lang()"
            [description]="'reporting.list.emptyBody' | t:lang()"
            [ctaLabel]="'reporting.list.create' | t:lang()"
          />
        } @else {
          <app-enterprise-data-table>
            <table class="data-table">
              <thead>
                <tr>
                  <th>{{ 'reporting.list.reportTitle' | t:lang() }}</th>
                  <th>{{ 'common.status' | t:lang() }}</th>
                  <th>{{ 'common.actions' | t:lang() }}</th>
                </tr>
              </thead>
              <tbody>
                @for (r of reports; track r.id) {
                  <tr>
                    <td>
                      <a [routerLink]="['/reports', r.id]">{{ r.title }}</a>
                    </td>
                    <td><app-enterprise-status-badge [status]="r.status" /></td>
                    <td>
                      <a [routerLink]="['/reports', r.id]" class="btn btn--ghost btn--sm">
                        {{ 'common.view' | t:lang() }}
                      </a>
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </app-enterprise-data-table>
        }
      }
    </div>
  `,
})
export class ReportsListPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(ReportingApiService);
  private orgCtx = inject(OrganizationContextService);

  orgId: number | null = null;
  reports: ExecutiveReport[] = [];
  definitions: ReportDefinition[] = [];
  code = 'monthly-exec';
  title = 'Monthly Executive';
  loading = false;
  busy = false;
  error = '';

  ngOnInit(): void {
    const org = this.orgCtx.activeOrganization();
    this.orgId = org?.id ?? null;
    if (this.orgId) this.reload();
  }

  reload(): void {
    if (!this.orgId) return;
    this.loading = true;
    this.error = '';
    this.api.listExecutive(this.orgId).subscribe({
      next: (p) => {
        this.reports = p.items || [];
        this.loading = false;
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || e?.message || this.i18n.t('common.loadFailed');
        this.loading = false;
      },
    });
  }

  createAndGenerate(): void {
    if (!this.orgId || !this.code || !this.title) return;
    this.busy = true;
    this.api.createDefinition(this.orgId, { code: this.code, title: this.title }).subscribe({
      next: (d) => {
        this.api.requestGeneration(this.orgId!, d.id).subscribe({
          next: (g) => {
            this.api.generate(this.orgId!, g.id).subscribe({
              next: () => {
                this.busy = false;
                this.reload();
              },
              error: (e) => {
                this.error = e?.error?.detail?.message || 'Generate failed';
                this.busy = false;
              },
            });
          },
          error: (e) => {
            this.error = e?.error?.detail?.message || 'Request failed';
            this.busy = false;
          },
        });
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || this.i18n.t('common.createFailed');
        this.busy = false;
      },
    });
  }
}
