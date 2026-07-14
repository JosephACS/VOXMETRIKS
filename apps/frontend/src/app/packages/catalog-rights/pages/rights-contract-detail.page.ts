import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { CatalogRightsApiService } from '../services/catalog-rights-api.service';
import {
  RightsApproval,
  RightsAuthorizedUse,
  RightsContract,
  RightsContractParty,
  RightsTerritory,
} from '../models/catalog-rights.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { LocaleDatePipe } from '../../../shared/pipes/locale-format.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-rights-contract-detail',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    ReactiveFormsModule,
    TranslatePipe,
    LocaleDatePipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  template: `
    <div class="vx-enterprise rights-contract-detail-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else if (loading) {
        <app-enterprise-loading-skeleton [rows]="6" />
      } @else if (contract) {
        <a routerLink="/catalog-rights/contracts" class="back-link">
          {{ 'catalogRights.contractDetail.back' | t:lang() }}
        </a>

        <app-enterprise-page-header
          [title]="('catalogRights.contractDetail.title' | t:lang()) + ' #' + contract.id"
          [subtitle]="'catalogRights.contractDetail.disclaimer' | t:lang()"
        >
          <app-enterprise-status-badge [status]="contract.status" />
        </app-enterprise-page-header>

        <app-enterprise-section-card [title]="'common.details' | t:lang()">
          <dl class="meta">
            <dt>{{ 'catalogRights.contracts.assetId' | t:lang() }}</dt>
            <dd>#{{ contract.asset_id }}</dd>
            <dt>{{ 'catalogRights.contracts.rightsType' | t:lang() }}</dt>
            <dd>{{ contract.rights_type }}</dd>
            <dt>{{ 'catalogRights.contracts.exclusive' | t:lang() }}</dt>
            <dd>{{ contract.exclusive ? ('common.yes' | t:lang()) : ('common.no' | t:lang()) }}</dd>
            <dt>{{ 'catalogRights.contracts.validFrom' | t:lang() }}</dt>
            <dd>{{ contract.valid_from }}</dd>
            <dt>{{ 'catalogRights.contracts.validTo' | t:lang() }}</dt>
            <dd>{{ contract.valid_to ?? '—' }}</dd>
            <dt>{{ 'catalogRights.contractDetail.evidenceRef' | t:lang() }}</dt>
            <dd>{{ contract.evidence_ref ?? '—' }}</dd>
          </dl>
        </app-enterprise-section-card>

        <app-enterprise-action-bar>
          @if (contract.status !== 'archived') {
            <button class="btn btn--danger" (click)="archive()">
              {{ 'catalogRights.contractDetail.archive' | t:lang() }}
            </button>
          }
          <a class="btn btn--secondary" [routerLink]="['/catalog-rights/contracts', contract.id, 'history']">
            {{ 'catalogRights.contractDetail.history' | t:lang() }}
          </a>
        </app-enterprise-action-bar>

        <app-enterprise-section-card [title]="'catalogRights.contractDetail.parties' | t:lang()">
          <p class="hint muted">{{ 'catalogRights.contractDetail.partiesHint' | t:lang() }}</p>
          @if (parties.length === 0) {
            <p class="muted">{{ 'catalogRights.contractDetail.noParties' | t:lang() }}</p>
          } @else {
            <app-enterprise-data-table>
              <table class="data-table">
                <thead>
                  <tr>
                    <th>{{ 'common.name' | t:lang() }}</th>
                    <th>{{ 'common.type' | t:lang() }}</th>
                    <th>{{ 'catalogRights.contractDetail.ownershipPct' | t:lang() }}</th>
                  </tr>
                </thead>
                <tbody>
                  @for (p of parties; track p.id) {
                    <tr>
                      <td>{{ p.party_name }}</td>
                      <td>{{ p.party_type }}</td>
                      <td>{{ p.ownership_percentage }}%</td>
                    </tr>
                  }
                </tbody>
              </table>
            </app-enterprise-data-table>
          }
          <form [formGroup]="partyForm" (ngSubmit)="addParty()" class="form-grid">
            <app-enterprise-form-field [label]="'common.name' | t:lang()" [required]="true">
              <input formControlName="party_name" class="input" />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'common.type' | t:lang()">
              <select formControlName="party_type" class="input">
                <option value="external">{{ 'catalogRights.contractDetail.partyExternal' | t:lang() }}</option>
                <option value="organization">{{ 'common.organization' | t:lang() }}</option>
                <option value="artist">{{ 'catalogRights.assetDetail.artists' | t:lang() }}</option>
              </select>
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'catalogRights.contractDetail.ownershipPct' | t:lang()" [required]="true">
              <input formControlName="ownership_percentage" type="number" step="0.01" class="input" />
            </app-enterprise-form-field>
            <div class="form-grid__actions">
              <button type="submit" class="btn btn--secondary" [disabled]="partyForm.invalid">
                {{ 'catalogRights.contractDetail.addParty' | t:lang() }}
              </button>
            </div>
          </form>
          @if (partyConflictWarning) {
            <p class="error">{{ partyConflictWarning }}</p>
          }
        </app-enterprise-section-card>

        <app-enterprise-section-card [title]="'catalogRights.contractDetail.territories' | t:lang()">
          @if (territories.length === 0) {
            <p class="muted">{{ 'catalogRights.contractDetail.noTerritories' | t:lang() }}</p>
          } @else {
            <ul class="ent-list">
              @for (t of territories; track t.id) {
                <li>{{ t.territory_code }} — {{ t.territory_name }}</li>
              }
            </ul>
          }
          <form [formGroup]="territoryForm" (ngSubmit)="addTerritory()" class="form-grid">
            <app-enterprise-form-field [label]="'catalogRights.conflicts.territory' | t:lang()" [required]="true">
              <input formControlName="territory_code" class="input" />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'common.name' | t:lang()" [required]="true">
              <input formControlName="territory_name" class="input" />
            </app-enterprise-form-field>
            <div class="form-grid__actions">
              <button type="submit" class="btn btn--secondary" [disabled]="territoryForm.invalid">
                {{ 'catalogRights.contractDetail.setTerritory' | t:lang() }}
              </button>
            </div>
          </form>
          @if (territoryConflictWarning) {
            <p class="error">{{ territoryConflictWarning }}</p>
          }
        </app-enterprise-section-card>

        <app-enterprise-section-card [title]="'catalogRights.contractDetail.authorizedUses' | t:lang()">
          @if (uses.length === 0) {
            <p class="muted">{{ 'catalogRights.contractDetail.noUses' | t:lang() }}</p>
          } @else {
            <ul class="ent-list">
              @for (u of uses; track u.id) {
                <li>{{ u.use_code }} — {{ u.description ?? '—' }}</li>
              }
            </ul>
          }
          <form [formGroup]="useForm" (ngSubmit)="addUse()" class="form-grid">
            <app-enterprise-form-field [label]="'catalogRights.contractDetail.useCode' | t:lang()" [required]="true">
              <input formControlName="use_code" class="input" />
            </app-enterprise-form-field>
            <app-enterprise-form-field [label]="'common.description' | t:lang()">
              <input formControlName="description" class="input" />
            </app-enterprise-form-field>
            <div class="form-grid__actions">
              <button type="submit" class="btn btn--secondary" [disabled]="useForm.invalid">
                {{ 'catalogRights.contractDetail.setUse' | t:lang() }}
              </button>
            </div>
          </form>
        </app-enterprise-section-card>

        <app-enterprise-section-card [title]="'catalogRights.contractDetail.approvals' | t:lang()">
          @if (approvals.length === 0) {
            <p class="muted">{{ 'catalogRights.contractDetail.noApprovals' | t:lang() }}</p>
          } @else {
            <app-enterprise-data-table>
              <table class="data-table">
                <thead>
                  <tr>
                    <th>{{ 'common.status' | t:lang() }}</th>
                    <th>{{ 'catalogRights.contractDetail.approver' | t:lang() }}</th>
                    <th>{{ 'common.notes' | t:lang() }}</th>
                    <th>{{ 'catalogRights.contractDetail.decided' | t:lang() }}</th>
                  </tr>
                </thead>
                <tbody>
                  @for (a of approvals; track a.id) {
                    <tr>
                      <td><app-enterprise-status-badge [status]="a.status" /></td>
                      <td>{{ a.approver_user_id ?? '—' }}</td>
                      <td>{{ a.notes ?? '—' }}</td>
                      <td>{{ a.decided_at ? (a.decided_at | localeDate: true) : '—' }}</td>
                    </tr>
                  }
                </tbody>
              </table>
            </app-enterprise-data-table>
          }
          <app-enterprise-action-bar>
            <button class="btn btn--secondary" (click)="submitForApproval()">
              {{ 'catalogRights.contractDetail.submit' | t:lang() }}
            </button>
            <button class="btn btn--primary" (click)="decide(true)">
              {{ 'catalogRights.contractDetail.approve' | t:lang() }}
            </button>
            <button class="btn btn--danger" (click)="decide(false)">
              {{ 'catalogRights.contractDetail.reject' | t:lang() }}
            </button>
          </app-enterprise-action-bar>
        </app-enterprise-section-card>
      }

      @if (error) {
        <app-enterprise-error-state [message]="error" (retry)="load()" />
      }
    </div>
  `,
})
export class RightsContractDetailPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(CatalogRightsApiService);
  private route = inject(ActivatedRoute);
  private fb = inject(FormBuilder);
  private orgCtx = inject(OrganizationContextService);

  contract: RightsContract | null = null;
  parties: RightsContractParty[] = [];
  territories: RightsTerritory[] = [];
  uses: RightsAuthorizedUse[] = [];
  approvals: RightsApproval[] = [];
  loading = false;
  error: string | null = null;
  partyConflictWarning: string | null = null;
  territoryConflictWarning: string | null = null;
  orgId: number | null = null;

  partyForm = this.fb.group({
    party_name: ['', [Validators.required]],
    party_type: ['external'],
    ownership_percentage: [null as number | null, [Validators.required]],
  });

  territoryForm = this.fb.group({
    territory_code: ['', [Validators.required]],
    territory_name: ['', [Validators.required]],
  });

  useForm = this.fb.group({
    use_code: ['', [Validators.required]],
    description: [''],
  });

  private get contractId(): number {
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
    this.api.getContract(orgId, this.contractId).subscribe({
      next: (c) => {
        this.contract = c;
        this.loading = false;
        this.loadParties();
        this.loadTerritories();
        this.loadUses();
        this.loadApprovals();
      },
      error: (e) => {
        this.loading = false;
        this.error = e.error?.message ?? this.i18n.t('common.failed');
      },
    });
  }

  loadParties(): void {
    const orgId = this.orgId;
    if (!orgId) return;
    this.api.listContractParties(orgId, this.contractId).subscribe({
      next: (items) => (this.parties = items),
      error: () => (this.parties = []),
    });
  }

  loadTerritories(): void {
    const orgId = this.orgId;
    if (!orgId) return;
    this.api.listContractTerritories(orgId, this.contractId).subscribe({
      next: (items) => (this.territories = items),
      error: () => (this.territories = []),
    });
  }

  loadUses(): void {
    const orgId = this.orgId;
    if (!orgId) return;
    this.api.listAuthorizedUses(orgId, this.contractId).subscribe({
      next: (items) => (this.uses = items),
      error: () => (this.uses = []),
    });
  }

  loadApprovals(): void {
    const orgId = this.orgId;
    if (!orgId) return;
    this.api.listApprovals(orgId, this.contractId).subscribe({
      next: (items) => (this.approvals = items),
      error: () => (this.approvals = []),
    });
  }

  archive(): void {
    const orgId = this.orgId;
    if (!orgId) return;
    this.api.archiveContract(orgId, this.contractId).subscribe({
      next: (c) => (this.contract = c),
      error: (e) => (this.error = e.error?.message ?? this.i18n.t('common.failed')),
    });
  }

  addParty(): void {
    const orgId = this.orgId;
    if (!orgId || this.partyForm.invalid) return;
    const value = this.partyForm.value;
    this.api
      .addContractParty(orgId, this.contractId, {
        party_name: value.party_name!,
        party_type: value.party_type || 'external',
        ownership_percentage: Number(value.ownership_percentage),
      })
      .subscribe({
        next: (res) => {
          this.partyForm.reset({ party_type: 'external' });
          this.loadParties();
          this.partyConflictWarning =
            res.conflicts_opened.length > 0
              ? this.i18n.t('catalogRights.contractDetail.partyConflict', { count: res.conflicts_opened.length })
              : null;
        },
        error: (e) => (this.error = e.error?.message ?? this.i18n.t('common.failed')),
      });
  }

  addTerritory(): void {
    const orgId = this.orgId;
    if (!orgId || this.territoryForm.invalid) return;
    const value = this.territoryForm.value;
    this.api
      .setTerritories(orgId, this.contractId, [
        { territory_code: value.territory_code!, territory_name: value.territory_name! },
      ])
      .subscribe({
        next: (res) => {
          this.territoryForm.reset();
          this.loadTerritories();
          this.territoryConflictWarning =
            res.conflicts_opened.length > 0
              ? this.i18n.t('catalogRights.contractDetail.territoryConflict', { count: res.conflicts_opened.length })
              : null;
        },
        error: (e) => (this.error = e.error?.message ?? this.i18n.t('common.failed')),
      });
  }

  addUse(): void {
    const orgId = this.orgId;
    if (!orgId || this.useForm.invalid) return;
    const value = this.useForm.value;
    this.api
      .setAuthorizedUses(orgId, this.contractId, [
        { use_code: value.use_code!, description: value.description || null },
      ])
      .subscribe({
        next: () => {
          this.useForm.reset();
          this.loadUses();
        },
        error: (e) => (this.error = e.error?.message ?? this.i18n.t('common.failed')),
      });
  }

  submitForApproval(): void {
    const orgId = this.orgId;
    if (!orgId) return;
    this.api.submitForApproval(orgId, this.contractId).subscribe({
      next: () => this.loadApprovals(),
      error: (e) => (this.error = e.error?.message ?? this.i18n.t('common.failed')),
    });
  }

  decide(approved: boolean): void {
    const orgId = this.orgId;
    if (!orgId) return;
    this.api.approveContract(orgId, this.contractId, approved).subscribe({
      next: () => {
        this.loadApprovals();
        this.load();
      },
      error: (e) => (this.error = e.error?.message ?? this.i18n.t('common.failed')),
    });
  }
}
