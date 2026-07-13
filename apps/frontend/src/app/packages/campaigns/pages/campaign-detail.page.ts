import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { CampaignsApiService } from '../services/campaigns-api.service';
import {
  Campaign, CampaignApproval, CampaignBudget, CampaignExpense, CampaignRoiSnapshot,
} from '../models/campaigns.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
@Component({
  selector: 'app-campaign-detail',
  standalone: true,
  imports: [CommonModule, RouterLink, ReactiveFormsModule, TranslatePipe],
  template: `
    <div class="campaign-detail-page">
      <a routerLink="/campaigns">← Back to campaigns</a>

      @if (loading) { <p>{{ 'common.loading' | t:lang() }}</p> }
      @else if (!orgId) { <p class="error">Select an organization context.</p> }
      @else if (campaign) {
        <h1>{{ campaign.name }}</h1>
        <p>Status: <span class="badge">{{ campaign.status }}</span></p>

        <section class="roi-section">
          <h2>ROI</h2>
          @if (roi) {
            @if (roi.status === 'available' && roi.roi_value != null) {
              <p class="roi-value">ROI: {{ roi.roi_value | number:'1.2-2' }}</p>
              @if (roi.budget_utilization != null) {
                <p>Budget utilization: {{ roi.budget_utilization * 100 | number:'1.0-0' }}%</p>
              }
            } @else {
              <p class="roi-unavailable">{{ 'common.notAvailable' | t:lang() }}</p>
              <p class="roi-reason">{{ roi.unavailable_reason || 'Insufficient data for monetary ROI' }}</p>
            }
            @if (roi.engagement_lift != null) {
              <p>Engagement (streams): {{ roi.engagement_lift | number }} — not monetary</p>
            }
          } @else {
            <p class="roi-unavailable">{{ 'common.notAvailable' | t:lang() }} — no snapshot yet</p>
            <button type="button" (click)="computeRoi()" [disabled]="busy">{{ 'campaigns.detail.roi' | t:lang() }}</button>
          }
        </section>

        <section>
          <h2>Budget</h2>
          @if (budget) {
            <p>{{ budget.amount | number }} {{ budget.currency }}</p>
          } @else {
            <form [formGroup]="budgetForm" (ngSubmit)="setBudget()">
              <input formControlName="amount" type="number" placeholder="Amount" />
              <input formControlName="currency" placeholder="Currency" />
              <button type="submit" [disabled]="budgetForm.invalid || busy">{{ 'campaigns.detail.budget' | t:lang() }}</button>
            </form>
          }
        </section>

        <section>
          <h2>Expenses</h2>
          <form [formGroup]="expenseForm" (ngSubmit)="addExpense()">
            <input formControlName="amount" type="number" placeholder="Amount" />
            <input formControlName="category" placeholder="Category" />
            <input formControlName="expense_date" type="date" />
            <button type="submit" [disabled]="expenseForm.invalid || busy">Add Expense</button>
          </form>
          @if (expenses.length === 0) { <p>No expenses recorded.</p> }
          @else {
            <ul>
              @for (e of expenses; track e.id) {
                <li>{{ e.expense_date }} — {{ e.category }}: {{ e.amount }} {{ e.currency }}</li>
              }
            </ul>
          }
        </section>

        <section>
          <h2>Approvals</h2>
          <div class="actions">
            <button type="button" (click)="requestApproval()" [disabled]="busy">{{ 'campaigns.detail.requestApproval' | t:lang() }}</button>
          </div>
          @if (approvals.length === 0) { <p>No approval requests.</p> }
          @else {
            <ul>
              @for (a of approvals; track a.id) {
                <li>
                  {{ a.approval_type }} — <span class="badge">{{ a.status }}</span>
                  (requested {{ a.requested_at | date:'short' }})
                  @if (a.status === 'pending') {
                    <button type="button" (click)="decide(a.id, true)" [disabled]="busy">Approve</button>
                    <button type="button" (click)="decide(a.id, false)" [disabled]="busy">Reject</button>
                  }
                </li>
              }
            </ul>
          }
        </section>
      } @else if (!loading) {
        <p class="empty-state">Campaign not found.</p>
      }
      @if (error) { <p class="error">{{ error }}</p> }
      @if (success) { <p class="success">{{ success }}</p> }
    </div>
  `,
})
export class CampaignDetailPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(CampaignsApiService);
  private route = inject(ActivatedRoute);
  private fb = inject(FormBuilder);
  private orgCtx = inject(OrganizationContextService);

  campaign: Campaign | null = null;
  budget: CampaignBudget | null = null;
  expenses: CampaignExpense[] = [];
  approvals: CampaignApproval[] = [];
  roi: CampaignRoiSnapshot | null = null;
  loading = false;
  busy = false;
  error: string | null = null;
  success: string | null = null;
  campaignId = 0;
  orgId: number | null = null;

  budgetForm = this.fb.group({ amount: [null as number | null, Validators.required], currency: ['USD', Validators.required] });
  expenseForm = this.fb.group({
    amount: [null as number | null, Validators.required],
    category: ['ads', Validators.required],
    expense_date: ['', Validators.required],
  });

  ngOnInit(): void {
    this.campaignId = Number(this.route.snapshot.paramMap.get('id'));
    this.orgId = this.orgCtx.activeOrganization()?.id ?? null;
    this.load();
  }

  load(): void {
    const orgId = this.orgId;
    if (orgId == null) return;
    this.loading = true;
    this.error = null;
    this.api.get(orgId, this.campaignId).subscribe({
      next: (c) => {
        this.campaign = c;
        this.api.getBudget(orgId, this.campaignId).subscribe({
          next: (b) => (this.budget = b),
          error: () => (this.budget = null),
        });
        this.api.listExpenses(orgId, this.campaignId).subscribe({
          next: (e) => (this.expenses = e || []),
          error: () => (this.expenses = []),
        });
        this.api.listApprovals(orgId, this.campaignId).subscribe({
          next: (a) => (this.approvals = a || []),
          error: () => (this.approvals = []),
        });
        this.api.getRoi(orgId, this.campaignId).subscribe({
          next: (r) => (this.roi = r),
          error: () => (this.roi = null),
        });
        this.loading = false;
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || e?.error?.message || 'Load failed';
        this.loading = false;
      },
    });
  }

  setBudget(): void {
    const orgId = this.orgId;
    if (orgId == null || this.budgetForm.invalid) return;
    const v = this.budgetForm.value;
    this.busy = true;
    this.api.setBudget(orgId, this.campaignId, { amount: v.amount!, currency: v.currency! }).subscribe({
      next: (b) => { this.budget = b; this.busy = false; this.success = 'Budget saved.'; },
      error: (e) => { this.error = e?.error?.detail?.message || 'Budget failed'; this.busy = false; },
    });
  }

  addExpense(): void {
    const orgId = this.orgId;
    if (orgId == null || this.expenseForm.invalid) return;
    const v = this.expenseForm.value;
    this.busy = true;
    this.api.addExpense(orgId, this.campaignId, {
      amount: v.amount!, currency: 'USD', category: v.category!, expense_date: v.expense_date!,
    }).subscribe({
      next: () => { this.expenseForm.reset({ category: 'ads' }); this.busy = false; this.success = 'Expense added.'; this.load(); },
      error: (e) => { this.error = e?.error?.detail?.message || 'Expense failed'; this.busy = false; },
    });
  }

  computeRoi(): void {
    const orgId = this.orgId;
    if (orgId == null) return;
    this.busy = true;
    this.api.computeRoi(orgId, this.campaignId).subscribe({
      next: (r) => { this.roi = r; this.busy = false; },
      error: (e) => { this.error = e?.error?.detail?.message || 'ROI compute failed'; this.busy = false; },
    });
  }

  requestApproval(): void {
    const orgId = this.orgId;
    if (orgId == null) return;
    this.busy = true;
    this.error = null;
    this.api.requestApproval(orgId, this.campaignId, { approval_type: 'launch' }).subscribe({
      next: () => { this.busy = false; this.success = 'Approval requested.'; this.load(); },
      error: (e) => { this.error = e?.error?.detail?.message || 'Approval request failed'; this.busy = false; },
    });
  }

  decide(approvalId: number, approved: boolean): void {
    const orgId = this.orgId;
    if (orgId == null) return;
    if (!approved && !confirm('Reject this campaign approval?')) return;
    this.busy = true;
    this.api.decideApproval(orgId, approvalId, { approved, reason: approved ? 'approved_ui' : 'rejected_ui' }).subscribe({
      next: () => { this.busy = false; this.success = approved ? 'Approved.' : 'Rejected.'; this.load(); },
      error: (e) => { this.error = e?.error?.detail?.message || 'Decision failed'; this.busy = false; },
    });
  }
}
