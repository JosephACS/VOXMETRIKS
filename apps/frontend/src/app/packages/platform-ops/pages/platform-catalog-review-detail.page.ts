import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { Observable } from 'rxjs';
import { CatalogPublishingApiService } from '../../catalog-publishing/services/catalog-publishing.api';
import {
  ReleaseDetail,
  displayReleaseTitle,
  hasPrivateMedia,
  humanReleaseStatus,
  publishingUiBucket,
} from '../../catalog-publishing/models/catalog-publishing.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { userFacingHttpError } from '../../../core/i18n/user-facing-error';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-platform-catalog-review-detail',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise platform-review-detail-page">
      <a routerLink="/platform-ops/catalog-reviews" class="back-link">
        {{ 'platformReviews.back' | t: lang() }}
      </a>

      @if (loading()) {
        <app-enterprise-loading-skeleton [rows]="6" />
      } @else if (error() && !detail()) {
        <app-enterprise-error-state [message]="error()!" (retry)="load()" />
      } @else if (!detail()) {
        <app-enterprise-empty-state [title]="'publishing.detail.notFound' | t: lang()" />
      } @else {
        <app-enterprise-page-header [title]="title()">
          <app-enterprise-status-badge
            [status]="badgeStatus(detail()!.submission.status)"
            [label]="statusLabel(detail()!.submission.status)"
          />
        </app-enterprise-page-header>

        <div class="preview-note" role="note">
          {{ 'platformReviews.independentNote' | t: lang() }}
        </div>

        @if (privateBanner()) {
          <div class="private-banner" role="status">
            {{ 'publishing.media.privateBanner' | t: lang() }}
          </div>
        }

        <app-enterprise-section-card [title]="'publishing.detail.tracks' | t: lang()">
          @if (!detail()!.tracks.length) {
            <p class="muted">{{ 'publishing.tracks.empty' | t: lang() }}</p>
          } @else {
            <ul class="track-list">
              @for (t of detail()!.tracks; track t.id) {
                <li>{{ t.track_number }}. {{ t.title }}</li>
              }
            </ul>
          }
        </app-enterprise-section-card>

        @if (alerts().length) {
          <app-enterprise-section-card [title]="'publishing.review.rightsAlerts' | t: lang()">
            <ul class="alerts">
              @for (a of alerts(); track a.id) {
                <li [class]="'alert alert--' + a.severity">
                  <strong>{{ a.severity }}</strong> · {{ a.code }} — {{ a.message }}
                </li>
              }
            </ul>
          </app-enterprise-section-card>
        }

        <app-enterprise-section-card [title]="'publishing.review.actions' | t: lang()">
          <label class="field-label" for="platform-review-notes">
            {{ 'publishing.review.notes' | t: lang() }}
          </label>
          <textarea
            id="platform-review-notes"
            [(ngModel)]="notes"
            class="input textarea"
            rows="3"
          ></textarea>

          <div class="actions">
            <button type="button" class="btn btn--primary" [disabled]="busy()" (click)="approve()">
              {{ 'publishing.review.approve' | t: lang() }}
            </button>
            <button
              type="button"
              class="btn btn--secondary"
              [disabled]="busy()"
              (click)="requestChanges()"
            >
              {{ 'publishing.review.requestChanges' | t: lang() }}
            </button>
            <button
              type="button"
              class="btn btn--danger"
              [disabled]="busy() || !notes.trim()"
              (click)="reject()"
            >
              {{ 'publishing.review.reject' | t: lang() }}
            </button>
            @if (canPublish()) {
              <button type="button" class="btn btn--primary" [disabled]="busy()" (click)="publish()">
                {{ 'platformReviews.publish' | t: lang() }}
              </button>
            }
          </div>
        </app-enterprise-section-card>

        @if (actionError()) {
          <app-enterprise-error-state [message]="actionError()!" />
        }
        @if (info()) {
          <p class="success" role="status">{{ info() }}</p>
        }
      }
    </div>
  `,
  styles: `
    .back-link {
      display: inline-block;
      margin-bottom: 0.75rem;
      color: rgba(255, 255, 255, 0.7);
      text-decoration: none;
    }
    .preview-note {
      margin: 0 0 0.75rem;
      padding: 0.65rem 0.9rem;
      border-radius: 8px;
      background: rgba(59, 130, 246, 0.12);
      border: 1px solid rgba(59, 130, 246, 0.3);
      color: #93c5fd;
      font-size: 0.88rem;
    }
    .private-banner {
      margin: 0 0 1rem;
      padding: 0.75rem 1rem;
      border-radius: 8px;
      background: rgba(240, 195, 106, 0.12);
      border: 1px solid rgba(240, 195, 106, 0.35);
      color: #f0c36a;
      font-size: 0.9rem;
    }
    .alerts,
    .track-list {
      list-style: none;
      padding: 0;
      margin: 0;
    }
    .alert,
    .track-list li {
      padding: 0.4rem 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      font-size: 0.9rem;
    }
    .alert--error,
    .alert--critical {
      color: #f87171;
    }
    .alert--warning {
      color: #f0c36a;
    }
    .field-label {
      display: block;
      margin-bottom: 0.35rem;
      font-size: 0.85rem;
      color: rgba(255, 255, 255, 0.65);
    }
    .textarea {
      width: 100%;
      resize: vertical;
    }
    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      margin-top: 0.85rem;
    }
    .btn--danger {
      background: rgba(248, 113, 113, 0.15);
      border: 1px solid rgba(248, 113, 113, 0.4);
      color: #fecaca;
    }
    .muted {
      color: rgba(255, 255, 255, 0.55);
    }
    .success {
      color: #6fd3a0;
      margin-top: 0.75rem;
    }
  `,
})
export class PlatformCatalogReviewDetailPage implements OnInit {
  private readonly api = inject(CatalogPublishingApiService);
  private readonly route = inject(ActivatedRoute);
  private readonly i18n = inject(I18nService);

  readonly lang = this.i18n.lang;
  readonly detail = signal<ReleaseDetail | null>(null);
  readonly loading = signal(false);
  readonly busy = signal(false);
  readonly error = signal<string | null>(null);
  readonly actionError = signal<string | null>(null);
  readonly info = signal<string | null>(null);
  notes = '';

  private submissionId = 0;

  ngOnInit(): void {
    this.submissionId = Number(this.route.snapshot.paramMap.get('id'));
    if (!this.submissionId) {
      this.error.set(this.i18n.t('publishing.detail.notFound'));
      return;
    }
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.error.set(null);
    this.api.platformReviewDetail(this.submissionId).subscribe({
      next: (detail) => {
        this.detail.set(detail);
        this.loading.set(false);
      },
      error: (err) => {
        this.error.set(userFacingHttpError(this.i18n, err));
        this.loading.set(false);
      },
    });
  }

  title(): string {
    const submission = this.detail()?.submission;
    return submission ? displayReleaseTitle(submission.title, submission.status) : '';
  }

  privateBanner(): boolean {
    const detail = this.detail();
    return detail ? hasPrivateMedia(detail.submission, detail.tracks) : false;
  }

  alerts() {
    return (this.detail()?.issues ?? []).filter(
      (issue) =>
        !issue.resolved &&
        (issue.severity === 'error' ||
          issue.severity === 'warning' ||
          issue.severity === 'critical' ||
          (issue.code || '').toLowerCase().includes('right')),
    );
  }

  canPublish(): boolean {
    return this.detail()?.submission.status === 'approved';
  }

  approve(): void {
    this.run(this.api.platformApprove(this.submissionId, this.notes), 'publishing.review.approved');
  }

  requestChanges(): void {
    const notes = this.notes.trim();
    if (!notes) {
      this.actionError.set(this.i18n.t('publishing.review.notesRequired'));
      this.info.set(null);
      return;
    }
    this.run(
      this.api.platformRequestChanges(this.submissionId, notes),
      'publishing.review.changesRequested',
    );
  }

  reject(): void {
    const reason = this.notes.trim();
    if (!reason) return;
    this.run(this.api.platformReject(this.submissionId, reason), 'publishing.review.rejected');
  }

  publish(): void {
    this.run(this.api.platformPublish(this.submissionId), 'platformReviews.published');
  }

  private run(request: Observable<unknown>, successKey: string): void {
    this.busy.set(true);
    this.actionError.set(null);
    this.info.set(null);
    request.subscribe({
      next: () => {
        this.info.set(this.i18n.t(successKey));
        this.busy.set(false);
        this.load();
      },
      error: (err: unknown) => {
        this.actionError.set(userFacingHttpError(this.i18n, err));
        this.busy.set(false);
      },
    });
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
