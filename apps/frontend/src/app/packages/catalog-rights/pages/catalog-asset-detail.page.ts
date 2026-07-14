import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { CatalogRightsApiService } from '../services/catalog-rights-api.service';
import {
  CatalogAsset,
  CatalogAssetArtist,
  CatalogOwnership,
  RightsCoverageRow,
} from '../models/catalog-rights.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-catalog-asset-detail',
  standalone: true,
  imports: [CommonModule, RouterLink, ReactiveFormsModule, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise catalog-asset-detail-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else if (loading) {
        <app-enterprise-loading-skeleton [rows]="6" />
      } @else if (asset) {
        <a routerLink="/catalog-rights/assets" class="back-link">
          {{ 'catalogRights.assetDetail.back' | t:lang() }}
        </a>

        <app-enterprise-page-header [title]="asset.title">
          <app-enterprise-status-badge [status]="asset.status" />
        </app-enterprise-page-header>

        <app-enterprise-section-card [title]="'common.details' | t:lang()">
          <dl class="meta">
            <dt>{{ 'catalogRights.assets.warehouseLink' | t:lang() }}</dt>
            <dd>
              @if (asset.warehouse_track_id) {
                <span class="badge badge--linked">
                  {{ 'catalogRights.assets.linked' | t:lang() }} #{{ asset.warehouse_track_id }}
                </span>
              } @else {
                <span class="badge badge--unlinked">{{ 'catalogRights.assets.notLinked' | t:lang() }}</span>
              }
            </dd>
          </dl>
        </app-enterprise-section-card>

        <app-enterprise-action-bar>
          <a
            class="btn btn--secondary"
            [routerLink]="['/catalog-rights/contracts']"
            [queryParams]="{ asset_id: asset.id }"
          >
            {{ 'catalogRights.contracts.title' | t:lang() }}
          </a>
        </app-enterprise-action-bar>

        <app-enterprise-section-card [title]="'catalogRights.assetDetail.linkTrack' | t:lang()">
          <p class="hint muted">{{ 'catalogRights.assetDetail.linkTrackHint' | t:lang() }}</p>
          <form [formGroup]="warehouseForm" (ngSubmit)="linkWarehouse()" class="form-grid">
            <app-enterprise-form-field [label]="'catalogRights.assets.warehouseTrack' | t:lang()" [required]="true">
              <input formControlName="warehouse_track_id" type="number" class="input" />
            </app-enterprise-form-field>
            <div class="form-grid__actions">
              <button type="submit" class="btn btn--secondary" [disabled]="warehouseForm.invalid">
                {{ 'catalogRights.assetDetail.link' | t:lang() }}
              </button>
            </div>
          </form>
        </app-enterprise-section-card>

        <app-enterprise-section-card [title]="'catalogRights.assetDetail.artists' | t:lang()">
          @if (artists.length === 0) {
            <p class="muted">{{ 'catalogRights.assetDetail.noArtists' | t:lang() }}</p>
          } @else {
            <ul class="ent-list">
              @for (a of artists; track a.id) {
                <li>Artist profile #{{ a.artist_profile_id }} — {{ a.role }}</li>
              }
            </ul>
          }
          <form [formGroup]="artistForm" (ngSubmit)="linkArtist()" class="form-grid">
            <app-enterprise-form-field [label]="'catalogRights.assets.artistProfile' | t:lang()" [required]="true">
              <input formControlName="artist_profile_id" type="number" class="input" />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'common.role' | t:lang()">
              <input formControlName="role" class="input" />
            </app-enterprise-form-field>
            <div class="form-grid__actions">
              <button type="submit" class="btn btn--secondary" [disabled]="artistForm.invalid">
                {{ 'catalogRights.assetDetail.linkArtist' | t:lang() }}
              </button>
            </div>
          </form>
        </app-enterprise-section-card>

        <app-enterprise-section-card [title]="'catalogRights.assetDetail.ownership' | t:lang()">
          @if (ownership.length === 0) {
            <p class="muted">{{ 'catalogRights.assetDetail.noOwnership' | t:lang() }}</p>
          } @else {
            <ul class="ent-list">
              @for (o of ownership; track o.id) {
                <li>
                  {{ o.ownership_type }} —
                  @if (o.organization_id) { org #{{ o.organization_id }} }
                  @if (o.artist_profile_id) { artist #{{ o.artist_profile_id }} }
                </li>
              }
            </ul>
          }
          <form [formGroup]="ownershipForm" (ngSubmit)="registerOwnership()" class="form-grid">
            <app-enterprise-form-field [label]="'common.type' | t:lang()">
              <select formControlName="ownership_type" class="input">
                <option value="label">{{ 'catalogRights.ownershipType.label' | t:lang() }}</option>
                <option value="artist">{{ 'catalogRights.assetDetail.artists' | t:lang() }}</option>
                <option value="publisher">{{ 'catalogRights.ownershipType.publisher' | t:lang() }}</option>
                <option value="other">{{ 'catalogRights.rightsType.other' | t:lang() }}</option>
              </select>
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'catalogRights.assetDetail.ownerOrgId' | t:lang()">
              <input formControlName="owner_organization_id" type="number" class="input" />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'catalogRights.assets.artistProfile' | t:lang()">
              <input formControlName="artist_profile_id" type="number" class="input" />
            </app-enterprise-form-field>
            <div class="form-grid__actions">
              <button type="submit" class="btn btn--secondary">
                {{ 'catalogRights.assetDetail.ownership' | t:lang() }}
              </button>
            </div>
          </form>
        </app-enterprise-section-card>

        <app-enterprise-section-card [title]="'catalogRights.assetDetail.coverage' | t:lang()">
          <p class="hint muted">{{ 'catalogRights.assetDetail.coverageHint' | t:lang() }}</p>
          <form [formGroup]="coverageForm" (ngSubmit)="loadCoverage()" class="form-grid">
            <app-enterprise-form-field [label]="'catalogRights.contracts.rightsType' | t:lang()">
              <select formControlName="rights_type" class="input">
                <option value="">{{ 'catalogRights.assetDetail.allRightsTypes' | t:lang() }}</option>
                <option value="master">{{ 'catalogRights.rightsType.master' | t:lang() }}</option>
                <option value="publishing">{{ 'catalogRights.rightsType.publishing' | t:lang() }}</option>
                <option value="neighboring">{{ 'catalogRights.rightsType.neighboring' | t:lang() }}</option>
                <option value="other">{{ 'catalogRights.rightsType.other' | t:lang() }}</option>
              </select>
            </app-enterprise-form-field>
            <div class="form-grid__actions">
              <button type="submit" class="btn btn--secondary">
                {{ 'catalogRights.assetDetail.queryCoverage' | t:lang() }}
              </button>
            </div>
          </form>
          @if (coverage.length > 0) {
            <app-enterprise-data-table>
              <table class="data-table">
                <thead>
                  <tr>
                    <th>{{ 'catalogRights.contracts.rightsType' | t:lang() }}</th>
                    <th>{{ 'catalogRights.conflicts.territory' | t:lang() }}</th>
                    <th>{{ 'catalogRights.assetDetail.totalPct' | t:lang() }}</th>
                    <th>{{ 'catalogRights.contracts.title' | t:lang() }}</th>
                    <th>{{ 'catalogRights.assetDetail.conflict' | t:lang() }}</th>
                  </tr>
                </thead>
                <tbody>
                  @for (row of coverage; track row.rights_type + row.territory_code) {
                    <tr>
                      <td>{{ row.rights_type }}</td>
                      <td>{{ row.territory_code }}</td>
                      <td>{{ row.total_percentage }}%</td>
                      <td>{{ row.contract_count }}</td>
                      <td>
                        @if (row.has_conflict) {
                          <span class="badge badge--danger">{{ 'catalogRights.assetDetail.conflict' | t:lang() }}</span>
                        } @else {
                          <span class="badge badge--ok">OK</span>
                        }
                      </td>
                    </tr>
                  }
                </tbody>
              </table>
            </app-enterprise-data-table>
          }
        </app-enterprise-section-card>

        <app-enterprise-section-card [title]="'catalogRights.assetDetail.overlap' | t:lang()">
          <form [formGroup]="overlapForm" (ngSubmit)="detectOverlap()" class="form-grid">
            <app-enterprise-form-field [label]="'catalogRights.contracts.rightsType' | t:lang()">
              <select formControlName="rights_type" class="input">
                <option value="master">{{ 'catalogRights.rightsType.master' | t:lang() }}</option>
                <option value="publishing">{{ 'catalogRights.rightsType.publishing' | t:lang() }}</option>
                <option value="neighboring">{{ 'catalogRights.rightsType.neighboring' | t:lang() }}</option>
                <option value="other">{{ 'catalogRights.rightsType.other' | t:lang() }}</option>
              </select>
            </app-enterprise-form-field>
            <div class="form-grid__actions">
              <button type="submit" class="btn btn--danger">
                {{ 'catalogRights.assetDetail.runOverlap' | t:lang() }}
              </button>
            </div>
          </form>
          @if (overlapResult) {
            @if (overlapResult.length === 0) {
              <p class="muted">{{ 'catalogRights.assetDetail.noConflicts' | t:lang() }}</p>
            } @else {
              <p>
                {{ 'catalogRights.assetDetail.conflictsOpened' | t:{ count: overlapResult.length }:lang() }}
                <a routerLink="/catalog-rights/conflicts">{{ 'catalogRights.conflicts.title' | t:lang() }}</a>.
              </p>
            }
          }
        </app-enterprise-section-card>
      }

      @if (error) {
        <app-enterprise-error-state [message]="error" (retry)="load()" />
      }
    </div>
  `,
})
export class CatalogAssetDetailPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(CatalogRightsApiService);
  private route = inject(ActivatedRoute);
  private fb = inject(FormBuilder);
  private orgCtx = inject(OrganizationContextService);

  asset: CatalogAsset | null = null;
  artists: CatalogAssetArtist[] = [];
  ownership: CatalogOwnership[] = [];
  coverage: RightsCoverageRow[] = [];
  overlapResult: unknown[] | null = null;
  loading = false;
  error: string | null = null;
  orgId: number | null = null;

  warehouseForm = this.fb.group({
    warehouse_track_id: [null as number | null, [Validators.required]],
  });

  artistForm = this.fb.group({
    artist_profile_id: [null as number | null, [Validators.required]],
    role: ['primary'],
  });

  ownershipForm = this.fb.group({
    ownership_type: ['label'],
    owner_organization_id: [null as number | null],
    artist_profile_id: [null as number | null],
  });

  coverageForm = this.fb.group({
    rights_type: [''],
  });

  overlapForm = this.fb.group({
    rights_type: ['master'],
  });

  private get assetId(): number {
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
    this.api.getAsset(orgId, this.assetId).subscribe({
      next: (a) => {
        this.asset = a;
        this.loading = false;
        this.loadArtists();
        this.loadOwnership();
      },
      error: (e) => {
        this.loading = false;
        this.error = e.error?.message ?? this.i18n.t('common.failed');
      },
    });
  }

  loadArtists(): void {
    const orgId = this.orgId;
    if (!orgId) return;
    this.api.listAssetArtists(orgId, this.assetId).subscribe({
      next: (items) => (this.artists = items),
      error: () => (this.artists = []),
    });
  }

  loadOwnership(): void {
    const orgId = this.orgId;
    if (!orgId) return;
    this.api.listOwnership(orgId, this.assetId).subscribe({
      next: (items) => (this.ownership = items),
      error: () => (this.ownership = []),
    });
  }

  linkWarehouse(): void {
    const orgId = this.orgId;
    if (!orgId || this.warehouseForm.invalid) return;
    const id = Number(this.warehouseForm.value.warehouse_track_id);
    this.api.linkWarehouseTrack(orgId, this.assetId, id).subscribe({
      next: (a) => {
        this.asset = a;
        this.warehouseForm.reset();
      },
      error: (e) => (this.error = e.error?.message ?? this.i18n.t('common.failed')),
    });
  }

  linkArtist(): void {
    const orgId = this.orgId;
    if (!orgId || this.artistForm.invalid) return;
    const value = this.artistForm.value;
    this.api
      .linkAssetArtist(orgId, this.assetId, Number(value.artist_profile_id), value.role || 'primary')
      .subscribe({
        next: () => {
          this.artistForm.reset({ role: 'primary' });
          this.loadArtists();
        },
        error: (e) => (this.error = e.error?.message ?? this.i18n.t('common.failed')),
      });
  }

  registerOwnership(): void {
    const orgId = this.orgId;
    if (!orgId) return;
    const value = this.ownershipForm.value;
    this.api
      .registerOwnership(orgId, this.assetId, {
        ownership_type: value.ownership_type || 'label',
        owner_organization_id: value.owner_organization_id || null,
        artist_profile_id: value.artist_profile_id || null,
      })
      .subscribe({
        next: () => {
          this.ownershipForm.reset({ ownership_type: 'label' });
          this.loadOwnership();
        },
        error: (e) => (this.error = e.error?.message ?? this.i18n.t('common.failed')),
      });
  }

  loadCoverage(): void {
    const orgId = this.orgId;
    if (!orgId) return;
    const rightsType = this.coverageForm.value.rights_type || undefined;
    this.api.queryCoverage(orgId, this.assetId, rightsType).subscribe({
      next: (rows) => (this.coverage = rows),
      error: (e) => (this.error = e.error?.message ?? this.i18n.t('common.failed')),
    });
  }

  detectOverlap(): void {
    const orgId = this.orgId;
    if (!orgId) return;
    const rightsType = this.overlapForm.value.rights_type || 'master';
    this.api.detectOverlap(orgId, this.assetId, rightsType).subscribe({
      next: (conflicts) => (this.overlapResult = conflicts),
      error: (e) => (this.error = e.error?.message ?? this.i18n.t('common.failed')),
    });
  }
}
