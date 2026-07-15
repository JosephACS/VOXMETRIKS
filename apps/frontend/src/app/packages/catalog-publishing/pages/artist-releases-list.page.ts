import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { catchError, of } from 'rxjs';
import { CatalogPublishingApiService } from '../services/catalog-publishing.api';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import {
  PortalSummary,
  ReleaseSubmission,
  publishingPrimaryLabelKey,
  publishingUiBucket,
} from '../models/catalog-publishing.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import { catalogPublishingAccess } from '../catalog-publishing-access';

@Component({
  selector: 'app-artist-releases-list',
  standalone: true,
  imports: [CommonModule, RouterModule, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise artist-releases-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <app-enterprise-page-header
          [title]="'publishing.releases.title' | t:lang()"
          [subtitle]="'publishing.releases.subtitle' | t:lang()"
        >
          @if (canCreate) {
            <a routerLink="/artist/releases/new" class="btn btn--primary">
              {{ 'publishing.releases.new' | t:lang() }}
            </a>
          }
        </app-enterprise-page-header>

        <div class="count-row">
          <span class="count-chip count-chip--draft">
            {{ 'publishing.status.draft' | t:lang() }}: {{ countDraft }}
          </span>
          <span class="count-chip count-chip--review">
            {{ 'publishing.status.inReview' | t:lang() }}: {{ countReview }}
          </span>
          <span class="count-chip count-chip--published">
            {{ 'publishing.status.published' | t:lang() }}: {{ countPublished }}
          </span>
        </div>

        @if (loading) {
          <app-enterprise-loading-skeleton [rows]="5" />
        } @else if (error) {
          <app-enterprise-error-state [message]="error" (retry)="load()" />
        } @else if (!rows.length) {
          <app-enterprise-empty-state
            [title]="'publishing.releases.empty' | t:lang()"
            [description]="'publishing.releases.emptyBody' | t:lang()"
            [ctaLabel]="'publishing.releases.new' | t:lang()"
          />
        } @else {
          <div class="release-cards">
            @for (r of rows; track r.id) {
              <article class="release-card">
                <div class="release-card__head">
                  <h3>
                    <a [routerLink]="['/artist/releases', r.id]">{{ r.title }}</a>
                  </h3>
                  <app-enterprise-status-badge
                    [status]="badgeStatus(r.status)"
                    [label]="statusLabel(r.status)"
                  />
                </div>
                <p class="muted">
                  {{ r.release_type }} · #{{ r.id }}
                  @if (r.planned_release_date) {
                    · {{ r.planned_release_date }}
                  }
                </p>
                <div class="release-card__actions">
                  <a [routerLink]="['/artist/releases', r.id]" class="btn btn--secondary btn--sm">
                    {{ 'publishing.releases.open' | t:lang() }}
                  </a>
                </div>
              </article>
            }
          </div>
        }
      }
    </div>
  `,
  styles: `
    .count-row {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      margin-bottom: 1.25rem;
    }
    .count-chip {
      font-size: 0.8rem;
      padding: 0.35rem 0.75rem;
      border-radius: 999px;
      border: 1px solid rgba(255, 255, 255, 0.12);
      background: rgba(255, 255, 255, 0.04);
    }
    .count-chip--draft { color: #c4c4c4; }
    .count-chip--review { color: #f0c36a; }
    .count-chip--published { color: #6fd3a0; }
    .release-cards {
      display: grid;
      gap: 0.85rem;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    }
    .release-card {
      padding: 1rem 1.1rem;
      border-radius: 10px;
      border: 1px solid rgba(255, 255, 255, 0.08);
      background: rgba(12, 14, 18, 0.72);
    }
    .release-card__head {
      display: flex;
      justify-content: space-between;
      gap: 0.75rem;
      align-items: flex-start;
    }
    .release-card h3 {
      margin: 0;
      font-size: 1rem;
    }
    .release-card h3 a {
      color: inherit;
      text-decoration: none;
    }
    .release-card__actions {
      margin-top: 0.75rem;
    }
    .muted { color: rgba(255, 255, 255, 0.55); font-size: 0.85rem; }
  `,
})
export class ArtistReleasesListPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;
  private api = inject(CatalogPublishingApiService);
  private orgCtx = inject(OrganizationContextService);
  private access = catalogPublishingAccess();

  orgId: number | null = null;
  rows: ReleaseSubmission[] = [];
  summary: PortalSummary | null = null;
  loading = false;
  error: string | null = null;
  canCreate = false;
  countDraft = 0;
  countReview = 0;
  countPublished = 0;

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    this.canCreate = this.access.canCreate();
    if (!this.orgId) return;
    this.load();
  }

  load(): void {
    if (!this.orgId) return;
    this.loading = true;
    this.error = null;

    this.api
      .portalSummary(this.orgId)
      .pipe(catchError(() => of(null)))
      .subscribe((s) => {
        this.summary = s;
        this.recomputeCounts();
      });

    this.api
      .listPortalReleases(this.orgId)
      .pipe(
        catchError(() =>
          this.api.listReleases(this.orgId!).pipe(catchError(() => of([] as ReleaseSubmission[]))),
        ),
      )
      .subscribe({
        next: (rows) => {
          this.rows = rows ?? [];
          this.recomputeCounts();
          this.loading = false;
        },
        error: () => {
          this.rows = [];
          this.loading = false;
          this.error = null; // graceful empty
        },
      });
  }

  private recomputeCounts(): void {
    const counts = this.summary?.status_counts;
    if (counts && Object.keys(counts).length) {
      this.countDraft = counts['draft'] ?? 0;
      this.countPublished = counts['published'] ?? 0;
      this.countReview = Object.entries(counts).reduce((acc, [k, v]) => {
        if (publishingUiBucket(k) === 'in_review') return acc + v;
        return acc;
      }, 0);
      return;
    }
    this.countDraft = this.rows.filter((r) => publishingUiBucket(r.status) === 'draft').length;
    this.countReview = this.rows.filter((r) => publishingUiBucket(r.status) === 'in_review').length;
    this.countPublished = this.rows.filter(
      (r) => publishingUiBucket(r.status) === 'published',
    ).length;
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
