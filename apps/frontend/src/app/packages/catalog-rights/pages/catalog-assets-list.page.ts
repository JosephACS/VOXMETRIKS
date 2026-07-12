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
import { LocaleDatePipe, LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';

@Component({
  selector: 'app-catalog-assets-list',
  standalone: true,
  imports: [CommonModule, RouterLink, ReactiveFormsModule, TranslatePipe, StatusLabelPipe, LocaleMoneyPipe, LocaleDatePipe],
  template: `
    <div class="catalog-assets-list-page">
      <h1>{{ 'catalogRights.assets.title' | t:lang() }}</h1>
      <p class="subtitle">
        Rights-tracking records for songs/works. This is not a legal registry — it does not
        assert legal validity or ownership.
      </p>

      <div class="filters">
        <label>
          Status
          <select [value]="statusFilter" (change)="onStatusChange($event)">
            <option value="">All</option>
            <option value="draft">Draft</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="archived">Archived</option>
          </select>
        </label>
      </div>

      <form [formGroup]="createForm" (ngSubmit)="createAsset()" class="create-form">
        <input formControlName="title" placeholder="Asset title" class="input" />
        <input formControlName="warehouse_track_id" type="number" placeholder="Warehouse track id (optional)" class="input" />
        <input formControlName="artist_profile_id" type="number" placeholder="Artist profile id (optional)" class="input" />
        <button type="submit" class="btn btn--primary" [disabled]="createForm.invalid">
          Register Asset
        </button>
      </form>

      @if (error) {
        <p class="error">{{ error }}</p>
      }

      @if (loading) {
        <p>{{ 'common.loading' | t:lang() }}</p>
      } @else if (assets.length === 0) {
        <p>{{ 'catalogRights.assets.empty' | t:lang() }}</p>
      } @else {
        <table class="assets-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Status</th>
              <th>Warehouse Link</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            @for (asset of assets; track asset.id) {
              <tr>
                <td>{{ asset.title }}</td>
                <td><span class="badge" [class]="'badge--' + asset.status">{{ asset.status }}</span></td>
                <td>
                  @if (asset.warehouse_track_id) {
                    <span class="badge badge--linked">Linked (#{{ asset.warehouse_track_id }})</span>
                  } @else {
                    <span class="badge badge--unlinked">Not linked</span>
                  }
                </td>
                <td>
                  <a [routerLink]="['/catalog-rights/assets', asset.id]">View</a>
                </td>
              </tr>
            }
          </tbody>
        </table>
        <p class="total">Total: {{ total }}</p>
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

  createForm = this.fb.group({
    title: ['', [Validators.required]],
    warehouse_track_id: [null as number | null],
    artist_profile_id: [null as number | null],
  });

  private get orgId(): number {
    return this.orgCtx.activeOrganization()?.id ?? 0;
  }

  ngOnInit(): void {
    this.load();
  }

  onStatusChange(event: Event): void {
    this.statusFilter = (event.target as HTMLSelectElement).value;
    this.load();
  }

  load(): void {
    if (!this.orgId) {
      this.error = this.i18n.t('common.orgRequiredContext');
      return;
    }
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
        this.error = e.error?.message ?? 'Error loading catalog assets';
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
        error: (e) => (this.error = e.error?.message ?? 'Error registering catalog asset'),
      });
  }
}
