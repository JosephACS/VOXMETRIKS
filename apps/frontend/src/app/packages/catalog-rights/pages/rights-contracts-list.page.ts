import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { CatalogRightsApiService } from '../services/catalog-rights-api.service';
import { RightsContract } from '../models/catalog-rights.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { StatusLabelPipe } from '../../../shared/pipes/status-label.pipe';
import { LocaleDatePipe } from '../../../shared/pipes/locale-format.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-rights-contracts-list',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    ReactiveFormsModule,
    TranslatePipe,
    StatusLabelPipe,
    LocaleDatePipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  template: `
    <div class="vx-enterprise rights-contracts-list-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <app-enterprise-page-header
          [title]="'catalogRights.contracts.title' | t:lang()"
          [subtitle]="'catalogRights.contracts.subtitle' | t:lang()"
        />

        <app-enterprise-action-bar>
          <app-enterprise-form-field [label]="'catalogRights.contracts.assetId' | t:lang()">
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
              <option value="draft">{{ 'draft' | statusLabel }}</option>
              <option value="active">{{ 'active' | statusLabel }}</option>
              <option value="expired">{{ 'expired' | statusLabel }}</option>
              <option value="archived">{{ 'archived' | statusLabel }}</option>
              <option value="disputed">{{ 'disputed' | statusLabel }}</option>
            </select>
          </app-enterprise-form-field>
        </app-enterprise-action-bar>

        <app-enterprise-section-card [title]="'catalogRights.contracts.create' | t:lang()">
          <form [formGroup]="createForm" (ngSubmit)="createContract()" class="form-grid">
            <app-enterprise-form-field
              [label]="'catalogRights.contracts.assetId' | t:lang()"
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
              [label]="'catalogRights.contracts.validFrom' | t:lang()"
              [required]="true"
            >
              <input formControlName="valid_from" type="date" class="input" />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'catalogRights.contracts.validToOptional' | t:lang()">
              <input formControlName="valid_to" type="date" class="input" />
            </app-enterprise-form-field>
            <label class="checkbox">
              <input type="checkbox" formControlName="exclusive" />
              {{ 'catalogRights.contracts.exclusive' | t:lang() }}
            </label>
            <div class="form-grid__actions">
              <button type="submit" class="btn btn--primary" [disabled]="createForm.invalid">
                {{ 'catalogRights.contracts.create' | t:lang() }}
              </button>
            </div>
          </form>
        </app-enterprise-section-card>

        @if (error) {
          <app-enterprise-error-state [message]="error" (retry)="load()" />
        } @else if (loading) {
          <app-enterprise-loading-skeleton [rows]="3" />
        } @else if (contracts.length === 0) {
          <app-enterprise-empty-state
            [title]="'catalogRights.contracts.emptyTitle' | t:lang()"
            [description]="'catalogRights.contracts.emptyBody' | t:lang()"
            [ctaLabel]="'catalogRights.contracts.create' | t:lang()"
          />
        } @else {
          <app-enterprise-data-table>
            <table class="data-table">
              <thead>
                <tr>
                  <th>{{ 'catalogRights.contracts.assetId' | t:lang() }}</th>
                  <th>{{ 'catalogRights.contracts.rightsType' | t:lang() }}</th>
                  <th>{{ 'common.status' | t:lang() }}</th>
                  <th>{{ 'catalogRights.contracts.exclusive' | t:lang() }}</th>
                  <th>{{ 'catalogRights.contracts.validFrom' | t:lang() }}</th>
                  <th>{{ 'catalogRights.contracts.validTo' | t:lang() }}</th>
                  <th>{{ 'common.actions' | t:lang() }}</th>
                </tr>
              </thead>
              <tbody>
                @for (c of contracts; track c.id) {
                  <tr>
                    <td>#{{ c.asset_id }}</td>
                    <td>{{ rightsTypeLabel(c.rights_type) }}</td>
                    <td><app-enterprise-status-badge [status]="c.status" /></td>
                    <td>{{ (c.exclusive ? 'common.yes' : 'common.no') | t:lang() }}</td>
                    <td>{{ c.valid_from | localeDate }}</td>
                    <td>{{ c.valid_to | localeDate }}</td>
                    <td>
                      <a [routerLink]="['/catalog-rights/contracts', c.id]" class="btn btn--ghost btn--sm">
                        {{ 'common.view' | t:lang() }}
                      </a>
                    </td>
                  </tr>
                }
              </tbody>
            </table>
          </app-enterprise-data-table>
          <p class="muted">{{ 'catalogRights.contracts.total' | t:lang() }}: {{ total }}</p>
        }
      }
    </div>
  `,
})
export class RightsContractsListPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(CatalogRightsApiService);
  private fb = inject(FormBuilder);
  private orgCtx = inject(OrganizationContextService);
  private route = inject(ActivatedRoute);

  contracts: RightsContract[] = [];
  total = 0;
  loading = false;
  error: string | null = null;
  statusFilter = '';
  assetFilter: number | null = null;
  orgId: number | null = null;

  createForm = this.fb.group({
    asset_id: [null as number | null, [Validators.required]],
    rights_type: ['master', [Validators.required]],
    valid_from: ['', [Validators.required]],
    valid_to: [''],
    exclusive: [false],
  });

  ngOnInit(): void {
    this.orgId = this.orgCtx.activeOrganization()?.id ?? null;
    const assetIdParam = this.route.snapshot.queryParamMap.get('asset_id');
    if (assetIdParam) {
      this.assetFilter = Number(assetIdParam);
      this.createForm.patchValue({ asset_id: this.assetFilter });
    }
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
    const id = this.orgCtx.activeOrganization()?.id ?? 0;
    this.orgId = id || null;
    if (!this.orgId) return;
    this.loading = true;
    this.api
      .listContracts(this.orgId, {
        asset_id: this.assetFilter || undefined,
        status: this.statusFilter || undefined,
      })
      .subscribe({
        next: (res) => {
          this.contracts = res.items;
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

  createContract(): void {
    if (this.createForm.invalid || !this.orgId) return;
    const value = this.createForm.value;
    this.api
      .createContract(this.orgId, {
        asset_id: Number(value.asset_id),
        rights_type: value.rights_type!,
        valid_from: value.valid_from!,
        valid_to: value.valid_to || null,
        exclusive: !!value.exclusive,
      })
      .subscribe({
        next: () => {
          this.createForm.reset({ rights_type: 'master', exclusive: false });
          this.load();
        },
        error: (e) => (this.error = e.error?.message ?? this.i18n.t('common.failed')),
      });
  }
}
