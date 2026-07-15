import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { catchError, of } from 'rxjs';
import { CatalogPublishingApiService } from '../services/catalog-publishing.api';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { PortalSummary, publishingUiBucket } from '../models/catalog-publishing.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { AuthService } from '../../../core/services/auth.service';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-artist-profile-page',
  standalone: true,
  imports: [CommonModule, RouterModule, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise artist-profile-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <app-enterprise-page-header
          [title]="'publishing.profile.title' | t:lang()"
          [subtitle]="'publishing.profile.subtitle' | t:lang()"
        />

        @if (loading) {
          <app-enterprise-loading-skeleton [rows]="4" />
        } @else if (error) {
          <app-enterprise-error-state [message]="error" (retry)="load()" />
        } @else {
          <app-enterprise-section-card [title]="'publishing.profile.account' | t:lang()">
            <dl class="meta">
              <dt>{{ 'publishing.profile.username' | t:lang() }}</dt>
              <dd>{{ username }}</dd>
              <dt>{{ 'publishing.profile.org' | t:lang() }}</dt>
              <dd>#{{ summary?.organization_id ?? orgId }}</dd>
              <dt>{{ 'publishing.profile.artistIds' | t:lang() }}</dt>
              <dd>
                @if (summary?.artist_profile_ids?.length) {
                  {{ summary!.artist_profile_ids.join(', ') }}
                } @else {
                  —
                }
              </dd>
            </dl>
          </app-enterprise-section-card>

          <app-enterprise-section-card [title]="'publishing.profile.counts' | t:lang()">
            <div class="count-row">
              <span class="count-chip">{{ 'publishing.status.draft' | t:lang() }}: {{ countDraft }}</span>
              <span class="count-chip">{{ 'publishing.status.inReview' | t:lang() }}: {{ countReview }}</span>
              <span class="count-chip">{{ 'publishing.status.published' | t:lang() }}: {{ countPublished }}</span>
            </div>
            <div class="quick-links">
              <a routerLink="/artist/releases" class="btn btn--secondary btn--sm">
                {{ 'nav.artist.releases' | t:lang() }}
              </a>
              <a routerLink="/artist/releases/new" class="btn btn--primary btn--sm">
                {{ 'nav.artist.newRelease' | t:lang() }}
              </a>
            </div>
          </app-enterprise-section-card>
        }
      }
    </div>
  `,
  styles: `
    .meta {
      display: grid;
      grid-template-columns: minmax(8rem, 14rem) 1fr;
      gap: 0.4rem 1rem;
      margin: 0;
    }
    .meta dt { color: rgba(255, 255, 255, 0.5); }
    .meta dd { margin: 0; }
    .count-row {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      margin-bottom: 1rem;
    }
    .count-chip {
      font-size: 0.8rem;
      padding: 0.35rem 0.75rem;
      border-radius: 999px;
      border: 1px solid rgba(255, 255, 255, 0.12);
      background: rgba(255, 255, 255, 0.04);
    }
    .quick-links {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
    }
  `,
})
export class ArtistProfilePage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;
  private api = inject(CatalogPublishingApiService);
  private orgCtx = inject(OrganizationContextService);
  private auth = inject(AuthService);

  orgId: number | null = null;
  summary: PortalSummary | null = null;
  username = '';
  loading = false;
  error: string | null = null;
  countDraft = 0;
  countReview = 0;
  countPublished = 0;

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    this.username = this.auth.getUser()?.username ?? '—';
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
      .subscribe({
        next: (s) => {
          this.summary = s;
          const counts = s?.status_counts ?? {};
          this.countDraft = counts['draft'] ?? 0;
          this.countPublished = counts['published'] ?? 0;
          this.countReview = Object.entries(counts).reduce((acc, [k, v]) => {
            if (publishingUiBucket(k) === 'in_review') return acc + v;
            return acc;
          }, 0);
          this.loading = false;
        },
        error: () => {
          this.summary = null;
          this.loading = false;
        },
      });
  }
}
