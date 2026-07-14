import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { CatalogRightsApiService } from '../services/catalog-rights-api.service';
import { CatalogAsset } from '../models/catalog-rights.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { StatusLabelPipe } from '../../../shared/pipes/status-label.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-catalog-assets-list',
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
    <div class="vx-enterprise catalog-assets-list-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <app-enterprise-page-header
          [title]="'catalogRights.assets.title' | t:lang()"
          [subtitle]="'catalogRights.assets.subtitle' | t:lang()"
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

        <app-enterprise-section-card [title]="'catalogRights.assets.create' | t:lang()">
          <form [formGroup]="createForm" (ngSubmit)="createAsset()" class="form-grid">
            <app-enterprise-form-field
              [label]="'catalogRights.assets.assetTitle' | t:lang()"
              [required]="true"
            >
              <input formControlName="title" class="input" />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'catalogRights.assets.warehouseTrack' | t:lang()">
              <input formControlName="warehouse_track_id" type="number" class="input" />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'catalogRights.assets.artistProfile' | t:lang()">
              <input formControlName="artist_profile_id" type="number" class="input" />
            </app-enterprise-form-field>
            <div class="form-grid__actions">
              <button type="submit" class="btn btn--primary" [disabled]="createForm.invalid">
                {{ 'catalogRights.assets.create' | t:lang() }}
              </button>
            </div>
          </form>
        </app-enterprise-section-card>

        @if (error) {
          <app-enterprise-error-state [message]="error" (retry)="load()" />
        } @else if (loading) {
          <app-enterprise-loading-skeleton [rows]="3" />
        } @else if (assets.length === 0) {
          <app-enterprise-empty-state
            [title]="'catalogRights.assets.emptyTitle' | t:lang()"
            [description]="'catalogRights.assets.emptyBody' | t:lang()"
            [ctaLabel]="'catalogRights.assets.create' | t:lang()"
          />
        } @else {
          <app-enterprise-data-table>
            <table class="data-table">
              <thead>
                <tr>
                  <th>{{ 'catalogRights.assets.assetTitle' | t:lang() }}</th>
                  <th>{{ 'common.status' | t:lang() }}</th>
                  <th>{{ 'catalogRights.assets.warehouseLink' | t:lang() }}</th>
                  <th>{{ 'common.actions' | t:lang() }}</th>
                </tr>
              </thead>
              <tbody>
                @for (asset of assets; track asset.id) {
                  <tr>
                    <td>{{ asset.title }}</td>
                    <td><app-enterprise-status-badge [status]="asset.status" /></td>
                    <td>
                      @if (asset.warehouse_track_id) {
                        <span class="badge badge--linked">
                          {{ 'catalogRights.assets.linked' | t:lang() }} (#{{ asset.warehouse_track_id }})
                        </span>
                      } @else {
                        <span class="badge badge--unlinked">
                          {{ 'catalogRights.assets.notLinked' | t:lang() }}
                        </span>
                      }
                    </td>
                    <td>
                      <a
                        [routerLink]="['/catalog-rights/assets', asset.id]"
                        class="btn btn--ghost btn--sm"
                      >
                        {{ 'common.view' | t:lang() }}
                      </a>
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </app-enterprise-data-table>
          <p class="muted">{{ 'catalogRights.assets.total' | t:lang() }}: {{ total }}</p>
        }
      }
    </div>
  `,
})
export class CatalogAssetsListPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(CatalogRightsApiService);
  private fb = inject(FormBuilder);
  private orgCtx = inject(OrganizationContextService);

  assets: CatalogAsset[] = [];
  total = 0;
  loading = false;
  error: string | null = null;
  statusFilter = '';
  orgId: number | null = null;

  createForm = this.fb.group({
    title: ['', [Validators.required]],
    warehouse_track_id: [null as number | null],
    artist_profile_id: [null as number | null],
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

  load(): void {
    const id = this.orgCtx.organizationId() ?? 0;
    this.orgId = id || null;
    if (!this.orgId) return;
    this.loading = true;
    this.api.listAssets(this.orgId, { status: this.statusFilter || undefined }).subscribe({
      next: (res) => {
        this.assets = res.items;
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

  createAsset(): void {
    if (this.createForm.invalid || !this.orgId) return;
    const value = this.createForm.value;
    this.api
      .registerAsset(this.orgId, {
        title: value.title!,
        warehouse_track_id: value.warehouse_track_id || null,
        artist_profile_id: value.artist_profile_id || null,
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
