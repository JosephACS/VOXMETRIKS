import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { ArtistContextService } from '../services/artist-context.service';
import { ArtistSpaceApiService } from '../services/artist-space-api.service';
import { artistJourneyError } from '../services/artist-space-error';
import {
  ReleaseSubmission,
  displayReleaseTitle,
  humanReleaseStatus,
  publishingUiBucket,
} from '../../catalog-publishing/models/catalog-publishing.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

type MusicTab = 'releases' | 'tracks';
type ReleaseStatusFilter = 'all' | 'draft' | 'in_review' | 'published';

interface WarehouseTrack {
  id_track?: number;
  nombre_track?: string;
  nombre_album?: string;
  [key: string]: unknown;
}

/**
 * Spec 051 — single Artist Space music surface.
 * Replaces the split tracks/releases pages; both remain reachable as tabs.
 */
@Component({
  selector: 'app-artist-space-music',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise artist-space-music-page">
      <app-enterprise-page-header
        [title]="'artistSpace.music.title' | t: lang()"
        [subtitle]="'artistSpace.music.subtitle' | t: lang()"
      >
        @if (canCreateRelease()) {
          <a
            class="btn btn--primary"
            routerLink="/artist-space/releases/new"
            data-testid="new-release-cta"
          >
            {{ 'artistSpace.music.newRelease' | t: lang() }}
          </a>
        }
      </app-enterprise-page-header>

      <nav class="tabs" role="tablist" aria-label="music">
        <button
          type="button"
          role="tab"
          class="tab"
          data-testid="tab-releases"
          [class.tab--active]="tab() === 'releases'"
          [attr.aria-selected]="tab() === 'releases'"
          (click)="selectTab('releases')"
        >
          {{ 'artistSpace.music.tabReleases' | t: lang() }}
        </button>
        <button
          type="button"
          role="tab"
          class="tab"
          data-testid="tab-tracks"
          [class.tab--active]="tab() === 'tracks'"
          [attr.aria-selected]="tab() === 'tracks'"
          (click)="selectTab('tracks')"
        >
          {{ 'artistSpace.music.tabTracks' | t: lang() }}
        </button>
      </nav>

      <div class="filters">
        <label class="filter">
          <span>{{ 'common.search' | t: lang() }}</span>
          <input
            class="input"
            type="search"
            [ngModel]="query()"
            (ngModelChange)="query.set($event)"
            [attr.placeholder]="'artistSpace.music.filterPlaceholder' | t: lang()"
          />
        </label>
        @if (tab() === 'releases') {
          <label class="filter">
            <span>{{ 'common.status' | t: lang() }}</span>
            <select
              class="input"
              [ngModel]="statusFilter()"
              (ngModelChange)="statusFilter.set($event)"
            >
              <option value="all">{{ 'publishing.review.filterAll' | t: lang() }}</option>
              <option value="draft">{{ 'publishing.status.draft' | t: lang() }}</option>
              <option value="in_review">{{ 'publishing.status.inReview' | t: lang() }}</option>
              <option value="published">{{ 'publishing.status.published' | t: lang() }}</option>
            </select>
          </label>
        }
      </div>

      @if (tab() === 'releases') {
        @if (releasesLoading()) {
          <app-enterprise-loading-skeleton [rows]="4" />
        } @else if (releasesError()) {
          <app-enterprise-error-state [message]="releasesError()!" (retry)="loadReleases()" />
        } @else if (!filteredReleases().length) {
          <app-enterprise-empty-state
            [title]="'artistSpace.releases.emptyTitle' | t: lang()"
            [description]="'artistSpace.releases.emptyBody' | t: lang()"
            [ctaLabel]="
              canCreateRelease() ? ('artistSpace.music.newRelease' | t: lang()) : undefined
            "
            [ctaLink]="canCreateRelease() ? '/artist-space/releases/new' : undefined"
          />
        } @else {
          <app-enterprise-data-table>
            <table class="data-table" data-testid="artist-releases-table">
              <thead>
                <tr>
                  <th>{{ 'publishing.field.title' | t: lang() }}</th>
                  <th>{{ 'publishing.field.releaseType' | t: lang() }}</th>
                  <th>{{ 'common.status' | t: lang() }}</th>
                </tr>
              </thead>
              <tbody>
                @for (r of filteredReleases(); track r.id) {
                  <tr>
                    <td>{{ releaseTitle(r) }}</td>
                    <td>{{ r.release_type }}</td>
                    <td>
                      <app-enterprise-status-badge
                        [status]="badgeStatus(r.status)"
                        [label]="statusLabel(r.status)"
                      />
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </app-enterprise-data-table>
        }
      } @else {
        @if (tracksLoading()) {
          <app-enterprise-loading-skeleton [rows]="4" />
        } @else if (tracksError()) {
          <app-enterprise-error-state [message]="tracksError()!" (retry)="loadTracks()" />
        } @else if (!filteredTracks().length) {
          <app-enterprise-empty-state
            [title]="'artistSpace.tracks.emptyTitle' | t: lang()"
            [description]="'artistSpace.tracks.emptyBody' | t: lang()"
          />
        } @else {
          <ul class="track-list" data-testid="artist-tracks-list">
            @for (t of filteredTracks(); track trackId(t)) {
              <li>
                <span class="track-list__name">{{ trackName(t) }}</span>
              </li>
            }
          </ul>
          <p class="muted">{{ 'artistSpace.tracks.total' | t: lang() }}: {{ trackTotal() }}</p>
        }
      }
    </div>
  `,
  styles: [
    `
      .artist-space-music-page {
        --music-border: var(--vx-border, rgba(255, 255, 255, 0.12));
        --music-muted: var(--vx-text-secondary, rgba(255, 255, 255, 0.6));
      }
      .tabs {
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem;
        margin: 0.5rem 0 1rem;
      }
      .tab {
        border: 1px solid var(--music-border);
        background: rgba(255, 255, 255, 0.03);
        color: var(--music-muted);
        border-radius: 999px;
        padding: 0.4rem 0.9rem;
        font-size: 0.85rem;
        cursor: pointer;
      }
      .tab--active {
        border-color: var(--vx-accent, #6fd3a0);
        color: inherit;
      }
      .filters {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        margin-bottom: 1rem;
      }
      .filter {
        display: flex;
        flex-direction: column;
        gap: 0.3rem;
        flex: 1 1 14rem;
        min-width: 0;
        font-size: 0.82rem;
        color: var(--music-muted);
      }
      .track-list {
        list-style: none;
        margin: 0;
        padding: 0;
      }
      .track-list li {
        padding: 0.55rem 0;
        border-bottom: 1px solid var(--music-border);
      }
      .track-list__name {
        overflow-wrap: anywhere;
      }
      .muted {
        color: var(--music-muted);
        font-size: 0.85rem;
      }
    `,
  ],
})
export class ArtistSpaceMusicPage implements OnInit {
  private readonly api = inject(ArtistSpaceApiService);
  private readonly artistCtx = inject(ArtistContextService);
  private readonly i18n = inject(I18nService);

  readonly lang = this.i18n.lang;
  readonly tab = signal<MusicTab>('releases');
  readonly query = signal('');
  readonly statusFilter = signal<ReleaseStatusFilter>('all');

  readonly releases = signal<ReleaseSubmission[]>([]);
  readonly releasesLoading = signal(false);
  readonly releasesError = signal<string | null>(null);

  readonly tracks = signal<WarehouseTrack[]>([]);
  readonly trackTotal = signal(0);
  readonly tracksLoading = signal(false);
  readonly tracksError = signal<string | null>(null);
  private tracksLoaded = false;

  canCreateRelease(): boolean {
    return this.artistCtx.can('artist_space.release.create');
  }

  ngOnInit(): void {
    this.loadReleases();
  }

  selectTab(tab: MusicTab): void {
    this.tab.set(tab);
    if (tab === 'tracks' && !this.tracksLoaded) {
      this.loadTracks();
    }
  }

  loadReleases(): void {
    const id = this.artistCtx.artistProfileId();
    if (id == null) {
      this.releasesError.set(this.i18n.t('artistSpace.error.noActiveArtist'));
      return;
    }
    this.releasesLoading.set(true);
    this.releasesError.set(null);
    this.api.listArtistReleases(id).subscribe({
      next: (rows) => {
        this.releases.set(rows ?? []);
        this.releasesLoading.set(false);
      },
      error: (e) => {
        this.releases.set([]);
        this.releasesError.set(artistJourneyError(this.i18n, e));
        this.releasesLoading.set(false);
      },
    });
  }

  loadTracks(): void {
    const id = this.artistCtx.artistProfileId();
    if (id == null) {
      this.tracksError.set(this.i18n.t('artistSpace.error.noActiveArtist'));
      return;
    }
    this.tracksLoading.set(true);
    this.tracksError.set(null);
    this.api.tracks(id).subscribe({
      next: (r) => {
        this.tracks.set((r?.items ?? []) as WarehouseTrack[]);
        this.trackTotal.set(r?.total ?? 0);
        this.tracksLoaded = true;
        this.tracksLoading.set(false);
      },
      error: (e) => {
        this.tracks.set([]);
        this.tracksError.set(artistJourneyError(this.i18n, e));
        this.tracksLoading.set(false);
      },
    });
  }

  filteredReleases(): ReleaseSubmission[] {
    const needle = this.query().trim().toLowerCase();
    const status = this.statusFilter();
    return this.releases().filter((r) => {
      if (needle && !displayReleaseTitle(r.title, r.status).toLowerCase().includes(needle)) {
        return false;
      }
      if (status === 'all') return true;
      const bucket = publishingUiBucket(r.status);
      return bucket === status;
    });
  }

  filteredTracks(): WarehouseTrack[] {
    const needle = this.query().trim().toLowerCase();
    if (!needle) return this.tracks();
    return this.tracks().filter((t) => this.trackName(t).toLowerCase().includes(needle));
  }

  trackId(track: WarehouseTrack): number {
    return Number(track['id_track'] ?? 0);
  }

  trackName(track: WarehouseTrack): string {
    return String(track['nombre_track'] ?? '—');
  }

  releaseTitle(release: ReleaseSubmission): string {
    return displayReleaseTitle(release.title, release.status);
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
