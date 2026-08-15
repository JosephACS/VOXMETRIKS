import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { CatalogPublishingApiService } from '../../catalog-publishing/services/catalog-publishing.api';
import {
  ReleaseSubmission,
  displayReleaseTitle,
  humanReleaseStatus,
  publishingUiBucket,
} from '../../catalog-publishing/models/catalog-publishing.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { userFacingHttpError } from '../../../core/i18n/user-facing-error';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

type QueueFilter = 'all' | 'submitted' | 'in_review' | 'changes_requested' | 'approved';

/** UI filter chips use friendly buckets; the API expects canonical release statuses. */
export function apiStatusForQueueFilter(filter: QueueFilter): string | undefined {
  if (filter === 'all') return undefined;
  if (filter === 'in_review') return 'under_review';
  return filter;
}

@Component({
  selector: 'app-platform-catalog-reviews',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise platform-reviews-page">
      <app-enterprise-page-header
        [title]="'platformReviews.title' | t: lang()"
        [subtitle]="'platformReviews.subtitle' | t: lang()"
      />

      <div class="filters" role="group" [attr.aria-label]="'platformReviews.filters' | t: lang()">
        @for (option of filters; track option) {
          <button
            type="button"
            class="chip"
            [class.chip--active]="filter() === option"
            (click)="setFilter(option)"
          >
            {{ 'platformReviews.filter.' + option | t: lang() }}
          </button>
        }
      </div>

      @if (loading()) {
        <app-enterprise-loading-skeleton [rows]="5" />
      } @else if (error()) {
        <app-enterprise-error-state [message]="error()!" (retry)="load()" />
      } @else if (!rows().length) {
        <app-enterprise-empty-state
          [title]="'platformReviews.empty' | t: lang()"
          [description]="'platformReviews.emptyBody' | t: lang()"
        />
      } @else {
        <ul class="queue">
          @for (row of rows(); track row.id) {
            <li class="queue-item">
              <div class="queue-item__main">
                <a class="queue-item__title" [routerLink]="['/platform-ops/catalog-reviews', row.id]">
                  {{ title(row) }}
                </a>
                <span class="queue-item__meta">
                  #{{ row.id }} · {{ row.release_type }}
                  @if (row.planned_release_date) {
                    · {{ row.planned_release_date }}
                  }
                </span>
              </div>
              <app-enterprise-status-badge
                [status]="badgeStatus(row.status)"
                [label]="statusLabel(row.status)"
              />
            </li>
          }
        </ul>
      }
    </div>
  `,
  styles: `
    .filters {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      margin-bottom: 1rem;
    }
    .chip {
      padding: 0.4rem 0.85rem;
      border-radius: 999px;
      border: 1px solid rgba(255, 255, 255, 0.14);
      background: transparent;
      color: rgba(255, 255, 255, 0.72);
      font-size: 0.85rem;
      cursor: pointer;
    }
    .chip--active {
      background: rgba(111, 211, 160, 0.14);
      border-color: rgba(111, 211, 160, 0.4);
      color: #6fd3a0;
    }
    .queue {
      list-style: none;
      margin: 0;
      padding: 0;
      display: grid;
      gap: 0.5rem;
    }
    .queue-item {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 0.75rem;
      padding: 0.85rem 1rem;
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 10px;
      background: rgba(255, 255, 255, 0.02);
    }
    .queue-item__main {
      display: flex;
      flex-direction: column;
      gap: 0.2rem;
      min-width: 0;
    }
    .queue-item__title {
      color: #fff;
      font-weight: 600;
      text-decoration: none;
      overflow-wrap: anywhere;
    }
    .queue-item__meta {
      font-size: 0.82rem;
      color: rgba(255, 255, 255, 0.55);
    }
    @media (max-width: 560px) {
      .queue-item {
        align-items: flex-start;
        flex-direction: column;
      }
    }
  `,
})
export class PlatformCatalogReviewsPage implements OnInit {
  private readonly api = inject(CatalogPublishingApiService);
  private readonly i18n = inject(I18nService);

  readonly lang = this.i18n.lang;
  readonly filters: readonly QueueFilter[] = [
    'all',
    'submitted',
    'in_review',
    'changes_requested',
    'approved',
  ];

  readonly filter = signal<QueueFilter>('all');
  readonly rows = signal<ReleaseSubmission[]>([]);
  readonly loading = signal(false);
  readonly error = signal<string | null>(null);

  ngOnInit(): void {
    this.load();
  }

  setFilter(value: QueueFilter): void {
    if (this.filter() === value) return;
    this.filter.set(value);
    this.load();
  }

  load(): void {
    const status = apiStatusForQueueFilter(this.filter());
    this.loading.set(true);
    this.error.set(null);
    this.api
      .platformReviewQueue({ status, limit: 100 })
      .subscribe({
        next: (rows) => {
          this.rows.set(rows ?? []);
          this.loading.set(false);
        },
        error: (err) => {
          this.error.set(userFacingHttpError(this.i18n, err));
          this.loading.set(false);
        },
      });
  }

  title(row: ReleaseSubmission): string {
    return displayReleaseTitle(row.title, row.status);
  }

  statusLabel(status: string): string {
    return humanReleaseStatus(status);
  }

  badgeStatus(status: string): string {
    const bucket = publishingUiBucket(status);
    if (bucket === 'draft') return 'draft';
    if (bucket === 'published') return 'published';
    if (bucket === 'in_review') return 'pending';
    return status;
  }
}
