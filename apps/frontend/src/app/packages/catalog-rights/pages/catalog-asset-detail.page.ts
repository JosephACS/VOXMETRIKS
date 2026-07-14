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
@Component({
  selector: 'app-catalog-asset-detail',
  standalone: true,
  imports: [CommonModule, RouterLink, ReactiveFormsModule, TranslatePipe],
  template: `
    <div class="vx-enterprise catalog-asset-detail-page">
      <a routerLink="/catalog-rights/assets">&larr; Back to assets</a>

      @if (asset) {
        <h1>{{ asset.title }}</h1>
        <div class="profile-card">
          <div class="field"><label>Status</label>
            <span class="badge" [class]="'badge--' + asset.status">{{ asset.status }}</span>
          </div>
          <div class="field"><label>Warehouse Track Link</label>
            @if (asset.warehouse_track_id) {
              <span class="badge badge--linked">Linked to track #{{ asset.warehouse_track_id }}</span>
            } @else {
              <span class="badge badge--unlinked">Not linked</span>
            }
          </div>
        </div>

        <div class="actions">
          <a class="btn btn--secondary" [routerLink]="['/catalog-rights/contracts']" [queryParams]="{ asset_id: asset.id }">
            View {{ 'catalogRights.contracts.title' | t:lang() }}
          </a>
        </div>

        <section class="link-warehouse">
          <h2>Link Warehouse Track</h2>
          <p class="hint">Optional reference only — this does not copy or duplicate dim_track data.</p>
          <form [formGroup]="warehouseForm" (ngSubmit)="linkWarehouse()">
            <input formControlName="warehouse_track_id" type="number" placeholder="Warehouse track id" class="input" />
            <button type="submit" class="btn btn--secondary" [disabled]="warehouseForm.invalid">Link</button>
          </form>
        </section>

        <section class="artists">
          <h2>Artists</h2>
          @if (artists.length === 0) {
            <p>No artists linked yet.</p>
          } @else {
            <ul>
              @for (a of artists; track a.id) {
                <li>Artist profile #{{ a.artist_profile_id }} — {{ a.role }}</li>
              }
            </ul>
          }
          <form [formGroup]="artistForm" (ngSubmit)="linkArtist()">
            <input formControlName="artist_profile_id" type="number" placeholder="Artist profile id" class="input" />
            <input formControlName="role" placeholder="Role (e.g. primary, featured)" class="input" />
            <button type="submit" class="btn btn--secondary" [disabled]="artistForm.invalid">Link Artist</button>
          </form>
        </section>

        <section class="ownership">
          <h2>Ownership</h2>
          @if (ownership.length === 0) {
            <p>No ownership records yet.</p>
          } @else {
            <ul>
              @for (o of ownership; track o.id) {
                <li>
                  {{ o.ownership_type }} —
                  @if (o.organization_id) { org #{{ o.organization_id }} }
                  @if (o.artist_profile_id) { artist #{{ o.artist_profile_id }} }
                </li>
              }
            </ul>
          }
          <form [formGroup]="ownershipForm" (ngSubmit)="registerOwnership()">
            <select formControlName="ownership_type" class="input">
              <option value="label">Label</option>
              <option value="artist">Artist</option>
              <option value="publisher">Publisher</option>
              <option value="other">Other</option>
            </select>
            <input formControlName="owner_organization_id" type="number" placeholder="Owner org id (optional)" class="input" />
            <input formControlName="artist_profile_id" type="number" placeholder="Artist profile id (optional)" class="input" />
            <button type="submit" class="btn btn--secondary">Register Ownership</button>
          </form>
        </section>

        <section class="coverage">
          <h2>Rights Coverage</h2>
          <p class="hint">
            Percentage totals are computed per rights type + territory + overlapping period —
            not a single global sum for the whole asset.
          </p>
          <form [formGroup]="coverageForm" (ngSubmit)="loadCoverage()">
            <select formControlName="rights_type" class="input">
              <option value="">All rights types</option>
              <option value="master">Master</option>
              <option value="publishing">Publishing</option>
              <option value="neighboring">Neighboring</option>
              <option value="other">Other</option>
            </select>
            <button type="submit" class="btn btn--secondary">Query Coverage</button>
          </form>
          @if (coverage.length > 0) {
            <table class="data-table">
              <thead>
                <tr><th>Rights Type</th><th>Territory</th><th>Total %</th><th>Contracts</th><th>Conflict</th></tr>
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
                        <span class="badge badge--danger">Conflict</span>
                      } @else {
                        <span class="badge badge--ok">OK</span>
                      }
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          }
        </section>

        <section class="overlap">
          <h2>Detect Overlap</h2>
          <form [formGroup]="overlapForm" (ngSubmit)="detectOverlap()">
            <select formControlName="rights_type" class="input">
              <option value="master">Master</option>
              <option value="publishing">Publishing</option>
              <option value="neighboring">Neighboring</option>
              <option value="other">Other</option>
            </select>
            <button type="submit" class="btn btn--danger">Run Overlap Detection</button>
          </form>
          @if (overlapResult) {
            @if (overlapResult.length === 0) {
              <p>No conflicts detected.</p>
            } @else {
              <p>{{ overlapResult.length }} conflict(s) opened. See <a routerLink="/catalog-rights/conflicts">Conflicts</a>.</p>
            }
          }
        </section>
      } @else if (loading) {
        <p>{{ 'common.loading' | t:lang() }}</p>
      }

      @if (error) {
        <p class="error">{{ error }}</p>
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

  private get orgId(): number {
    return this.orgCtx.activeOrganization()?.id ?? 0;
  }

  private get assetId(): number {
    return Number(this.route.snapshot.paramMap.get('id'));
  }

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading = true;
    this.api.getAsset(this.orgId, this.assetId).subscribe({
      next: (a) => {
        this.asset = a;
        this.loading = false;
        this.loadArtists();
        this.loadOwnership();
      },
      error: (e) => {
        this.loading = false;
        this.error = e.error?.message ?? 'Error loading catalog asset';
      },
    });
  }

  loadArtists(): void {
    this.api.listAssetArtists(this.orgId, this.assetId).subscribe({
      next: (items) => (this.artists = items),
      error: () => (this.artists = []),
    });
  }

  loadOwnership(): void {
    this.api.listOwnership(this.orgId, this.assetId).subscribe({
      next: (items) => (this.ownership = items),
      error: () => (this.ownership = []),
    });
  }

  linkWarehouse(): void {
    if (this.warehouseForm.invalid) return;
    const id = Number(this.warehouseForm.value.warehouse_track_id);
    this.api.linkWarehouseTrack(this.orgId, this.assetId, id).subscribe({
      next: (a) => {
        this.asset = a;
        this.warehouseForm.reset();
      },
      error: (e) => (this.error = e.error?.message ?? 'Error linking warehouse track'),
    });
  }

  linkArtist(): void {
    if (this.artistForm.invalid) return;
    const value = this.artistForm.value;
    this.api
      .linkAssetArtist(this.orgId, this.assetId, Number(value.artist_profile_id), value.role || 'primary')
      .subscribe({
        next: () => {
          this.artistForm.reset({ role: 'primary' });
          this.loadArtists();
        },
        error: (e) => (this.error = e.error?.message ?? 'Error linking artist'),
      });
  }

  registerOwnership(): void {
    const value = this.ownershipForm.value;
    this.api
      .registerOwnership(this.orgId, this.assetId, {
        ownership_type: value.ownership_type || 'label',
        owner_organization_id: value.owner_organization_id || null,
        artist_profile_id: value.artist_profile_id || null,
      })
      .subscribe({
        next: () => {
          this.ownershipForm.reset({ ownership_type: 'label' });
          this.loadOwnership();
        },
        error: (e) => (this.error = e.error?.message ?? 'Error registering ownership'),
      });
  }

  loadCoverage(): void {
    const rightsType = this.coverageForm.value.rights_type || undefined;
    this.api.queryCoverage(this.orgId, this.assetId, rightsType).subscribe({
      next: (rows) => (this.coverage = rows),
      error: (e) => (this.error = e.error?.message ?? 'Error loading coverage'),
    });
  }

  detectOverlap(): void {
    const rightsType = this.overlapForm.value.rights_type || 'master';
    this.api.detectOverlap(this.orgId, this.assetId, rightsType).subscribe({
      next: (conflicts) => (this.overlapResult = conflicts),
      error: (e) => (this.error = e.error?.message ?? 'Error detecting overlap'),
    });
  }
}
