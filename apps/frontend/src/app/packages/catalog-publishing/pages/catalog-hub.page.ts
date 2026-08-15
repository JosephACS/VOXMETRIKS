import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { forkJoin, of } from 'rxjs';
import { catchError, map, switchMap } from 'rxjs/operators';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { CatalogPublishingApiService } from '../services/catalog-publishing.api';
import { ArtistsApiService } from '../../artists/services/artists-api.service';
import { ArtistProfile } from '../../artists/models/artist.models';
import {
  PortalSummary,
  ReleaseSubmission,
  SubmissionTrack,
  displayReleaseTitle,
  humanReleaseStatus,
  publishingUiBucket,
} from '../models/catalog-publishing.models';
import { AuthService } from '../../../core/services/auth.service';
import { catalogPublishingAccess } from '../catalog-publishing-access';
import { productArtistDisplayName } from '../../../shared/utils/product-presentation.util';

type ViewFilter = 'all' | 'releases' | 'tracks' | 'artists' | 'attention';

interface TrackPreview {
  track: SubmissionTrack;
  release: ReleaseSubmission;
}

@Component({
  selector: 'app-catalog-hub-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, ...ENTERPRISE_UI_IMPORTS],
  styleUrls: ['../styles/catalog-editorial.css'],
  template: `
    <div class="vx-enterprise cat-page" data-testid="catalog-hub">
      <header class="cat-head">
        <p class="cat-kicker">Catálogo</p>
        <h1 class="cat-title">Catálogo y publicación</h1>
        <p class="cat-sub">Gestiona música, artistas y lanzamientos del catálogo.</p>
      </header>

      @if (!orgId) {
        <app-enterprise-org-required />
      } @else if (loading()) {
        <app-enterprise-loading-skeleton [rows]="7" />
      } @else if (error()) {
        <app-enterprise-error-state [message]="error()!" (retry)="load()" />
      } @else {
        <div class="cat-signals" aria-label="Resumen operativo">
          <span class="cat-chip">Canciones <strong>{{ trackCount() }}</strong></span>
          <span class="cat-chip">Artistas <strong>{{ artistCount() }}</strong></span>
          <span class="cat-chip">Lanzamientos <strong>{{ releaseCount() }}</strong></span>
          @if (attentionCount() > 0) {
            <span class="cat-chip cat-chip--attention"
              >Requieren atención <strong>{{ attentionCount() }}</strong></span
            >
          }
        </div>

        <div class="cat-toolbar">
          <input
            class="cat-search"
            type="search"
            [(ngModel)]="query"
            (ngModelChange)="onQuery()"
            placeholder="Buscar música, artista o lanzamiento"
            aria-label="Buscar música, artista o lanzamiento"
          />
          <select class="cat-select" [(ngModel)]="filter" (ngModelChange)="onQuery()" aria-label="Filtrar">
            <option value="all">Todo</option>
            <option value="releases">Lanzamientos</option>
            <option value="tracks">Canciones</option>
            <option value="artists">Artistas</option>
            <option value="attention">Requieren atención</option>
          </select>
          <div class="cat-actions">
            @if (canCreate) {
              <a class="primary" routerLink="/artist/releases/new">Publicar música</a>
            }
            <a routerLink="/catalog-review">Revisiones</a>
          </div>
        </div>

        @if (showReleases()) {
          <section class="cat-section" aria-label="Lanzamientos">
            <div class="cat-section__head">
              <h2 class="cat-section__title">Lanzamientos</h2>
              <a class="cat-section__link" routerLink="/artist/releases">Ver todos</a>
            </div>
            @if (!filteredReleases().length) {
              <p class="cat-empty">No encontramos contenido con estos filtros.</p>
            } @else {
              <ul class="cat-list">
                @for (r of filteredReleases(); track r.id) {
                  <li>
                    <a class="cat-row" [routerLink]="['/artist/releases', r.id]">
                      <div class="cat-cover" aria-hidden="true">
                        @if (coverUrl(r); as src) {
                          <img [src]="src" alt="" loading="lazy" (error)="onCoverError($event)" />
                        } @else {
                          <img
                            class="cat-cover__mark"
                            src="/assets/images/voxmetrik-icon.webp"
                            alt=""
                          />
                        }
                      </div>
                      <div>
                        <p class="cat-row__title">{{ displayTitle(r) }}</p>
                        <p class="cat-row__meta">
                          {{ releaseTypeLabel(r.release_type) }}
                          @if (r.genre) {
                            · {{ r.genre }}
                          }
                          @if (r.planned_release_date || r.published_at) {
                            · {{ formatDate(r.published_at || r.planned_release_date!) }}
                          }
                        </p>
                      </div>
                      <div class="cat-row__side">
                        <span class="cat-badge" [ngClass]="badgeClass(r.status)">{{
                          humanStatus(r.status)
                        }}</span>
                      </div>
                    </a>
                  </li>
                }
              </ul>
            }
          </section>
        }

        @if (showTracks()) {
          <section class="cat-section" aria-label="Canciones">
            <div class="cat-section__head">
              <h2 class="cat-section__title">Canciones</h2>
              <a class="cat-section__link" routerLink="/artist/tracks">Ver todas</a>
            </div>
            @if (!filteredTracks().length) {
              <p class="cat-empty">No encontramos contenido con estos filtros.</p>
            } @else {
              <ul class="cat-list">
                @for (row of filteredTracks(); track row.track.id) {
                  <li>
                    <a class="cat-row" [routerLink]="['/artist/releases', row.release.id]">
                      <div class="cat-cover" aria-hidden="true">
                        @if (coverUrl(row.release); as src) {
                          <img [src]="src" alt="" loading="lazy" (error)="onCoverError($event)" />
                        } @else {
                          <img
                            class="cat-cover__mark"
                            src="/assets/images/voxmetrik-icon.webp"
                            alt=""
                          />
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
            }
          </section>
        }

        @if (showArtists()) {
          <section class="cat-section" aria-label="Artistas">
            <div class="cat-section__head">
              <h2 class="cat-section__title">Artistas</h2>
              <a class="cat-section__link" routerLink="/artist-profiles">Ver todos</a>
            </div>
            @if (!filteredArtists().length) {
              <p class="cat-empty">No encontramos contenido con estos filtros.</p>
            } @else {
              <ul class="cat-list">
                @for (a of filteredArtists(); track a.id) {
                  <li>
                    <a class="cat-row" [routerLink]="['/artist-profiles', a.id]">
                      <div class="cat-cover" aria-hidden="true">
                        <span class="cat-artist-initial">{{ (artistLabel(a) || '?').charAt(0) }}</span>
                      </div>
                      <div>
                        <p class="cat-row__title">{{ artistLabel(a) }}</p>
                        <p class="cat-row__meta">
                          {{ humanArtistStatus(a.status) }}
                          @if (artistLegalLabel(a)) {
                            · {{ artistLegalLabel(a) }}
                          }
                        </p>
                      </div>
                      <div class="cat-row__side">
                        <span class="cat-badge">Abrir</span>
                      </div>
                    </a>
                  </li>
                }
              </ul>
            }
          </section>
        }
      }
    </div>
  `,
})
export class CatalogHubPage implements OnInit {
  private readonly orgCtx = inject(OrganizationContextService);
  private readonly api = inject(CatalogPublishingApiService);
  private readonly artistsApi = inject(ArtistsApiService);
  private readonly auth = inject(AuthService);
  private readonly access = catalogPublishingAccess();

  orgId: number | null = null;
  canCreate = false;
  query = '';
  filter: ViewFilter = 'all';

  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly releases = signal<ReleaseSubmission[]>([]);
  readonly tracks = signal<TrackPreview[]>([]);
  readonly artists = signal<ArtistProfile[]>([]);
  readonly summary = signal<PortalSummary | null>(null);
  readonly brokenCovers = signal<Record<number, true>>({});

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    this.canCreate = this.access.canCreate();
    if (this.orgId) this.load();
    else this.loading.set(false);
  }

  onQuery(): void {
    /* template bindings drive filtered* getters via signals + fields */
  }

  releaseCount(): number {
    return this.releases().length;
  }

  trackCount(): number {
    return this.tracks().length;
  }

  artistCount(): number {
    return this.artists().length;
  }

  attentionCount(): number {
    const counts = this.summary()?.status_counts;
    if (counts) {
      return Object.entries(counts).reduce((acc, [k, v]) => {
        const s = k.toLowerCase();
        if (
          s === 'submitted' ||
          s === 'under_review' ||
          s === 'changes_requested' ||
          publishingUiBucket(k) === 'in_review'
        ) {
          return acc + (v || 0);
        }
        return acc;
      }, 0);
    }
    return this.releases().filter((r) => {
      const b = publishingUiBucket(r.status);
      return b === 'in_review' || r.status === 'changes_requested';
    }).length;
  }

  showReleases(): boolean {
    return this.filter === 'all' || this.filter === 'releases' || this.filter === 'attention';
  }

  showTracks(): boolean {
    return this.filter === 'all' || this.filter === 'tracks';
  }

  showArtists(): boolean {
    return this.filter === 'all' || this.filter === 'artists';
  }

  filteredReleases(): ReleaseSubmission[] {
    let rows = this.releases();
    if (this.filter === 'attention') {
      rows = rows.filter((r) => publishingUiBucket(r.status) === 'in_review');
    }
    const q = this.query.trim().toLowerCase();
    if (!q) return rows.slice(0, 12);
    return rows
      .filter(
        (r) =>
          r.title.toLowerCase().includes(q) ||
          (r.genre || '').toLowerCase().includes(q) ||
          (r.label_name || '').toLowerCase().includes(q),
      )
      .slice(0, 12);
  }

  filteredTracks(): TrackPreview[] {
    const q = this.query.trim().toLowerCase();
    const rows = this.tracks();
    if (!q) return rows.slice(0, 12);
    return rows
      .filter(
        (row) =>
          row.track.title.toLowerCase().includes(q) ||
          row.release.title.toLowerCase().includes(q) ||
          (row.track.isrc || '').toLowerCase().includes(q),
      )
      .slice(0, 12);
  }

  filteredArtists(): ArtistProfile[] {
    const q = this.query.trim().toLowerCase();
    const rows = this.artists();
    if (!q) return rows.slice(0, 8);
    return rows
      .filter(
        (a) =>
          a.display_name.toLowerCase().includes(q) ||
          (a.legal_name || '').toLowerCase().includes(q),
      )
      .slice(0, 8);
  }

  coverUrl(r: ReleaseSubmission): string | null {
    const id = r.cover_media_id;
    if (!id || this.brokenCovers()[id]) return null;
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

  artistLabel(a: ArtistProfile): string {
    return productArtistDisplayName(a.display_name);
  }

  artistLegalLabel(a: ArtistProfile): string {
    return productArtistDisplayName(a.legal_name);
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

  humanArtistStatus(status: string): string {
    const s = (status || '').toLowerCase();
    if (s === 'active') return 'Activo';
    if (s === 'draft') return 'Borrador';
    if (s === 'inactive') return 'Inactivo';
    if (s === 'archived') return 'Archivado';
    return status || 'Sin datos';
  }

  releaseTypeLabel(type: string | null | undefined): string {
    const t = (type || '').toLowerCase();
    if (t === 'single') return 'Single';
    if (t === 'ep') return 'EP';
    if (t === 'album') return 'Álbum';
    if (t === 'compilation') return 'Compilación';
    return type || 'Lanzamiento';
  }

  formatDate(iso: string): string {
    const d = Date.parse(iso);
    if (Number.isNaN(d)) return iso.slice(0, 10);
    return new Date(d)
      .toLocaleDateString('es-ES', { year: 'numeric', month: 'short', day: 'numeric' })
      .replace(/\./g, '')
      .replace(/\s+/g, ' ')
      .trim();
  }

  load(): void {
    const orgId = this.orgId;
    if (!orgId) return;
    this.loading.set(true);
    this.error.set(null);

    forkJoin({
      summary: this.api.portalSummary(orgId),
      releases: this.api
        .listPortalReleases(orgId, { limit: 40 })
        .pipe(catchError(() => this.api.listReleases(orgId, { limit: 40 }))),
      artists: this.artistsApi.list(orgId, { page: 1, page_size: 24 }),
    })
      .pipe(
        switchMap((res) => {
          this.summary.set(res.summary);
          const releases = res.releases ?? [];
          this.releases.set(releases);
          this.artists.set(res.artists.items ?? []);

          const sample = releases.slice(0, 8);
          if (!sample.length) {
            return of([] as TrackPreview[]);
          }
          return forkJoin(
            sample.map((r) =>
              this.api.getRelease(orgId, r.id).pipe(
                map((detail) =>
                  (detail.tracks || []).map((t) => ({ track: t, release: detail.submission || r })),
                ),
              ),
            ),
          ).pipe(map((chunks) => chunks.flat()));
        }),
      )
      .subscribe({
        next: (tracks) => {
          this.tracks.set(tracks);
          this.loading.set(false);
        },
        error: () => {
          this.error.set('No se pudo cargar el catálogo.');
          this.loading.set(false);
        },
      });
  }
}
