import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { CampaignsApiService } from '../services/campaigns-api.service';
import {
  Campaign, CampaignApproval, CampaignBudget, CampaignExpense, CampaignRoiSnapshot,
} from '../models/campaigns.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';

@Component({
  selector: 'app-campaign-detail',
  standalone: true,
  imports: [CommonModule, RouterLink, ReactiveFormsModule],
  template: `
    <div class="campaign-detail-page">
      <a routerLink="/campaigns">← Back to campaigns</a>

      @if (loading) { <p>Loading…</p> }
      @else if (campaign) {
        <h1>{{ campaign.name }}</h1>
        <p>Status: <span class="badge">{{ campaign.status }}</span></p>

        <section class="roi-section">
          <h2>ROI</h2>
          @if (roi) {
            @if (roi.status === 'available') {
              <p class="roi-value">ROI: {{ roi.roi_value | number:'1.2-2' }}</p>
              <p>Budget utilization: {{ (roi.budget_utilization || 0) * 100 | number:'1.0-0' }}%</p>
            } @else {
              <p class="roi-unavailable">No disponible</p>
              <p class="roi-reason">{{ roi.unavailable_reason }}</p>
            }
            @if (roi.engagement_lift) {
              <p>Engagement (streams): {{ roi.engagement_lift | number }} — not monetary</p>
            }
          } @else {
            <p class="roi-unavailable">No disponible — no snapshot yet</p>
            <button type="button" (click)="computeRoi()">Compute ROI</button>
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
              <button type="submit" [disabled]="budgetForm.invalid">Set Budget</button>
            </form>
          }
        </section>

        <section>
          <h2>Expenses</h2>
          <form [formGroup]="expenseForm" (ngSubmit)="addExpense()">
            <input formControlName="amount" type="number" placeholder="Amount" />
            <input formControlName="category" placeholder="Category" />
            <input formControlName="expense_date" type="date" />
            <button type="submit" [disabled]="expenseForm.invalid">Add Expense</button>
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
          @if (approvals.length === 0) { <p>No approval requests.</p> }
          @else {
            <ul>
              @for (a of approvals; track a.id) {
                <li>{{ a.approval_type }} — {{ a.status }} (requested {{ a.requested_at | date:'short' }})</li>
              }
            </ul>
          }
        </section>
      }
      @if (error) { <p class="error">{{ error }}</p> }
    </div>
  `,
})
export class CampaignDetailPage implements OnInit {
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
  error: string | null = null;
  campaignId = 0;

  budgetForm = this.fb.group({ amount: [null as number | null, Validators.required], currency: ['USD', Validators.required] });
  expenseForm = this.fb.group({
    amount: [null as number | null, Validators.required],
    category: ['ads', Validators.required],
    expense_date: ['', Validators.required],
  });

  ngOnInit(): void {
    this.campaignId = Number(this.route.snapshot.paramMap.get('id'));
    this.load();
  }

  load(): void {
    const orgId = this.orgCtx.activeOrganization()?.id;
    if (!orgId) return;
    this.loading = true;
    this.api.get(orgId, this.campaignId).subscribe({
      next: (c) => {
        this.campaign = c;
        this.api.getBudget(orgId, this.campaignId).subscribe((b) => (this.budget = b));
        this.api.listExpenses(orgId, this.campaignId).subscribe((e) => (this.expenses = e));
        this.api.listApprovals(orgId, this.campaignId).subscribe((a) => (this.approvals = a));
        this.api.getRoi(orgId, this.campaignId).subscribe((r) => (this.roi = r));
        this.loading = false;
      },
      error: (e) => { this.error = e?.error?.message || 'Load failed'; this.loading = false; },
    });
  }

  setBudget(): void {
    const orgId = this.orgCtx.activeOrganization()?.id;
    if (!orgId || this.budgetForm.invalid) return;
    const v = this.budgetForm.value;
    this.api.setBudget(orgId, this.campaignId, { amount: v.amount!, currency: v.currency! }).subscribe({
      next: (b) => { this.budget = b; },
      error: (e) => { this.error = e?.error?.message || 'Budget failed'; },
    });
  }

  addExpense(): void {
    const orgId = this.orgCtx.activeOrganization()?.id;
    if (!orgId || this.expenseForm.invalid) return;
    const v = this.expenseForm.value;
    this.api.addExpense(orgId, this.campaignId, {
      amount: v.amount!, currency: 'USD', category: v.category!, expense_date: v.expense_date!,
    }).subscribe({
      next: () => { this.expenseForm.reset({ category: 'ads' }); this.load(); },
      error: (e) => { this.error = e?.error?.message || 'Expense failed'; },
    });
  }

  computeRoi(): void {
    const orgId = this.orgCtx.activeOrganization()?.id;
    if (!orgId) return;
    this.api.computeRoi(orgId, this.campaignId).subscribe({
      next: (r) => { this.roi = r; },
      error: (e) => { this.error = e?.error?.message || 'ROI compute failed'; },
    });
  }
}
