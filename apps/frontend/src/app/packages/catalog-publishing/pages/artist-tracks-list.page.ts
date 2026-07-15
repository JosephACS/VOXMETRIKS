import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { catchError, forkJoin, map, of } from 'rxjs';
import { CatalogPublishingApiService } from '../services/catalog-publishing.api';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import {
  ReleaseSubmission,
  SubmissionTrack,
  hasPrivateMedia,
  publishingPrimaryLabelKey,
  publishingUiBucket,
} from '../models/catalog-publishing.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

interface TrackRow {
  track: SubmissionTrack;
  release: ReleaseSubmission;
  privateAudio: boolean;
}

@Component({
  selector: 'app-artist-tracks-list',
  standalone: true,
  imports: [CommonModule, RouterModule, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise artist-tracks-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <app-enterprise-page-header
          [title]="'publishing.tracks.title' | t:lang()"
          [subtitle]="'publishing.tracks.subtitle' | t:lang()"
        />

        @if (anyPrivate) {
          <div class="private-banner" role="status">
            {{ 'publishing.media.privateBanner' | t:lang() }}
          </div>
        }

        @if (loading) {
          <app-enterprise-loading-skeleton [rows]="5" />
        } @else if (error) {
          <app-enterprise-error-state [message]="error" (retry)="load()" />
        } @else if (!rows.length) {
          <app-enterprise-empty-state
            [title]="'publishing.tracks.empty' | t:lang()"
            [description]="'publishing.tracks.emptyBody' | t:lang()"
          />
        } @else {
          <app-enterprise-data-table>
            <table class="data-table">
              <thead>
                <tr>
                  <th>{{ 'publishing.field.trackTitle' | t:lang() }}</th>
                  <th>{{ 'publishing.releases.title' | t:lang() }}</th>
                  <th>{{ 'common.status' | t:lang() }}</th>
                  <th>{{ 'publishing.field.isrc' | t:lang() }}</th>
                </tr>
              </thead>
              <tbody>
                @for (row of rows; track row.track.id) {
                  <tr>
                    <td>
                      {{ row.track.title }}
                      @if (row.privateAudio) {
                        <span class="tag">{{ 'publishing.media.privateTag' | t:lang() }}</span>
                      }
                    </td>
                    <td>
                      <a [routerLink]="['/artist/releases', row.release.id]">
                        {{ row.release.title }}
                      </a>
                    </td>
                    <td>
                      <app-enterprise-status-badge
                        [status]="badgeStatus(row.release.status)"
                        [label]="statusLabel(row.release.status)"
                      />
                    </td>
                    <td>{{ row.track.isrc || '—' }}</td>
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
    .private-banner {
      margin: 0 0 1rem;
      padding: 0.75rem 1rem;
      border-radius: 8px;
      background: rgba(240, 195, 106, 0.12);
      border: 1px solid rgba(240, 195, 106, 0.35);
      color: #f0c36a;
      font-size: 0.9rem;
    }
    .tag {
      margin-left: 0.4rem;
      font-size: 0.75rem;
      color: #f0c36a;
    }
    a { color: inherit; }
  `,
})
export class ArtistTracksListPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;
  private api = inject(CatalogPublishingApiService);
  private orgCtx = inject(OrganizationContextService);

  orgId: number | null = null;
  rows: TrackRow[] = [];
  loading = false;
  error: string | null = null;
  anyPrivate = false;

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    if (!this.orgId) return;
    this.load();
  }

  load(): void {
    if (!this.orgId) return;
    this.loading = true;
    this.error = null;
    const orgId = this.orgId;

    this.api
      .listPortalReleases(orgId)
      .pipe(
        catchError(() =>
          this.api.listReleases(orgId).pipe(catchError(() => of([] as ReleaseSubmission[]))),
        ),
        map((releases) => releases ?? []),
      )
      .subscribe((releases) => {
        if (!releases.length) {
          this.rows = [];
          this.anyPrivate = false;
          this.loading = false;
          return;
        }
        const limited = releases.slice(0, 25);
        forkJoin(
          limited.map((r) =>
            this.api.getRelease(orgId, r.id).pipe(
              catchError(() => of(null)),
              map((detail) => ({ release: r, detail })),
            ),
          ),
        ).subscribe({
          next: (packs) => {
            const rows: TrackRow[] = [];
            for (const p of packs) {
              if (!p.detail) continue;
              const privateRel = hasPrivateMedia(p.detail.submission, p.detail.tracks);
              for (const t of p.detail.tracks) {
                rows.push({
                  track: t,
                  release: p.detail.submission,
                  privateAudio: privateRel && !!t.audio_media_id,
                });
              }
            }
            this.rows = rows;
            this.anyPrivate = rows.some((r) => r.privateAudio);
            this.loading = false;
          },
          error: () => {
            this.rows = [];
            this.loading = false;
          },
        });
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
