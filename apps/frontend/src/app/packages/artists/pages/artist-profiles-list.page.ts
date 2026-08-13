import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { ArtistsApiService } from '../services/artists-api.service';
import { ArtistProfile } from '../models/artist.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { StatusLabelPipe } from '../../../shared/pipes/status-label.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import { productArtistDisplayName } from '../../../shared/utils/product-presentation.util';

@Component({
  selector: 'app-artist-profiles-list',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    ReactiveFormsModule,
    TranslatePipe,
    StatusLabelPipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  template: `
    <div class="vx-enterprise artist-profiles-list-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <app-enterprise-page-header
          [title]="'artists.list.title' | t:lang()"
          [subtitle]="'artists.list.subtitle' | t:lang()"
        />

        <app-enterprise-action-bar>
          <app-enterprise-form-field [label]="'common.status' | t:lang()">
            <select class="input" [value]="statusFilter" (change)="onStatusChange($event)">
              <option value="">{{ 'common.all' | t:lang() }}</option>
              <option value="draft">{{ 'draft' | statusLabel }}</option>
              <option value="active">{{ 'active' | statusLabel }}</option>
              <option value="inactive">{{ 'inactive' | statusLabel }}</option>
              <option value="archived">{{ 'archived' | statusLabel }}</option>
            </select>
          </app-enterprise-form-field>
        </app-enterprise-action-bar>

        <app-enterprise-section-card [title]="'artists.list.create' | t:lang()">
          <form [formGroup]="createForm" (ngSubmit)="createArtist()" class="form-grid">
            <app-enterprise-form-field
              [label]="'artists.list.displayName' | t:lang()"
              [required]="true"
            >
              <input formControlName="display_name" class="input" />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'artists.list.legalName' | t:lang()">
              <input formControlName="legal_name" class="input" />
            </app-enterprise-form-field>
            <div class="form-grid__actions">
              <button type="submit" class="btn btn--primary" [disabled]="createForm.invalid">
                {{ 'artists.list.create' | t:lang() }}
              </button>
            </div>
          </form>
        </app-enterprise-section-card>

        @if (error) {
          <app-enterprise-error-state [message]="error" (retry)="load()" />
        } @else if (loading) {
          <app-enterprise-loading-skeleton [rows]="3" />
        } @else if (artists.length === 0) {
          <app-enterprise-empty-state
            [title]="'artists.list.emptyTitle' | t:lang()"
            [description]="'artists.list.emptyBody' | t:lang()"
            [ctaLabel]="'artists.list.create' | t:lang()"
          />
        } @else {
          <div class="artist-row-list">
            @for (artist of artists; track artist.id) {
              <a [routerLink]="['/artist-profiles', artist.id]" class="artist-row">
                <div class="artist-row__avatar" aria-hidden="true">
                  <span>{{ artistLabel(artist).charAt(0) || '?' }}</span>
                </div>
                <div class="artist-row__body">
                  <strong>{{ artistLabel(artist) }}</strong>
                  <span class="muted">
                    {{ artist.status | statusLabel }}
                    @if (artist.warehouse_artist_id) {
                      · {{ 'artists.list.linked' | t:lang() }}
                    } @else {
                      · {{ 'artists.list.notLinked' | t:lang() }}
                    }
                  </span>
                </div>
              </a>
            }
          </div>
          <p class="muted">{{ 'artists.list.total' | t:lang() }}: {{ total }}</p>
        }
      }
    </div>
  `,
  styles: [
    `
      .artist-row-list {
        display: grid;
        gap: 0;
      }
      .artist-row {
        display: grid;
        grid-template-columns: 48px minmax(0, 1fr);
        gap: 0.75rem;
        align-items: center;
        padding: 0.7rem 0;
        border-top: 1px solid var(--vx-border-subtle, var(--border, rgba(255, 255, 255, 0.08)));
        text-decoration: none;
        color: inherit;
      }
      .artist-row:first-child {
        border-top: 0;
        padding-top: 0;
      }
      .artist-row__avatar {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        display: grid;
        place-items: center;
        background: color-mix(in srgb, var(--vx-accent, #1ed896) 16%, transparent);
        color: var(--vx-accent, #1ed896);
        font-weight: 700;
      }
      .artist-row__body {
        display: grid;
        gap: 0.15rem;
      }
      .artist-row__body strong {
        font-size: 0.95rem;
      }
      .artist-row__body .muted {
        font-size: 0.78rem;
        color: var(--vx-text-secondary, var(--color-text-muted, rgba(255, 255, 255, 0.5)));
      }
    `,
  ],
})
export class ArtistProfilesListPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(ArtistsApiService);
  private fb = inject(FormBuilder);
  private orgCtx = inject(OrganizationContextService);

  artists: ArtistProfile[] = [];
  total = 0;
  loading = false;
  error: string | null = null;
  statusFilter = '';
  orgId: number | null = null;

  createForm = this.fb.group({
    display_name: ['', [Validators.required]],
    legal_name: [''],
  });

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    if (!this.orgId) return;
    this.load();
  }

  onStatusChange(event: Event): void {
    this.statusFilter = (event.target as HTMLSelectElement).value;
    this.load();
  }

  artistLabel(artist: ArtistProfile): string {
    return productArtistDisplayName(artist.display_name);
  }

  load(): void {
    const id = this.orgCtx.organizationId() ?? 0;
    this.orgId = id || null;
    if (!this.orgId) return;
    this.loading = true;
    this.api.list(this.orgId, { status: this.statusFilter || undefined }).subscribe({
      next: (res) => {
        this.artists = res.items;
        this.total = res.total;
        this.loading = false;
        this.error = null;
      },
      error: (e) => {
        this.loading = false;
        this.error = e.error?.message ?? this.i18n.t('common.failed');
      },
    });
  }

  createArtist(): void {
    if (this.createForm.invalid || !this.orgId) return;
    const value = this.createForm.value;
    this.api
      .create(this.orgId, {
        display_name: value.display_name!,
        legal_name: value.legal_name || null,
      })
      .subscribe({
        next: () => {
          this.createForm.reset();
          this.load();
        },
        error: (e) => (this.error = e.error?.message ?? this.i18n.t('common.failed')),
      });
  }
}
