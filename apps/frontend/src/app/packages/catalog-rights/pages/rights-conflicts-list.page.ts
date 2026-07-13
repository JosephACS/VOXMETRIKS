import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { CatalogRightsApiService } from '../services/catalog-rights-api.service';
import { RightsConflict } from '../models/catalog-rights.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
@Component({
  selector: 'app-rights-conflicts-list',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, TranslatePipe],
  template: `
    <div class="rights-conflicts-list-page">
      <h1>{{ 'catalogRights.conflicts.title' | t:lang() }}</h1>
      <p class="subtitle">
        Conflicts are opened automatically when ownership percentages exceed 100% for the same
        asset, rights type, territory, and overlapping period. Review and resolve below.
      </p>

      <div class="filters">
        <label>
          Asset id
          <input type="number" [value]="assetFilter ?? ''" (change)="onAssetChange($event)" class="input" />
        </label>
        <label>
          Status
          <select [value]="statusFilter" (change)="onStatusChange($event)">
            <option value="">All</option>
            <option value="open">Open</option>
            <option value="resolved">Resolved</option>
            <option value="dismissed">Dismissed</option>
          </select>
        </label>
      </div>

      <form [formGroup]="openForm" (ngSubmit)="openConflict()" class="create-form">
        <input formControlName="asset_id" type="number" placeholder="Asset id" class="input" />
        <select formControlName="rights_type" class="input">
          <option value="master">Master</option>
          <option value="publishing">Publishing</option>
          <option value="neighboring">Neighboring</option>
          <option value="other">Other</option>
        </select>
        <input formControlName="territory_code" placeholder="Territory code" class="input" />
        <input formControlName="details" placeholder="Details (optional)" class="input" />
        <button type="submit" class="btn btn--primary" [disabled]="openForm.invalid">
          Open Conflict Manually
        </button>
      </form>

      @if (error) {
        <p class="error">{{ error }}</p>
      }

      @if (loading) {
        <p>{{ 'common.loading' | t:lang() }}</p>
      } @else if (conflicts.length === 0) {
        <p>No conflicts.</p>
      } @else {
        <table class="data-table">
          <thead>
            <tr><th>Asset</th><th>Rights Type</th><th>Territory</th><th>Status</th><th>Details</th><th></th></tr>
          </thead>
          <tbody>
            @for (c of conflicts; track c.id) {
              <tr>
                <td>#{{ c.asset_id }}</td>
                <td>{{ c.rights_type }}</td>
                <td>{{ c.territory_code }}</td>
                <td><span class="badge" [class]="'badge--' + c.status">{{ c.status }}</span></td>
                <td>{{ c.details ?? '—' }}</td>
                <td>
                  @if (c.status === 'open') {
                    <button class="btn btn--secondary" (click)="resolve(c.id, 'resolved')">Resolve</button>
                    <button class="btn btn--secondary" (click)="resolve(c.id, 'dismissed')">Dismiss</button>
                  }
                </td>
              </tr>
            }
          </tbody>
        </table>
      }
    </div>
  `,
})
export class RightsConflictsListPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(CatalogRightsApiService);
  private fb = inject(FormBuilder);
  private orgCtx = inject(OrganizationContextService);

  conflicts: RightsConflict[] = [];
  loading = false;
  error: string | null = null;
  statusFilter = '';
  assetFilter: number | null = null;

  openForm = this.fb.group({
    asset_id: [null as number | null, [Validators.required]],
    rights_type: ['master', [Validators.required]],
    territory_code: ['', [Validators.required]],
    details: [''],
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

  onAssetChange(event: Event): void {
    const value = (event.target as HTMLInputElement).value;
    this.assetFilter = value ? Number(value) : null;
    this.load();
  }

  load(): void {
    if (!this.orgId) {
      this.error = this.i18n.t('common.orgRequiredContext');
      return;
    }
    this.loading = true;
    this.api
      .listConflicts(this.orgId, {
        asset_id: this.assetFilter || undefined,
        status: this.statusFilter || undefined,
      })
      .subscribe({
        next: (items) => {
          this.conflicts = items;
          this.loading = false;
          this.error = null;
        },
        error: (e) => {
          this.loading = false;
          this.error = e.error?.message ?? 'Error loading conflicts';
        },
      });
  }

  openConflict(): void {
    if (this.openForm.invalid || !this.orgId) return;
    const value = this.openForm.value;
    this.api
      .openConflict(this.orgId, {
        asset_id: Number(value.asset_id),
        rights_type: value.rights_type!,
        territory_code: value.territory_code!,
        details: value.details || null,
      })
      .subscribe({
        next: () => {
          this.openForm.reset({ rights_type: 'master' });
          this.load();
        },
        error: (e) => (this.error = e.error?.message ?? 'Error opening conflict'),
      });
  }

  resolve(conflictId: number, resolution: string): void {
    this.api.resolveConflict(this.orgId, conflictId, resolution).subscribe({
      next: () => this.load(),
      error: (e) => (this.error = e.error?.message ?? 'Error resolving conflict'),
    });
  }
}
