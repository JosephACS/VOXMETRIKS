import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { CatalogRightsApiService } from '../services/catalog-rights-api.service';
import { RightsContract } from '../models/catalog-rights.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
@Component({
  selector: 'app-rights-contracts-list',
  standalone: true,
  imports: [CommonModule, RouterLink, ReactiveFormsModule, TranslatePipe],
  template: `
    <div class="vx-enterprise rights-contracts-list-page">
      <h1>{{ 'catalogRights.contracts.title' | t:lang() }}</h1>
      <p class="subtitle read-only-notice">
        Catalog ownership/licensing agreements (master, publishing, neighboring rights). This is
        separate from CRM commercial (sales) contracts, and does not assert legal validity.
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
            <option value="draft">Draft</option>
            <option value="active">Active</option>
            <option value="expired">Expired</option>
            <option value="archived">Archived</option>
            <option value="disputed">Disputed</option>
          </select>
        </label>
      </div>

      <form [formGroup]="createForm" (ngSubmit)="createContract()" class="create-form">
        <input formControlName="asset_id" type="number" placeholder="Asset id" class="input" />
        <select formControlName="rights_type" class="input">
          <option value="master">Master</option>
          <option value="publishing">Publishing</option>
          <option value="neighboring">Neighboring</option>
          <option value="other">Other</option>
        </select>
        <input formControlName="valid_from" type="date" class="input" />
        <input formControlName="valid_to" type="date" placeholder="Valid to (optional)" class="input" />
        <label class="checkbox">
          <input type="checkbox" formControlName="exclusive" /> Exclusive
        </label>
        <button type="submit" class="btn btn--primary" [disabled]="createForm.invalid">
          Create Contract
        </button>
      </form>

      @if (error) {
        <p class="error">{{ error }}</p>
      }

      @if (loading) {
        <p>{{ 'common.loading' | t:lang() }}</p>
      } @else if (contracts.length === 0) {
        <p>{{ 'catalogRights.contracts.empty' | t:lang() }}</p>
      } @else {
        <table class="contracts-table">
          <thead>
            <tr><th>Asset</th><th>Type</th><th>Status</th><th>Exclusive</th><th>Valid From</th><th>Valid To</th><th></th></tr>
          </thead>
          <tbody>
            @for (c of contracts; track c.id) {
              <tr>
                <td>#{{ c.asset_id }}</td>
                <td>{{ c.rights_type }}</td>
                <td><span class="badge" [class]="'badge--' + c.status">{{ c.status }}</span></td>
                <td>{{ c.exclusive ? 'Yes' : 'No' }}</td>
                <td>{{ c.valid_from }}</td>
                <td>{{ c.valid_to ?? '—' }}</td>
                <td><a [routerLink]="['/catalog-rights/contracts', c.id]">View</a></td>
              </tr>
            }
          </tbody>
        </table>
        <p class="total">Total: {{ total }}</p>
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

  createForm = this.fb.group({
    asset_id: [null as number | null, [Validators.required]],
    rights_type: ['master', [Validators.required]],
    valid_from: ['', [Validators.required]],
    valid_to: [''],
    exclusive: [false],
  });

  private get orgId(): number {
    return this.orgCtx.activeOrganization()?.id ?? 0;
  }

  ngOnInit(): void {
    const assetIdParam = this.route.snapshot.queryParamMap.get('asset_id');
    if (assetIdParam) {
      this.assetFilter = Number(assetIdParam);
      this.createForm.patchValue({ asset_id: this.assetFilter });
    }
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
          this.error = e.error?.message ?? 'Error loading rights contracts';
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
        error: (e) => (this.error = e.error?.message ?? 'Error creating rights contract'),
      });
  }
}
