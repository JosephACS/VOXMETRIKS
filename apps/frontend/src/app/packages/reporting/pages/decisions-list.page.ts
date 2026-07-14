import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { ReportingApiService } from '../services/reporting-api.service';
import { BusinessDecision } from '../models/reporting.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-decisions-list',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterLink,
    TranslatePipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  template: `
    <div class="vx-enterprise decisions-list-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <app-enterprise-page-header
          [title]="'decisions.list.title' | t:lang()"
          [subtitle]="'decisions.list.subtitle' | t:lang()"
        >
          <a routerLink="/reports" class="btn btn--secondary">
            {{ 'reporting.list.title' | t:lang() }}
          </a>
        </app-enterprise-page-header>

        <app-enterprise-section-card [title]="'decisions.list.record' | t:lang()">
          <form class="form-grid" (ngSubmit)="create()">
            <app-enterprise-form-field
              [label]="'decisions.list.decisionTitle' | t:lang()"
              [required]="true"
            >
              <input [(ngModel)]="title" name="title" class="input" />
            </app-enterprise-form-field>
            <app-enterprise-form-field
              [label]="'decisions.list.proposal' | t:lang()"
              [required]="true"
            >
              <input [(ngModel)]="proposal" name="proposal" class="input" />
            </app-enterprise-form-field>
            <div class="form-grid__actions">
              <button type="submit" class="btn btn--primary" [disabled]="busy">
                {{ 'decisions.list.record' | t:lang() }}
              </button>
            </div>
          </form>
        </app-enterprise-section-card>

        @if (loading) {
          <app-enterprise-loading-skeleton [rows]="3" />
        } @else if (error) {
          <app-enterprise-error-state [message]="error" (retry)="reload()" />
        } @else if (!items.length) {
          <app-enterprise-empty-state
            [title]="'decisions.list.emptyTitle' | t:lang()"
            [description]="'decisions.list.emptyBody' | t:lang()"
            [ctaLabel]="'decisions.list.record' | t:lang()"
          />
        } @else {
          <app-enterprise-data-table>
            <table class="data-table">
              <thead>
                <tr>
                  <th>{{ 'decisions.list.decisionTitle' | t:lang() }}</th>
                  <th>{{ 'common.status' | t:lang() }}</th>
                  <th>{{ 'common.actions' | t:lang() }}</th>
                </tr>
              </thead>
              <tbody>
                @for (d of items; track d.id) {
                  <tr>
                    <td>
                      <a [routerLink]="['/business-decisions', d.id]">{{ d.title }}</a>
                    </td>
                    <td><app-enterprise-status-badge [status]="d.status" /></td>
                    <td>
                      <a
                        [routerLink]="['/business-decisions', d.id]"
                        class="btn btn--ghost btn--sm"
                      >
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
export class DecisionsListPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(ReportingApiService);
  private orgCtx = inject(OrganizationContextService);

  orgId: number | null = null;
  items: BusinessDecision[] = [];
  title = '';
  proposal = '';
  loading = false;
  busy = false;
  error = '';

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    if (this.orgId) this.reload();
  }

  reload(): void {
    if (!this.orgId) return;
    this.loading = true;
    this.api.listDecisions(this.orgId).subscribe({
      next: (p) => {
        this.items = p.items || [];
        this.loading = false;
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || this.i18n.t('common.loadFailed');
        this.loading = false;
      },
    });
  }

  create(): void {
    if (!this.orgId || !this.title || !this.proposal) return;
    this.busy = true;
    this.api.createDecision(this.orgId, { title: this.title, proposal: this.proposal }).subscribe({
      next: () => {
        this.busy = false;
        this.title = '';
        this.proposal = '';
        this.reload();
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || this.i18n.t('common.createFailed');
        this.busy = false;
      },
    });
  }
}
