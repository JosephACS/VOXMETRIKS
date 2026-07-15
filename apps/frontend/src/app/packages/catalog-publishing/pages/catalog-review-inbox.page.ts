import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { catchError, of } from 'rxjs';
import { CatalogPublishingApiService } from '../services/catalog-publishing.api';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import {
  ReleaseSubmission,
  publishingPrimaryLabelKey,
  publishingUiBucket,
} from '../models/catalog-publishing.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import { catalogPublishingAccess } from '../catalog-publishing-access';

@Component({
  selector: 'app-catalog-review-inbox',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise catalog-review-inbox-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else if (!canReview) {
        <app-enterprise-empty-state
          [title]="'publishing.review.forbidden' | t:lang()"
          [description]="'publishing.review.forbiddenBody' | t:lang()"
        />
      } @else {
        <app-enterprise-page-header
          [title]="'publishing.review.inboxTitle' | t:lang()"
          [subtitle]="'publishing.review.inboxSubtitle' | t:lang()"
        />

        <div class="filters">
          <label>
            {{ 'common.status' | t:lang() }}
            <select [(ngModel)]="statusFilter" (ngModelChange)="applyFilter()" class="input">
              <option value="all">{{ 'publishing.review.filterAll' | t:lang() }}</option>
              <option value="draft">{{ 'publishing.status.draft' | t:lang() }}</option>
              <option value="in_review">{{ 'publishing.status.inReview' | t:lang() }}</option>
              <option value="published">{{ 'publishing.status.published' | t:lang() }}</option>
            </select>
          </label>
        </div>

        @if (loading) {
          <app-enterprise-loading-skeleton [rows]="5" />
        } @else if (error) {
          <app-enterprise-error-state [message]="error" (retry)="load()" />
        } @else if (!filtered.length) {
          <app-enterprise-empty-state
            [title]="'publishing.review.empty' | t:lang()"
            [description]="'publishing.review.emptyBody' | t:lang()"
          />
        } @else {
          <app-enterprise-data-table>
            <table class="data-table">
              <thead>
                <tr>
                  <th>{{ 'publishing.field.title' | t:lang() }}</th>
                  <th>{{ 'publishing.field.releaseType' | t:lang() }}</th>
                  <th>{{ 'common.status' | t:lang() }}</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                @for (r of filtered; track r.id) {
                  <tr>
                    <td>{{ r.title }}</td>
                    <td>{{ r.release_type }}</td>
                    <td>
                      <app-enterprise-status-badge
                        [status]="badgeStatus(r.status)"
                        [label]="statusLabel(r.status)"
                      />
                    </td>
                    <td>
                      <a [routerLink]="['/catalog-review', r.id]" class="btn btn--secondary btn--sm">
                        {{ 'publishing.review.open' | t:lang() }}
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
  styles: `
    .filters {
      margin-bottom: 1rem;
      display: flex;
      gap: 1rem;
      flex-wrap: wrap;
    }
    .filters label {
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
      font-size: 0.85rem;
      color: rgba(255, 255, 255, 0.65);
    }
    .filters .input { min-width: 12rem; }
  `,
})
export class CatalogReviewInboxPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;
  private api = inject(CatalogPublishingApiService);
  private orgCtx = inject(OrganizationContextService);
  private access = catalogPublishingAccess();

  orgId: number | null = null;
  canReview = false;
  rows: ReleaseSubmission[] = [];
  filtered: ReleaseSubmission[] = [];
  statusFilter: 'all' | 'draft' | 'in_review' | 'published' = 'all';
  loading = false;
  error: string | null = null;

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    this.canReview = this.access.canReview();
    if (!this.orgId || !this.canReview) return;
    this.load();
  }

  load(): void {
    if (!this.orgId) return;
    this.loading = true;
    this.error = null;
    this.api
      .reviewQueue(this.orgId)
      .pipe(catchError(() => of([] as ReleaseSubmission[])))
      .subscribe({
        next: (rows) => {
          this.rows = rows ?? [];
          this.applyFilter();
          this.loading = false;
        },
        error: () => {
          this.rows = [];
          this.filtered = [];
          this.loading = false;
        },
      });
  }

  applyFilter(): void {
    if (this.statusFilter === 'all') {
      this.filtered = [...this.rows];
      return;
    }
    this.filtered = this.rows.filter((r) => {
      const b = publishingUiBucket(r.status);
      if (this.statusFilter === 'draft') return b === 'draft';
      if (this.statusFilter === 'published') return b === 'published';
      return b === 'in_review';
    });
  }

  statusLabel(status: string): string {
    return this.i18n.t(publishingPrimaryLabelKey(status));
  }

  badgeStatus(status: string): string {
    const b = publishingUiBucket(status);
    if (b === 'draft') return 'draft';
    if (b === 'published') return 'published';
    if (b === 'in_review') return 'pending';
    return status;
  }
}
