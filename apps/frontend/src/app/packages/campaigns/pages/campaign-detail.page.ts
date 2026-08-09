import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { CampaignsApiService } from '../services/campaigns-api.service';
import {
  Campaign,
  CampaignApproval,
  CampaignBudget,
  CampaignExpense,
  CampaignRoiSnapshot,
} from '../models/campaigns.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { LocaleDatePipe, LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import { ConfirmDialogService } from '../../../shared/services/confirm-dialog.service';

@Component({
  selector: 'app-campaign-detail',
  standalone: true,
  imports: [
    CommonModule,
    RouterLink,
    ReactiveFormsModule,
    TranslatePipe,
    LocaleMoneyPipe,
    LocaleDatePipe,
    ...ENTERPRISE_UI_IMPORTS,
  ],
  template: `
    <div class="vx-enterprise campaign-detail-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <a routerLink="/campaigns" class="back-link">{{ 'campaigns.detail.back' | t:lang() }}</a>

        @if (loading) {
          <app-enterprise-loading-skeleton [rows]="4" />
        } @else if (campaign) {
          <app-enterprise-page-header [title]="campaign.name">
            <app-enterprise-status-badge [status]="campaign.status" />
          </app-enterprise-page-header>
          <p class="muted" data-testid="campaign-market">
            {{ 'campaigns.list.market' | t:lang() }}:
            {{ campaign.market || ('common.notAvailable' | t:lang()) }}
          </p>

          <div class="vx-summary-strip" data-testid="campaign-summary-strip">
            <div class="kpi-card">
              <h3>{{ 'campaigns.detail.budgetTitle' | t:lang() }}</h3>
              @if (budget) {
                <p class="kpi-value">{{ budget.amount | localeMoney: budget.currency }}</p>
              } @else {
                <p class="kpi-null">{{ 'common.notAvailable' | t:lang() }}</p>
              }
            </div>
            <div class="kpi-card">
              <h3>{{ 'campaigns.detail.spendTitle' | t:lang() }}</h3>
              <p class="kpi-value">{{ expensesTotal | localeMoney: 'USD' }}</p>
            </div>
            <div class="kpi-card">
              <h3>{{ 'campaigns.detail.roiSimulated' | t:lang() }}</h3>
              @if (roi?.status === 'available' && roi?.roi_value != null) {
                <p class="kpi-value">{{ roi!.roi_value | number: '1.2-2' }}</p>
              } @else {
                <p class="kpi-null">{{ 'common.notAvailable' | t:lang() }}</p>
              }
              <span class="vx-sim-badge">{{ 'campaigns.detail.academicEstimate' | t:lang() }}</span>
            </div>
          </div>

          <div class="vx-sim-callout" role="note" data-testid="campaign-roi-disclosure">
            {{ 'campaigns.detail.roiDisclosure' | t:lang() }}
          </div>

          <app-enterprise-section-card [title]="'campaigns.detail.roiTitle' | t:lang()">
            @if (roi) {
              @if (roi.status === 'available' && roi.roi_value != null) {
                <p class="roi-value">
                  {{ 'campaigns.detail.roiSimulated' | t:lang() }}:
                  {{ roi.roi_value | number: '1.2-2' }}
                </p>
                @if (roi.budget_utilization != null) {
                  <p>
                    {{ 'campaigns.detail.budgetUtilization' | t:lang() }}:
                    {{ roi.budget_utilization * 100 | number: '1.0-0' }}%
                  </p>
                }
              } @else {
                <p class="muted">{{ 'common.notAvailable' | t:lang() }}</p>
                <p class="muted">
                  {{ roi.unavailable_reason || ('campaigns.detail.roiUnavailableReason' | t:lang()) }}
                </p>
              }
              @if (roi.engagement_lift != null) {
                <p>
                  {{ 'campaigns.detail.engagementLift' | t:lang() }}:
                  {{ roi.engagement_lift | number }} —
                  {{ 'campaigns.detail.engagementNotMonetary' | t:lang() }}
                </p>
              }
            } @else {
              <p class="muted">
                {{ 'common.notAvailable' | t:lang() }} —
                {{ 'campaigns.detail.noRoiSnapshot' | t:lang() }}
              </p>
              <button type="button" class="btn btn--secondary" (click)="computeRoi()" [disabled]="busy">
                {{ 'campaigns.detail.roi' | t:lang() }}
              </button>
            }
          </app-enterprise-section-card>

          <app-enterprise-section-card [title]="'campaigns.detail.budgetTitle' | t:lang()">
            @if (budget) {
              <p>{{ budget.amount | localeMoney: budget.currency }}</p>
            } @else {
              <form [formGroup]="budgetForm" (ngSubmit)="setBudget()" class="form-grid">
                <app-enterprise-form-field [label]="'common.amount' | t:lang()" [required]="true">
                  <input formControlName="amount" type="number" class="input" />
                </app-enterprise-form-field>
                <app-enterprise-form-field [label]="'common.currency' | t:lang()" [required]="true">
                  <input formControlName="currency" class="input" />
                </app-enterprise-form-field>
                <div class="form-grid__actions">
                  <button
                    type="submit"
                    class="btn btn--primary"
                    [disabled]="budgetForm.invalid || busy"
                  >
                    {{ 'campaigns.detail.budget' | t:lang() }}
                  </button>
                </div>
              </form>
            }
          </app-enterprise-section-card>

          <app-enterprise-section-card [title]="'campaigns.detail.expensesTitle' | t:lang()">
            <form [formGroup]="expenseForm" (ngSubmit)="addExpense()" class="form-grid">
              <app-enterprise-form-field [label]="'common.amount' | t:lang()" [required]="true">
                <input formControlName="amount" type="number" class="input" />
              </app-enterprise-form-field>
              <app-enterprise-form-field [label]="'campaigns.detail.category' | t:lang()" [required]="true">
                <input formControlName="category" class="input" />
              </app-enterprise-form-field>
              <app-enterprise-form-field
                [label]="'campaigns.detail.expenseDate' | t:lang()"
                [required]="true"
              >
                <input formControlName="expense_date" type="date" class="input" />
              </app-enterprise-form-field>
              <div class="form-grid__actions">
                <button
                  type="submit"
                  class="btn btn--primary"
                  [disabled]="expenseForm.invalid || busy"
                >
                  {{ 'campaigns.detail.addExpense' | t:lang() }}
                </button>
              </div>
            </form>

            @if (expenses.length === 0) {
              <p class="muted">{{ 'campaigns.detail.noExpenses' | t:lang() }}</p>
            } @else {
              <app-enterprise-data-table>
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>{{ 'common.date' | t:lang() }}</th>
                      <th>{{ 'campaigns.detail.category' | t:lang() }}</th>
                      <th>{{ 'common.amount' | t:lang() }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    @for (e of expenses; track e.id) {
                      <tr>
                        <td>{{ e.expense_date | localeDate }}</td>
                        <td>{{ e.category }}</td>
                        <td>{{ e.amount | localeMoney: e.currency }}</td>
                      </tr>
                    }
                  </tbody>
                </table>
              </app-enterprise-data-table>
            }
          </app-enterprise-section-card>

          <app-enterprise-section-card [title]="'campaigns.detail.approvalsTitle' | t:lang()">
            <div class="form-grid__actions">
              <button
                type="button"
                class="btn btn--secondary"
                (click)="requestApproval()"
                [disabled]="busy"
              >
                {{ 'campaigns.detail.requestApproval' | t:lang() }}
              </button>
            </div>
            @if (approvals.length === 0) {
              <p class="muted">{{ 'campaigns.detail.noApprovals' | t:lang() }}</p>
            } @else {
              <app-enterprise-data-table>
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>{{ 'common.type' | t:lang() }}</th>
                      <th>{{ 'common.status' | t:lang() }}</th>
                      <th>{{ 'common.date' | t:lang() }}</th>
                      <th>{{ 'common.actions' | t:lang() }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    @for (a of approvals; track a.id) {
                      <tr>
                        <td>{{ a.approval_type }}</td>
                        <td><app-enterprise-status-badge [status]="a.status" /></td>
                        <td>
                          {{ 'campaigns.detail.requested' | t:lang() }}
                          {{ a.requested_at | localeDate: true }}
                        </td>
                        <td>
                          @if (a.status === 'pending') {
                            <button
                              type="button"
                              class="btn btn--primary btn--sm"
                              (click)="decide(a.id, true)"
                              [disabled]="busy"
                            >
                              {{ 'campaigns.detail.approve' | t:lang() }}
                            </button>
                            <button
                              type="button"
                              class="btn btn--ghost btn--sm"
                              (click)="decide(a.id, false)"
                              [disabled]="busy"
                            >
                              {{ 'campaigns.detail.reject' | t:lang() }}
                            </button>
                          }
                        </td>
                      </tr>
                    }
                  </tbody>
                </table>
              </app-enterprise-data-table>
            }
          </app-enterprise-section-card>
        } @else if (!loading) {
          <app-enterprise-empty-state [title]="'campaigns.detail.notFound' | t:lang()" />
        }

        @if (error) {
          <app-enterprise-error-state [message]="error" (retry)="load()" />
        }
        @if (success) {
          <p class="success">{{ success }}</p>
        }
      }
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
  private confirmDlg = inject(ConfirmDialogService);

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

  budgetForm = this.fb.group({
    amount: [null as number | null, Validators.required],
    currency: ['USD', Validators.required],
  });
  expenseForm = this.fb.group({
    amount: [null as number | null, Validators.required],
    category: ['ads', Validators.required],
    expense_date: ['', Validators.required],
  });

  get expensesTotal(): number {
    return this.expenses.reduce((sum, e) => sum + (Number(e.amount) || 0), 0);
  }

  ngOnInit(): void {
    this.campaignId = Number(this.route.snapshot.paramMap.get('id'));
    this.orgId = this.orgCtx.organizationId();
    if (!this.orgId) return;
    this.load();
  }

  load(): void {
    const orgId = this.orgCtx.organizationId();
    this.orgId = orgId;
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
        this.error = e?.error?.detail?.message || e?.error?.message || this.i18n.t('common.failed');
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
      next: (b) => {
        this.budget = b;
        this.busy = false;
        this.success = this.i18n.t('campaigns.detail.budgetSaved');
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || this.i18n.t('common.failed');
        this.busy = false;
      },
    });
  }

  addExpense(): void {
    const orgId = this.orgId;
    if (orgId == null || this.expenseForm.invalid) return;
    const v = this.expenseForm.value;
    this.busy = true;
    this.api
      .addExpense(orgId, this.campaignId, {
        amount: v.amount!,
        currency: 'USD',
        category: v.category!,
        expense_date: v.expense_date!,
      })
      .subscribe({
        next: () => {
          this.expenseForm.reset({ category: 'ads' });
          this.busy = false;
          this.success = this.i18n.t('campaigns.detail.expenseAdded');
          this.load();
        },
        error: (e) => {
          this.error = e?.error?.detail?.message || this.i18n.t('common.failed');
          this.busy = false;
        },
      });
  }

  computeRoi(): void {
    const orgId = this.orgId;
    if (orgId == null) return;
    this.busy = true;
    this.api.computeRoi(orgId, this.campaignId).subscribe({
      next: (r) => {
        this.roi = r;
        this.busy = false;
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || this.i18n.t('common.failed');
        this.busy = false;
      },
    });
  }

  requestApproval(): void {
    const orgId = this.orgId;
    if (orgId == null) return;
    this.busy = true;
    this.error = null;
    this.api.requestApproval(orgId, this.campaignId, { approval_type: 'launch' }).subscribe({
      next: () => {
        this.busy = false;
        this.success = this.i18n.t('campaigns.detail.approvalRequested');
        this.load();
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || this.i18n.t('common.failed');
        this.busy = false;
      },
    });
  }

  async decide(approvalId: number, approved: boolean): Promise<void> {
    const orgId = this.orgId;
    if (orgId == null) return;
    if (!approved) {
      const ok = await this.confirmDlg.open({
        title: this.i18n.t('common.confirm'),
        message: this.i18n.t('campaigns.detail.rejectApprovalConfirm'),
        confirmLabel: this.i18n.t('campaigns.detail.reject'),
        cancelLabel: this.i18n.t('common.cancel'),
        danger: true,
      });
      if (!ok) return;
    }
    this.busy = true;
    this.api
      .decideApproval(orgId, approvalId, {
        approved,
        reason: approved ? 'approved_ui' : 'rejected_ui',
      })
      .subscribe({
        next: () => {
          this.busy = false;
          this.success = approved
            ? this.i18n.t('campaigns.detail.approved')
            : this.i18n.t('campaigns.detail.rejected');
          this.load();
        },
        error: (e) => {
          this.error = e?.error?.detail?.message || this.i18n.t('common.failed');
          this.busy = false;
        },
      });
  }
}
