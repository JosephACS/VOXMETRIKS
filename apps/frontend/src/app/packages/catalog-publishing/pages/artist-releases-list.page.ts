import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { catchError } from 'rxjs';
import { CatalogPublishingApiService } from '../services/catalog-publishing.api';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import {
  PortalSummary,
  ReleaseSubmission,
  displayReleaseTitle,
  humanReleaseStatus,
  publishingUiBucket,
} from '../models/catalog-publishing.models';
import { AuthService } from '../../../core/services/auth.service';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import { catalogPublishingAccess } from '../catalog-publishing-access';

@Component({
  selector: 'app-artist-releases-list',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, ...ENTERPRISE_UI_IMPORTS],
  styleUrls: ['../styles/catalog-editorial.css'],
  template: `
    <div class="vx-enterprise cat-page" data-testid="artist-releases-list">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <header class="cat-head">
          <p class="cat-kicker">Catálogo</p>
          <h1 class="cat-title">Lanzamientos</h1>
          <p class="cat-sub">Borradores, revisiones y lanzamientos publicados.</p>
        </header>

        <div class="cat-signals">
          <span class="cat-chip">Borrador <strong>{{ countDraft }}</strong></span>
          <span class="cat-chip">En revisión <strong>{{ countReview }}</strong></span>
          <span class="cat-chip">Publicado <strong>{{ countPublished }}</strong></span>
        </div>

        <div class="cat-toolbar">
          <input
            class="cat-search"
            type="search"
            [(ngModel)]="query"
            placeholder="Buscar lanzamiento"
            aria-label="Buscar lanzamiento"
          />
          <select class="cat-select" [(ngModel)]="statusFilter" aria-label="Estado">
            <option value="all">Todos los estados</option>
            <option value="draft">Borrador</option>
            <option value="in_review">En revisión</option>
            <option value="published">Publicado</option>
          </select>
          <div class="cat-actions">
            @if (canCreate) {
              <a class="primary" routerLink="/artist/releases/new">Publicar música</a>
            }
          </div>
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
              @for (r of filteredRows; track r.id) {
                <li>
                  <a class="cat-row" [routerLink]="['/artist/releases', r.id]">
                    <div class="cat-cover" aria-hidden="true">
                      @if (coverUrl(r); as src) {
                        <img [src]="src" alt="" loading="lazy" (error)="onCoverError($event)" />
                      } @else {
                        <img class="cat-cover__mark" src="/assets/brand/voxmetriks-mark.svg" alt="" />
                      }
                    </div>
                    <div>
                      <p class="cat-row__title">{{ displayTitle(r) }}</p>
                      <p class="cat-row__meta">
                        {{ releaseTypeLabel(r.release_type) }}
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
          </section>
        }
      }
    </div>
  `,
})
export class ArtistReleasesListPage implements OnInit {
  private api = inject(CatalogPublishingApiService);
  private orgCtx = inject(OrganizationContextService);
  private auth = inject(AuthService);
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
  query = '';
  statusFilter: 'all' | 'draft' | 'in_review' | 'published' = 'all';

  get filteredRows(): ReleaseSubmission[] {
    let rows = this.rows;
    if (this.statusFilter !== 'all') {
      rows = rows.filter((r) => publishingUiBucket(r.status) === this.statusFilter);
    }
    const q = this.query.trim().toLowerCase();
    if (!q) return rows;
    return rows.filter((r) => r.title.toLowerCase().includes(q));
  }

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

    this.api.portalSummary(this.orgId).subscribe({
      next: (s) => {
        this.summary = s;
        this.recomputeCounts();
      },
      error: () => {
        // Summary is secondary to the release list; keep counts at zero on failure.
        this.summary = null;
        this.recomputeCounts();
      },
    });

    this.api
      .listPortalReleases(this.orgId)
      .pipe(catchError(() => this.api.listReleases(this.orgId!)))
      .subscribe({
        next: (rows) => {
          this.rows = rows ?? [];
          this.recomputeCounts();
          this.loading = false;
        },
        error: () => {
          this.rows = [];
          this.loading = false;
          this.error = 'No se pudieron cargar los lanzamientos.';
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
      mark.src = '/assets/brand/voxmetriks-mark.svg';
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

  releaseTypeLabel(type: string | null | undefined): string {
    const t = (type || '').toLowerCase();
    if (t === 'single') return 'Single';
    if (t === 'ep') return 'EP';
    if (t === 'album') return 'Álbum';
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
}
