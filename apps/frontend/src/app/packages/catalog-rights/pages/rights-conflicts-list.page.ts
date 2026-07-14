import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { CatalogRightsApiService } from '../services/catalog-rights-api.service';
import { RightsConflict } from '../models/catalog-rights.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { StatusLabelPipe } from '../../../shared/pipes/status-label.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-rights-conflicts-list',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    TranslatePipe,
    StatusLabelPipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  template: `
    <div class="vx-enterprise rights-conflicts-list-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <app-enterprise-page-header
          [title]="'catalogRights.conflicts.title' | t:lang()"
          [subtitle]="'catalogRights.conflicts.subtitle' | t:lang()"
        />

        <app-enterprise-action-bar>
          <app-enterprise-form-field [label]="'catalogRights.conflicts.assetId' | t:lang()">
            <input
              type="number"
              class="input"
              [value]="assetFilter ?? ''"
              (change)="onAssetChange($event)"
            />
          </app-enterprise-form-field>
          <app-enterprise-form-field [label]="'common.status' | t:lang()">
            <select class="input" [value]="statusFilter" (change)="onStatusChange($event)">
              <option value="">{{ 'common.all' | t:lang() }}</option>
              <option value="open">{{ 'open' | statusLabel }}</option>
              <option value="resolved">{{ 'resolved' | statusLabel }}</option>
              <option value="dismissed">{{ 'dismissed' | statusLabel }}</option>
            </select>
          </app-enterprise-form-field>
        </app-enterprise-action-bar>

        <app-enterprise-section-card [title]="'catalogRights.conflicts.open' | t:lang()">
          <form [formGroup]="openForm" (ngSubmit)="openConflict()" class="form-grid">
            <app-enterprise-form-field
              [label]="'catalogRights.conflicts.assetId' | t:lang()"
              [required]="true"
            >
              <input formControlName="asset_id" type="number" class="input" />
            </app-enterprise-form-field>
            <app-enterprise-form-field
              [label]="'catalogRights.contracts.rightsType' | t:lang()"
              [required]="true"
            >
              <select formControlName="rights_type" class="input">
                <option value="master">{{ 'catalogRights.rightsType.master' | t:lang() }}</option>
                <option value="publishing">{{ 'catalogRights.rightsType.publishing' | t:lang() }}</option>
                <option value="neighboring">{{ 'catalogRights.rightsType.neighboring' | t:lang() }}</option>
                <option value="other">{{ 'catalogRights.rightsType.other' | t:lang() }}</option>
              </select>
            </app-enterprise-form-field>
            <app-enterprise-form-field
              [label]="'catalogRights.conflicts.territory' | t:lang()"
              [required]="true"
            >
              <input formControlName="territory_code" class="input" />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'catalogRights.conflicts.detailsOptional' | t:lang()">
              <input formControlName="details" class="input" />
            </app-enterprise-form-field>
            <div class="form-grid__actions">
              <button type="submit" class="btn btn--primary" [disabled]="openForm.invalid">
                {{ 'catalogRights.conflicts.open' | t:lang() }}
              </button>
            </div>
          </form>
        </app-enterprise-section-card>

        @if (error) {
          <app-enterprise-error-state [message]="error" (retry)="load()" />
        } @else if (loading) {
          <app-enterprise-loading-skeleton [rows]="3" />
        } @else if (conflicts.length === 0) {
          <app-enterprise-empty-state
            [title]="'catalogRights.conflicts.emptyTitle' | t:lang()"
            [description]="'catalogRights.conflicts.emptyBody' | t:lang()"
            [ctaLabel]="'catalogRights.conflicts.open' | t:lang()"
          />
        } @else {
          <app-enterprise-data-table>
            <table class="data-table">
              <thead>
                <tr>
                  <th>{{ 'catalogRights.conflicts.assetId' | t:lang() }}</th>
                  <th>{{ 'catalogRights.contracts.rightsType' | t:lang() }}</th>
                  <th>{{ 'catalogRights.conflicts.territory' | t:lang() }}</th>
                  <th>{{ 'common.status' | t:lang() }}</th>
                  <th>{{ 'common.details' | t:lang() }}</th>
                  <th>{{ 'common.actions' | t:lang() }}</th>
                </tr>
              </thead>
              <tbody>
                @for (c of conflicts; track c.id) {
                  <tr>
                    <td>#{{ c.asset_id }}</td>
                    <td>{{ rightsTypeLabel(c.rights_type) }}</td>
                    <td>{{ c.territory_code }}</td>
                    <td><app-enterprise-status-badge [status]="c.status" /></td>
                    <td>{{ c.details || ('common.notAvailable' | t:lang()) }}</td>
                    <td>
                      @if (c.status === 'open') {
                        <button
                          type="button"
                          class="btn btn--secondary btn--sm"
                          (click)="resolve(c.id, 'resolved')"
                        >
                          {{ 'catalogRights.conflicts.resolve' | t:lang() }}
                        </button>
                        <button
                          type="button"
                          class="btn btn--ghost btn--sm"
                          (click)="resolve(c.id, 'dismissed')"
                        >
                          {{ 'catalogRights.conflicts.dismiss' | t:lang() }}
                        </button>
                      }
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </app-enterprise-data-table>
        }
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
  orgId: number | null = null;

  openForm = this.fb.group({
    asset_id: [null as number | null, [Validators.required]],
    rights_type: ['master', [Validators.required]],
    territory_code: ['', [Validators.required]],
    details: [''],
  });

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    if (!this.orgId) return;
    this.load();
  }

  rightsTypeLabel(code: string): string {
    const key = `catalogRights.rightsType.${code}`;
    const translated = this.i18n.t(key);
    return translated === key ? code : translated;
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
    const id = this.orgCtx.organizationId() ?? 0;
    this.orgId = id || null;
    if (!this.orgId) return;
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
          this.error = e.error?.message ?? this.i18n.t('common.failed');
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
        error: (e) => (this.error = e.error?.message ?? this.i18n.t('common.failed')),
      });
  }

  resolve(conflictId: number, resolution: string): void {
    if (!this.orgId) return;
    this.api.resolveConflict(this.orgId, conflictId, resolution).subscribe({
      next: () => this.load(),
      error: (e) => (this.error = e.error?.message ?? this.i18n.t('common.failed')),
    });
  }
}
