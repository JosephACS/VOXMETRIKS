import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { ArtistsApiService } from '../services/artists-api.service';
import { ArtistOrganizationLink, ArtistProfile } from '../models/artist.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-artist-profile-detail',
  standalone: true,
  imports: [CommonModule, RouterLink, ReactiveFormsModule, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise artist-profile-detail-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else if (loading) {
        <app-enterprise-loading-skeleton [rows]="5" />
      } @else if (artist) {
        <a routerLink="/artist-profiles" class="back-link">{{ 'artists.detail.back' | t:lang() }}</a>

        <app-enterprise-page-header [title]="artist.display_name">
          <app-enterprise-status-badge [status]="artist.status" />
        </app-enterprise-page-header>

        <app-enterprise-section-card [title]="'common.details' | t:lang()">
          <dl class="meta">
            <dt>{{ 'billing.profile.legalName' | t:lang() }}</dt>
            <dd>{{ artist.legal_name ?? '—' }}</dd>
            <dt>{{ 'artists.detail.normalizedName' | t:lang() }}</dt>
            <dd>{{ artist.normalized_name }}</dd>
            <dt>{{ 'artists.detail.warehouseLink' | t:lang() }}</dt>
            <dd>
              @if (artist.warehouse_artist_id) {
                <span class="badge badge--linked">
                  {{ 'artists.detail.linked' | t:lang() }} #{{ artist.warehouse_artist_id }}
                </span>
              } @else {
                <span class="badge badge--unlinked">{{ 'artists.detail.notLinked' | t:lang() }}</span>
              }
            </dd>
          </dl>
        </app-enterprise-section-card>

        <app-enterprise-action-bar>
          @if (artist.status === 'draft' || artist.status === 'inactive') {
            <button class="btn btn--primary" (click)="activate()">
              {{ 'artists.detail.activate' | t:lang() }}
            </button>
          }
          @if (artist.status === 'active') {
            <button class="btn btn--secondary" (click)="deactivate()">
              {{ 'artists.detail.deactivate' | t:lang() }}
            </button>
          }
          @if (artist.status !== 'archived') {
            <button class="btn btn--danger" (click)="archive()">
              {{ 'artists.detail.archive' | t:lang() }}
            </button>
          }
          <a class="btn btn--secondary" [routerLink]="['/artist-profiles', artist.id, 'team']">
            {{ 'artists.detail.team' | t:lang() }}
          </a>
          <a class="btn btn--secondary" [routerLink]="['/artist-profiles', artist.id, 'history']">
            {{ 'artists.detail.viewHistory' | t:lang() }}
          </a>
        </app-enterprise-action-bar>

        <app-enterprise-section-card [title]="'artists.detail.warehouseLink' | t:lang()">
          <form [formGroup]="warehouseForm" (ngSubmit)="linkWarehouse()" class="form-grid">
            <app-enterprise-form-field [label]="'artists.detail.catalogArtistId' | t:lang()" [required]="true">
              <input formControlName="warehouse_artist_id" type="number" class="input" />
            </app-enterprise-form-field>
            <div class="form-grid__actions">
              <button type="submit" class="btn btn--secondary" [disabled]="warehouseForm.invalid">
                {{ 'artists.detail.link' | t:lang() }}
              </button>
            </div>
          </form>
        </app-enterprise-section-card>

        <app-enterprise-section-card [title]="'artists.detail.transferOrg' | t:lang()">
          <form [formGroup]="transferForm" (ngSubmit)="transfer()" class="form-grid">
            <app-enterprise-form-field [label]="'artists.detail.targetOrgId' | t:lang()" [required]="true">
              <input formControlName="target_organization_id" type="number" class="input" />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'common.reason' | t:lang()">
              <input formControlName="reason" class="input" />
            </app-enterprise-form-field>
            <div class="form-grid__actions">
              <button type="submit" class="btn btn--danger" [disabled]="transferForm.invalid">
                {{ 'artists.detail.transfer' | t:lang() }}
              </button>
            </div>
          </form>
        </app-enterprise-section-card>

        <app-enterprise-section-card [title]="'artists.detail.orgLinks' | t:lang()">
          @if (orgLinks.length === 0) {
            <p class="muted">{{ 'artists.detail.noOrgLinks' | t:lang() }}</p>
          } @else {
            <ul class="ent-list">
              @for (link of orgLinks; track link.id) {
                <li>
                  Org #{{ link.organization_id }} — {{ link.relationship_role }}
                  ({{ link.is_primary ? ('artists.detail.primary' | t:lang()) : ('artists.detail.secondary' | t:lang()) }})
                  — <app-enterprise-status-badge [status]="link.status" />
                </li>
              }
            </ul>
          }
        </app-enterprise-section-card>
      }

      @if (error) {
        <app-enterprise-error-state [message]="error" (retry)="load()" />
      }
    </div>
  `,
})
export class ArtistProfileDetailPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(ArtistsApiService);
  private route = inject(ActivatedRoute);
  private fb = inject(FormBuilder);
  private orgCtx = inject(OrganizationContextService);

  artist: ArtistProfile | null = null;
  orgLinks: ArtistOrganizationLink[] = [];
  loading = false;
  error: string | null = null;
  orgId: number | null = null;

  warehouseForm = this.fb.group({
    warehouse_artist_id: [null as number | null, [Validators.required]],
  });

  transferForm = this.fb.group({
    target_organization_id: [null as number | null, [Validators.required]],
    reason: [''],
  });

  private get artistId(): number {
    return Number(this.route.snapshot.paramMap.get('id'));
  }

  ngOnInit(): void {
    this.orgId = this.orgCtx.activeOrganization()?.id ?? null;
    if (this.orgId) this.load();
  }

  load(): void {
    const orgId = this.orgId;
    if (!orgId) return;
    this.loading = true;
    this.error = null;
    this.api.get(orgId, this.artistId).subscribe({
      next: (a) => {
        this.artist = a;
        this.loading = false;
        this.loadOrgLinks();
      },
      error: (e) => {
        this.loading = false;
        this.error = e.error?.message ?? this.i18n.t('common.failed');
      },
    });
  }

  loadOrgLinks(): void {
    const orgId = this.orgId;
    if (!orgId) return;
    this.api.listOrganizations(orgId, this.artistId).subscribe({
      next: (links) => (this.orgLinks = links),
      error: () => (this.orgLinks = []),
    });
  }

  activate(): void {
    const orgId = this.orgId;
    if (!orgId) return;
    this.api.activate(orgId, this.artistId).subscribe({
      next: (a) => (this.artist = a),
      error: (e) => (this.error = e.error?.message ?? this.i18n.t('common.failed')),
    });
  }

  deactivate(): void {
    const orgId = this.orgId;
    if (!orgId) return;
    this.api.deactivate(orgId, this.artistId).subscribe({
      next: (a) => (this.artist = a),
      error: (e) => (this.error = e.error?.message ?? this.i18n.t('common.failed')),
    });
  }

  archive(): void {
    const orgId = this.orgId;
    if (!orgId) return;
    this.api.archive(orgId, this.artistId).subscribe({
      next: (a) => (this.artist = a),
      error: (e) => (this.error = e.error?.message ?? this.i18n.t('common.failed')),
    });
  }

  linkWarehouse(): void {
    const orgId = this.orgId;
    if (!orgId || this.warehouseForm.invalid) return;
    const id = Number(this.warehouseForm.value.warehouse_artist_id);
    this.api.linkWarehouseArtist(orgId, this.artistId, id).subscribe({
      next: (a) => {
        this.artist = a;
        this.warehouseForm.reset();
      },
      error: (e) => (this.error = e.error?.message ?? this.i18n.t('common.failed')),
    });
  }

  transfer(): void {
    const orgId = this.orgId;
    if (!orgId || this.transferForm.invalid) return;
    const value = this.transferForm.value;
    this.api
      .transferOrganization(orgId, this.artistId, Number(value.target_organization_id), value.reason || undefined)
      .subscribe({
        next: (a) => {
          this.artist = a;
          this.transferForm.reset();
          this.loadOrgLinks();
        },
        error: (e) => (this.error = e.error?.message ?? this.i18n.t('common.failed')),
      });
  }
}
