import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ReportingApiService } from '../services/reporting-api.service';
import { BusinessDecision, DecisionAction, DecisionFollowUp } from '../models/reporting.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-decision-detail',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise decision-detail-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <a routerLink="/business-decisions" class="back-link">{{ 'reporting.decisions.back' | t:lang() }}</a>

        @if (loading) {
          <app-enterprise-loading-skeleton [rows]="4" />
        } @else if (error && !decision) {
          <app-enterprise-error-state [message]="error" (retry)="reload()" />
        } @else if (decision) {
          <app-enterprise-page-header [title]="decision.title">
            <app-enterprise-status-badge [status]="decision.status" />
          </app-enterprise-page-header>

          <p class="muted">{{ decision.proposal }}</p>

          <app-enterprise-action-bar>
            <button type="button" class="btn btn--primary" (click)="approve()">
              {{ 'decisions.detail.approve' | t:lang() }}
            </button>
            <button type="button" class="btn btn--secondary" (click)="complete()">
              {{ 'decisions.detail.complete' | t:lang() }}
            </button>
          </app-enterprise-action-bar>

          <app-enterprise-section-card [title]="'reporting.decisions.actions' | t:lang()">
            <div class="form-grid">
              <app-enterprise-form-field [label]="'reporting.decisions.actionTitle' | t:lang()">
                <input [(ngModel)]="actionTitle" class="input" />
              </app-enterprise-form-field>
              <div class="form-grid__actions">
                <button type="button" class="btn btn--secondary" (click)="addAction()">
                  {{ 'decisions.detail.addAction' | t:lang() }}
                </button>
              </div>
            </div>
            <ul class="ent-list">
              @for (a of actions; track a.id) {
                <li>{{ a.title }} — <app-enterprise-status-badge [status]="a.status" /></li>
              }
            </ul>
          </app-enterprise-section-card>

          <app-enterprise-section-card [title]="'reporting.decisions.followUps' | t:lang()">
            <div class="form-grid">
              <app-enterprise-form-field [label]="'reporting.decisions.note' | t:lang()">
                <input [(ngModel)]="note" class="input" />
              </app-enterprise-form-field>
              <div class="form-grid__actions">
                <button type="button" class="btn btn--secondary" (click)="addFollowUp()">
                  {{ 'decisions.detail.addFollowUp' | t:lang() }}
                </button>
              </div>
            </div>
            <ul class="ent-list">
              @for (f of followUps; track f.id) {
                <li>{{ f.note }}</li>
              }
            </ul>
          </app-enterprise-section-card>

          @if (error) {
            <app-enterprise-error-state [message]="error" />
          }
        }
      }
    </div>
  `,
})
export class DecisionDetailPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(ReportingApiService);
  private orgCtx = inject(OrganizationContextService);
  private route = inject(ActivatedRoute);

  orgId: number | null = null;
  id = 0;
  decision: BusinessDecision | null = null;
  actions: DecisionAction[] = [];
  followUps: DecisionFollowUp[] = [];
  actionTitle = '';
  note = '';
  loading = false;
  error = '';

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    this.id = Number(this.route.snapshot.paramMap.get('id'));
    if (this.orgId && this.id) this.reload();
  }

  reload(): void {
    if (!this.orgId) return;
    this.loading = true;
    this.error = '';
    this.api.getDecision(this.orgId, this.id).subscribe({
      next: (d) => {
        this.decision = d;
        this.loading = false;
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || this.i18n.t('common.failed');
        this.loading = false;
      },
    });
    this.api.listActions(this.orgId, this.id).subscribe({ next: (a) => (this.actions = a) });
    this.api.listFollowUps(this.orgId, this.id).subscribe({ next: (f) => (this.followUps = f) });
  }

  approve(): void {
    if (!this.orgId) return;
    this.api.approveDecision(this.orgId, this.id).subscribe({
      next: (d) => (this.decision = d),
      error: (e) => (this.error = e?.error?.detail?.message || this.i18n.t('common.failed')),
    });
  }

  complete(): void {
    if (!this.orgId) return;
    this.api.completeDecision(this.orgId, this.id).subscribe({
      next: (d) => (this.decision = d),
      error: (e) => (this.error = e?.error?.detail?.message || this.i18n.t('common.failed')),
    });
  }

  addAction(): void {
    if (!this.orgId || !this.actionTitle) return;
    this.api.addAction(this.orgId, this.id, this.actionTitle).subscribe({
      next: () => {
        this.actionTitle = '';
        this.reload();
      },
      error: (e) => (this.error = e?.error?.detail?.message || this.i18n.t('common.failed')),
    });
  }

  addFollowUp(): void {
    if (!this.orgId || !this.note) return;
    this.api.addFollowUp(this.orgId, this.id, this.note).subscribe({
      next: () => {
        this.note = '';
        this.reload();
      },
      error: (e) => (this.error = e?.error?.detail?.message || this.i18n.t('common.failed')),
    });
  }
}
