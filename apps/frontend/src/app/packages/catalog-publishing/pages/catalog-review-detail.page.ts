import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { CatalogPublishingApiService } from '../services/catalog-publishing.api';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import {
  ReleaseDetail,
  hasPrivateMedia,
  publishingPrimaryLabelKey,
  publishingUiBucket,
} from '../models/catalog-publishing.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { userFacingHttpError } from '../../../core/i18n/user-facing-error';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import { catalogPublishingAccess } from '../catalog-publishing-access';

@Component({
  selector: 'app-catalog-review-detail',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    RouterModule,
    TranslatePipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  template: `
    <div class="vx-enterprise catalog-review-detail-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else if (!canReview) {
        <app-enterprise-empty-state
          [title]="'publishing.review.forbidden' | t:lang()"
          [description]="'publishing.review.forbiddenBody' | t:lang()"
        />
      } @else {
        <a routerLink="/catalog-review" class="back-link">
          {{ 'publishing.review.back' | t:lang() }}
        </a>

        @if (loading) {
          <app-enterprise-loading-skeleton [rows]="6" />
        } @else if (error && !detail) {
          <app-enterprise-error-state [message]="error" (retry)="load()" />
        } @else if (!detail) {
          <app-enterprise-empty-state [title]="'publishing.detail.notFound' | t:lang()" />
        } @else {
          <app-enterprise-page-header [title]="detail.submission.title">
            <app-enterprise-status-badge
              [status]="badgeStatus(detail.submission.status)"
              [label]="statusLabel(detail.submission.status)"
            />
          </app-enterprise-page-header>

          <div class="preview-note" role="note">
            {{ 'publishing.review.privatePreviewNote' | t:lang() }}
          </div>

          @if (showPrivateBanner) {
            <div class="private-banner" role="status">
              {{ 'publishing.media.privateBanner' | t:lang() }}
            </div>
          }

          @if (rightsAlerts.length) {
            <app-enterprise-section-card [title]="'publishing.review.rightsAlerts' | t:lang()">
              <ul class="alerts">
                @for (a of rightsAlerts; track a.id) {
                  <li [class]="'alert alert--' + a.severity">
                    <strong>{{ a.severity }}</strong> · {{ a.code }} — {{ a.message }}
                  </li>
                }
              </ul>
            </app-enterprise-section-card>
          }

          <app-enterprise-section-card [title]="'publishing.detail.tracks' | t:lang()">
            @if (!detail.tracks.length) {
              <p class="muted">{{ 'publishing.tracks.empty' | t:lang() }}</p>
            } @else {
              <ul class="track-list">
                @for (t of detail.tracks; track t.id) {
                  <li>{{ t.track_number }}. {{ t.title }}</li>
                }
              </ul>
            }
          </app-enterprise-section-card>

          <app-enterprise-section-card [title]="'publishing.review.actions' | t:lang()">
            <label class="field-label">{{ 'publishing.review.notes' | t:lang() }}</label>
            <textarea [(ngModel)]="notes" class="input textarea" rows="3"></textarea>

            <div class="actions">
              <button type="button" class="btn btn--primary" [disabled]="busy" (click)="approve()">
                {{ 'publishing.review.approve' | t:lang() }}
              </button>
              <button type="button" class="btn btn--secondary" [disabled]="busy" (click)="requestChanges()">
                {{ 'publishing.review.requestChanges' | t:lang() }}
              </button>
              <button type="button" class="btn btn--danger" [disabled]="busy || !notes.trim()" (click)="reject()">
                {{ 'publishing.review.reject' | t:lang() }}
              </button>
            </div>
          </app-enterprise-section-card>

          @if (actionError) {
            <app-enterprise-error-state [message]="actionError" />
          }
          @if (info) {
            <p class="success">{{ info }}</p>
          }
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
    .alerts { list-style: none; padding: 0; margin: 0; }
    .alert {
      padding: 0.5rem 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      font-size: 0.9rem;
    }
    .alert--error, .alert--critical { color: #f87171; }
    .alert--warning { color: #f0c36a; }
    .track-list { list-style: none; padding: 0; margin: 0; }
    .track-list li {
      padding: 0.35rem 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }
    .field-label {
      display: block;
      margin-bottom: 0.35rem;
      font-size: 0.85rem;
      color: rgba(255, 255, 255, 0.65);
    }
    .textarea { width: 100%; resize: vertical; }
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
    .muted { color: rgba(255, 255, 255, 0.55); }
    .success { color: #6fd3a0; margin-top: 0.75rem; }
  `,
})
export class CatalogReviewDetailPage implements OnInit {
  private api = inject(CatalogPublishingApiService);
  private orgCtx = inject(OrganizationContextService);
  private route = inject(ActivatedRoute);
  private i18n = inject(I18nService);
  private access = catalogPublishingAccess();
  readonly lang = this.i18n.lang;

  orgId: number | null = null;
  submissionId = 0;
  canReview = false;
  detail: ReleaseDetail | null = null;
  loading = false;
  busy = false;
  error: string | null = null;
  actionError: string | null = null;
  info: string | null = null;
  notes = '';
  showPrivateBanner = false;

  get rightsAlerts() {
    return (this.detail?.issues ?? []).filter(
      (i) =>
        !i.resolved &&
        (i.severity === 'error' ||
          i.severity === 'warning' ||
          i.severity === 'critical' ||
          (i.code || '').toLowerCase().includes('right')),
    );
  }

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    this.canReview = this.access.canReview();
    this.submissionId = Number(this.route.snapshot.paramMap.get('id'));
    if (!this.orgId || !this.canReview || !this.submissionId) return;
    this.load();
  }

  load(): void {
    if (!this.orgId || !this.submissionId) return;
    this.loading = true;
    this.error = null;
    this.api.getRelease(this.orgId, this.submissionId).subscribe({
      next: (detail) => {
        this.detail = detail;
        this.showPrivateBanner = hasPrivateMedia(detail.submission, detail.tracks);
        this.loading = false;
      },
      error: (e) => {
        this.error = userFacingHttpError(this.i18n, e);
        this.loading = false;
      },
    });
  }

  approve(): void {
    if (!this.orgId || !this.submissionId) return;
    this.busy = true;
    this.actionError = null;
    this.api.reviewApprove(this.orgId, this.submissionId, this.notes).subscribe({
      next: () => {
        this.info = this.i18n.t('publishing.review.approved');
        this.busy = false;
        this.load();
      },
      error: (e) => {
        this.actionError = userFacingHttpError(this.i18n, e);
        this.busy = false;
      },
    });
  }

  reject(): void {
    if (!this.orgId || !this.submissionId || !this.notes.trim()) return;
    this.busy = true;
    this.actionError = null;
    this.api.reviewReject(this.orgId, this.submissionId, this.notes.trim()).subscribe({
      next: () => {
        this.info = this.i18n.t('publishing.review.rejected');
        this.busy = false;
        this.load();
      },
      error: (e) => {
        this.actionError = userFacingHttpError(this.i18n, e);
        this.busy = false;
      },
    });
  }

  requestChanges(): void {
    if (!this.orgId || !this.submissionId) return;
    this.busy = true;
    this.actionError = null;
    this.api
      .reviewRequestChanges(this.orgId, this.submissionId, this.notes || 'changes requested')
      .subscribe({
        next: () => {
          this.info = this.i18n.t('publishing.review.changesRequested');
          this.busy = false;
          this.load();
        },
        error: (e) => {
          this.actionError = userFacingHttpError(this.i18n, e);
          this.busy = false;
        },
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
