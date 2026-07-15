import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { catchError, of } from 'rxjs';
import { CatalogPublishingApiService } from '../services/catalog-publishing.api';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import {
  ReleaseDetail,
  StatusHistoryEntry,
  hasPrivateMedia,
  publishingPrimaryLabelKey,
  publishingUiBucket,
} from '../models/catalog-publishing.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { LocaleDatePipe } from '../../../shared/pipes/locale-format.pipe';
import { userFacingHttpError } from '../../../core/i18n/user-facing-error';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import { catalogPublishingAccess } from '../catalog-publishing-access';

@Component({
  selector: 'app-artist-release-detail',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    TranslatePipe,
    LocaleDatePipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  template: `
    <div class="vx-enterprise artist-release-detail-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <a routerLink="/artist/releases" class="back-link">
          {{ 'publishing.detail.back' | t:lang() }}
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

          @if (showPrivateBanner) {
            <div class="private-banner" role="status">
              {{ 'publishing.media.privateBanner' | t:lang() }}
            </div>
          }

          <app-enterprise-section-card [title]="'publishing.detail.meta' | t:lang()">
            <dl class="meta">
              <dt>{{ 'common.status' | t:lang() }}</dt>
              <dd>{{ statusLabel(detail.submission.status) }}</dd>
              <dt>{{ 'publishing.field.releaseType' | t:lang() }}</dt>
              <dd>{{ detail.submission.release_type }}</dd>
              <dt>{{ 'publishing.field.genre' | t:lang() }}</dt>
              <dd>{{ detail.submission.genre || '—' }}</dd>
              <dt>{{ 'publishing.tracks.title' | t:lang() }}</dt>
              <dd>{{ detail.tracks.length }}</dd>
              <dt>{{ 'publishing.field.plannedDate' | t:lang() }}</dt>
              <dd>{{ detail.submission.planned_release_date || '—' }}</dd>
            </dl>
          </app-enterprise-section-card>

          <app-enterprise-section-card [title]="'publishing.detail.tracks' | t:lang()">
            @if (!detail.tracks.length) {
              <p class="muted">{{ 'publishing.tracks.empty' | t:lang() }}</p>
            } @else {
              <ul class="track-list">
                @for (t of detail.tracks; track t.id) {
                  <li>
                    <span>{{ t.track_number }}. {{ t.title }}</span>
                    @if (t.audio_media_id && detail.submission.status !== 'published') {
                      <span class="tag">{{ 'publishing.media.privateTag' | t:lang() }}</span>
                    }
                  </li>
                }
              </ul>
            }
          </app-enterprise-section-card>

          <app-enterprise-section-card [title]="'publishing.detail.history' | t:lang()">
            @if (!history.length) {
              <p class="muted">{{ 'publishing.detail.historyEmpty' | t:lang() }}</p>
            } @else {
              <ol class="history">
                @for (h of history; track h.id) {
                  <li>
                    <strong>{{ statusLabel(h.to_status) }}</strong>
                    <span class="muted"> ← {{ statusLabel(h.from_status) }}</span>
                    @if (h.reason) {
                      <span> — {{ h.reason }}</span>
                    }
                    <div class="muted">{{ h.created_at | localeDate:true }}</div>
                  </li>
                }
              </ol>
            }
          </app-enterprise-section-card>

          @if (canSubmit && (detail.submission.status === 'draft' || detail.submission.status === 'changes_requested')) {
            <button type="button" class="btn btn--primary" [disabled]="busy" (click)="submit()">
              {{ 'publishing.detail.submit' | t:lang() }}
            </button>
          }

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
    .private-banner {
      margin: 0 0 1rem;
      padding: 0.75rem 1rem;
      border-radius: 8px;
      background: rgba(240, 195, 106, 0.12);
      border: 1px solid rgba(240, 195, 106, 0.35);
      color: #f0c36a;
      font-size: 0.9rem;
    }
    .meta {
      display: grid;
      grid-template-columns: minmax(8rem, 12rem) 1fr;
      gap: 0.4rem 1rem;
      margin: 0;
    }
    .meta dt { color: rgba(255, 255, 255, 0.5); }
    .meta dd { margin: 0; }
    .track-list {
      list-style: none;
      padding: 0;
      margin: 0;
    }
    .track-list li {
      display: flex;
      justify-content: space-between;
      gap: 0.5rem;
      padding: 0.4rem 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }
    .tag {
      font-size: 0.75rem;
      color: #f0c36a;
    }
    .history { padding-left: 1.1rem; }
    .history li { margin-bottom: 0.65rem; }
    .muted { color: rgba(255, 255, 255, 0.55); }
    .success { color: #6fd3a0; margin-top: 0.75rem; }
  `,
})
export class ArtistReleaseDetailPage implements OnInit {
  private api = inject(CatalogPublishingApiService);
  private orgCtx = inject(OrganizationContextService);
  private route = inject(ActivatedRoute);
  private i18n = inject(I18nService);
  private access = catalogPublishingAccess();
  readonly lang = this.i18n.lang;

  orgId: number | null = null;
  submissionId = 0;
  detail: ReleaseDetail | null = null;
  history: StatusHistoryEntry[] = [];
  loading = false;
  busy = false;
  error: string | null = null;
  actionError: string | null = null;
  info: string | null = null;
  canSubmit = false;
  showPrivateBanner = false;

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    this.canSubmit = this.access.canSubmit();
    this.submissionId = Number(this.route.snapshot.paramMap.get('id'));
    if (!this.orgId || !this.submissionId) return;
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
    this.api
      .releaseHistory(this.orgId, this.submissionId)
      .pipe(catchError(() => of([] as StatusHistoryEntry[])))
      .subscribe((h) => (this.history = h));
  }

  submit(): void {
    if (!this.orgId || !this.submissionId) return;
    this.busy = true;
    this.actionError = null;
    this.api.submitRelease(this.orgId, this.submissionId).subscribe({
      next: () => {
        this.info = this.i18n.t('publishing.detail.submitted');
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
