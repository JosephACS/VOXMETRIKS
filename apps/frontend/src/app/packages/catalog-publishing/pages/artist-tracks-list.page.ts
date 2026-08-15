import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { catchError, forkJoin, map } from 'rxjs';
import { CatalogPublishingApiService } from '../services/catalog-publishing.api';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import {
  ReleaseSubmission,
  SubmissionTrack,
  displayReleaseTitle,
  hasPrivateMedia,
  humanReleaseStatus,
  publishingUiBucket,
} from '../models/catalog-publishing.models';
import { AuthService } from '../../../core/services/auth.service';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

interface TrackRow {
  track: SubmissionTrack;
  release: ReleaseSubmission;
  privateAudio: boolean;
}

@Component({
  selector: 'app-artist-tracks-list',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, ...ENTERPRISE_UI_IMPORTS],
  styleUrls: ['../styles/catalog-editorial.css'],
  template: `
    <div class="vx-enterprise cat-page" data-testid="artist-tracks-list">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <header class="cat-head">
          <p class="cat-kicker">Catálogo</p>
          <h1 class="cat-title">Canciones</h1>
          <p class="cat-sub">Pistas del catálogo vinculadas a lanzamientos.</p>
        </header>

        <div class="cat-toolbar">
          <input
            class="cat-search"
            type="search"
            [(ngModel)]="query"
            placeholder="Buscar canción o lanzamiento"
            aria-label="Buscar canción o lanzamiento"
          />
        </div>

        @if (loading) {
          <app-enterprise-loading-skeleton [rows]="5" />
        } @else if (error) {
          <app-enterprise-error-state [message]="error" (retry)="load()" />
        } @else if (!filteredRows.length) {
          <section class="cat-section">
            <p class="cat-empty">No encontramos contenido con estos filtros.</p>
          </section>
        } @else {
          <section class="cat-section">
            <ul class="cat-list">
              @for (row of filteredRows; track row.track.id) {
                <li>
                  <a class="cat-row" [routerLink]="['/artist/releases', row.release.id]">
                    <div class="cat-cover" aria-hidden="true">
                      @if (coverUrl(row.release); as src) {
                        <img [src]="src" alt="" loading="lazy" (error)="onCoverError($event)" />
                      } @else {
                        <img class="cat-cover__mark" src="/assets/images/voxmetrik-icon.webp" alt="" />
                      }
                    </div>
                    <div>
                      <p class="cat-row__title">{{ row.track.title }}</p>
                      <p class="cat-row__meta">
                        {{ displayTitle(row.release) }}
                        @if (row.track.isrc) {
                          · {{ row.track.isrc }}
                        }
                        @if (!row.track.audio_media_id && row.release.status !== 'published') {
                          · Fuente de reproducción pendiente
                        }
                      </p>
                    </div>
                    <div class="cat-row__side">
                      <span class="cat-badge" [ngClass]="badgeClass(row.release.status)">{{
                        humanStatus(row.release.status)
                      }}</span>
                    </div>
                  </a>
                </li>
              }
            </ul>
          </section>
        }
      }
    </div>
  `,
})
export class ArtistTracksListPage implements OnInit {
  private api = inject(CatalogPublishingApiService);
  private orgCtx = inject(OrganizationContextService);
  private auth = inject(AuthService);

  orgId: number | null = null;
  rows: TrackRow[] = [];
  loading = false;
  error: string | null = null;
  query = '';

  get filteredRows(): TrackRow[] {
    const q = this.query.trim().toLowerCase();
    if (!q) return this.rows;
    return this.rows.filter(
      (row) =>
        row.track.title.toLowerCase().includes(q) ||
        row.release.title.toLowerCase().includes(q) ||
        (row.track.isrc || '').toLowerCase().includes(q),
    );
  }

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
        catchError(() => this.api.listReleases(orgId)),
        map((releases) => releases ?? []),
      )
      .subscribe({
        next: (releases) => {
          if (!releases.length) {
            this.rows = [];
            this.loading = false;
            return;
          }
          const limited = releases.slice(0, 25);
          forkJoin(
            limited.map((r) =>
              this.api.getRelease(orgId, r.id).pipe(map((detail) => ({ release: r, detail }))),
            ),
          ).subscribe({
            next: (packs) => {
              const rows: TrackRow[] = [];
              for (const p of packs) {
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
              this.loading = false;
            },
            error: () => {
              this.rows = [];
              this.loading = false;
              this.error = 'No se pudieron cargar las pistas.';
            },
          });
        },
        error: () => {
          this.rows = [];
          this.loading = false;
          this.error = 'No se pudieron cargar los lanzamientos.';
        },
      });
  }

  coverUrl(r: ReleaseSubmission): string | null {
    const id = r.cover_media_id;
    if (!id) return null;
    const base = this.api.mediaContentUrl(id);
    const token = this.auth.getToken();
    return token ? `${base}${base.includes('?') ? '&' : '?'}token=${encodeURIComponent(token)}` : base;
  }

  onCoverError(ev: Event): void {
    const img = ev.target as HTMLImageElement | null;
    if (!img) return;
    img.style.display = 'none';
    const parent = img.parentElement;
    if (parent && !parent.querySelector('.cat-cover__mark')) {
      const mark = document.createElement('img');
      mark.className = 'cat-cover__mark';
      mark.src = '/assets/images/voxmetrik-icon.webp';
      mark.alt = '';
      parent.appendChild(mark);
    }
  }

  displayTitle(r: ReleaseSubmission): string {
    return displayReleaseTitle(r.title, r.status);
  }

  humanStatus(status: string): string {
    return humanReleaseStatus(status);
  }

  badgeClass(status: string): string {
    const s = (status || '').toLowerCase();
    if (s === 'published') return 'cat-badge--published';
    if (s === 'changes_requested') return 'cat-badge--attention';
    if (s === 'draft') return 'cat-badge--draft';
    if (publishingUiBucket(s) === 'in_review') return 'cat-badge--review';
    return '';
  }
}
