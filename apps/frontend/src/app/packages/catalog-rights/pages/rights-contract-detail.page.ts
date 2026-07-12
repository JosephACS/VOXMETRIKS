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
import { StatusLabelPipe } from '../../../shared/pipes/status-label.pipe';
import { LocaleDatePipe, LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';

@Component({
  selector: 'app-rights-contract-detail',
  standalone: true,
  imports: [CommonModule, RouterLink, ReactiveFormsModule, TranslatePipe, StatusLabelPipe, LocaleMoneyPipe, LocaleDatePipe],
  template: `
    <div class="rights-contract-detail-page">
      <a routerLink="/catalog-rights/contracts">&larr; Back to contracts</a>

      @if (contract) {
        <h1>Rights Contract #{{ contract.id }}</h1>
        <p class="subtitle read-only-notice">
          This record tracks catalog ownership/licensing rights only. It is not a substitute for
          legal counsel and does not certify legal validity.
        </p>

        <div class="profile-card">
          <div class="field"><label>Asset</label><span>#{{ contract.asset_id }}</span></div>
          <div class="field"><label>Rights Type</label><span>{{ contract.rights_type }}</span></div>
          <div class="field"><label>Status</label>
            <span class="badge" [class]="'badge--' + contract.status">{{ contract.status }}</span>
          </div>
          <div class="field"><label>Exclusive</label><span>{{ contract.exclusive ? 'Yes' : 'No' }}</span></div>
          <div class="field"><label>Valid From</label><span>{{ contract.valid_from }}</span></div>
          <div class="field"><label>Valid To</label><span>{{ contract.valid_to ?? '—' }}</span></div>
          <div class="field"><label>Evidence Ref</label><span>{{ contract.evidence_ref ?? '—' }}</span></div>
        </div>

        <div class="actions">
          @if (contract.status !== 'archived') {
            <button class="btn btn--danger" (click)="archive()">Archive</button>
          }
          <a class="btn btn--secondary" [routerLink]="['/catalog-rights/contracts', contract.id, 'history']">
            View History
          </a>
        </div>

        <section class="parties">
          <h2>{{ 'catalogRights.contractDetail.parties' | t:lang() }}</h2>
          <p class="hint">
            Ownership percentages are validated per rights type + territory + overlapping period,
            not as a single global sum.
          </p>
          @if (parties.length === 0) {
            <p>No parties yet.</p>
          } @else {
            <table class="data-table">
              <thead><tr><th>Name</th><th>Type</th><th>Ownership %</th></tr></thead>
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
          }
          <form [formGroup]="partyForm" (ngSubmit)="addParty()">
            <input formControlName="party_name" placeholder="Party name" class="input" />
            <select formControlName="party_type" class="input">
              <option value="external">External</option>
              <option value="organization">Organization</option>
              <option value="artist">Artist</option>
            </select>
            <input formControlName="ownership_percentage" type="number" step="0.01" placeholder="Ownership %" class="input" />
            <button type="submit" class="btn btn--secondary" [disabled]="partyForm.invalid">Add Party</button>
          </form>
          @if (partyConflictWarning) {
            <p class="error">{{ partyConflictWarning }}</p>
          }
        </section>

        <section class="territories">
          <h2>Territories</h2>
          @if (territories.length === 0) {
            <p>No territories set yet (defaults to worldwide coverage checks).</p>
          } @else {
            <ul>
              @for (t of territories; track t.id) {
                <li>{{ t.territory_code }} — {{ t.territory_name }}</li>
              }
            </ul>
          }
          <form [formGroup]="territoryForm" (ngSubmit)="addTerritory()">
            <input formControlName="territory_code" placeholder="Territory code (e.g. US, WW)" class="input" />
            <input formControlName="territory_name" placeholder="Territory name" class="input" />
            <button type="submit" class="btn btn--secondary" [disabled]="territoryForm.invalid">Set Territory</button>
          </form>
          @if (territoryConflictWarning) {
            <p class="error">{{ territoryConflictWarning }}</p>
          }
        </section>

        <section class="authorized-uses">
          <h2>Authorized Uses</h2>
          @if (uses.length === 0) {
            <p>No authorized uses set yet.</p>
          } @else {
            <ul>
              @for (u of uses; track u.id) {
                <li>{{ u.use_code }} — {{ u.description ?? '—' }}</li>
              }
            </ul>
          }
          <form [formGroup]="useForm" (ngSubmit)="addUse()">
            <input formControlName="use_code" placeholder="Use code (e.g. streaming, sync)" class="input" />
            <input formControlName="description" placeholder="Description (optional)" class="input" />
            <button type="submit" class="btn btn--secondary" [disabled]="useForm.invalid">Set Use</button>
          </form>
        </section>

        <section class="approvals">
          <h2>Approvals</h2>
          @if (approvals.length === 0) {
            <p>No approval requests yet.</p>
          } @else {
            <table class="data-table">
              <thead><tr><th>Status</th><th>Approver</th><th>Notes</th><th>Decided</th></tr></thead>
              <tbody>
                @for (a of approvals; track a.id) {
                  <tr>
                    <td><span class="badge" [class]="'badge--' + a.status">{{ a.status }}</span></td>
                    <td>{{ a.approver_user_id ?? '—' }}</td>
                    <td>{{ a.notes ?? '—' }}</td>
                    <td>{{ a.decided_at ? (a.decided_at | date:'short') : '—' }}</td>
                  </tr>
                }
              </tbody>
            </table>
          }
          <div class="approval-actions">
            <button class="btn btn--secondary" (click)="submitForApproval()">{{ 'catalogRights.contractDetail.submit' | t:lang() }}</button>
            <button class="btn btn--primary" (click)="decide(true)">Approve</button>
            <button class="btn btn--danger" (click)="decide(false)">Reject</button>
          </div>
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

  private get orgId(): number {
    return this.orgCtx.activeOrganization()?.id ?? 0;
  }

  private get contractId(): number {
    return Number(this.route.snapshot.paramMap.get('id'));
  }

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading = true;
    this.api.getContract(this.orgId, this.contractId).subscribe({
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
        this.error = e.error?.message ?? 'Error loading rights contract';
      },
    });
  }

  loadParties(): void {
    this.api.listContractParties(this.orgId, this.contractId).subscribe({
      next: (items) => (this.parties = items),
      error: () => (this.parties = []),
    });
  }

  loadTerritories(): void {
    this.api.listContractTerritories(this.orgId, this.contractId).subscribe({
      next: (items) => (this.territories = items),
      error: () => (this.territories = []),
    });
  }

  loadUses(): void {
    this.api.listAuthorizedUses(this.orgId, this.contractId).subscribe({
      next: (items) => (this.uses = items),
      error: () => (this.uses = []),
    });
  }

  loadApprovals(): void {
    this.api.listApprovals(this.orgId, this.contractId).subscribe({
      next: (items) => (this.approvals = items),
      error: () => (this.approvals = []),
    });
  }

  archive(): void {
    this.api.archiveContract(this.orgId, this.contractId).subscribe({
      next: (c) => (this.contract = c),
      error: (e) => (this.error = e.error?.message ?? 'Error archiving contract'),
    });
  }

  addParty(): void {
    if (this.partyForm.invalid) return;
    const value = this.partyForm.value;
    this.api
      .addContractParty(this.orgId, this.contractId, {
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
              ? `${res.conflicts_opened.length} conflict(s) opened due to overlapping ownership. See Conflicts.`
              : null;
        },
        error: (e) => (this.error = e.error?.message ?? 'Error adding party'),
      });
  }

  addTerritory(): void {
    if (this.territoryForm.invalid) return;
    const value = this.territoryForm.value;
    this.api
      .setTerritories(this.orgId, this.contractId, [
        { territory_code: value.territory_code!, territory_name: value.territory_name! },
      ])
      .subscribe({
        next: (res) => {
          this.territoryForm.reset();
          this.loadTerritories();
          this.territoryConflictWarning =
            res.conflicts_opened.length > 0
              ? `${res.conflicts_opened.length} conflict(s) opened due to overlapping territory coverage. See Conflicts.`
              : null;
        },
        error: (e) => (this.error = e.error?.message ?? 'Error setting territory'),
      });
  }

  addUse(): void {
    if (this.useForm.invalid) return;
    const value = this.useForm.value;
    this.api
      .setAuthorizedUses(this.orgId, this.contractId, [
        { use_code: value.use_code!, description: value.description || null },
      ])
      .subscribe({
        next: () => {
          this.useForm.reset();
          this.loadUses();
        },
        error: (e) => (this.error = e.error?.message ?? 'Error setting authorized use'),
      });
  }

  submitForApproval(): void {
    this.api.submitForApproval(this.orgId, this.contractId).subscribe({
      next: () => this.loadApprovals(),
      error: (e) => (this.error = e.error?.message ?? 'Error submitting for approval'),
    });
  }

  decide(approved: boolean): void {
    this.api.approveContract(this.orgId, this.contractId, approved).subscribe({
      next: () => {
        this.loadApprovals();
        this.load();
      },
      error: (e) => (this.error = e.error?.message ?? 'Error deciding on approval'),
    });
  }
}
