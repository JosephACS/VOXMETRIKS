import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { ReportingApiService } from '../services/reporting-api.service';
import { BusinessDecision, DecisionAction, DecisionFollowUp } from '../models/reporting.models';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';

import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { StatusLabelPipe } from '../../../shared/pipes/status-label.pipe';
import { LocaleDatePipe, LocaleMoneyPipe } from '../../../shared/pipes/locale-format.pipe';

@Component({
  selector: 'app-decision-detail',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, TranslatePipe, StatusLabelPipe, LocaleMoneyPipe, LocaleDatePipe],
  template: `
    <div class="page">
      <p><a routerLink="/business-decisions">← Decisions</a></p>
      @if (loading) { <p>{{ 'common.loading' | t:lang() }}</p> }
      @else if (error) { <p class="error">{{ error }}</p> }
      @else if (decision) {
        <h1>{{ decision.title }}</h1>
        <p>{{ decision.proposal }}</p>
        <p>Status: {{ decision.status }}</p>
        <button type="button" (click)="approve()">Approve</button>
        <button type="button" (click)="complete()">Complete</button>
        <h2>Actions</h2>
        <input [(ngModel)]="actionTitle" placeholder="action title" />
        <button type="button" (click)="addAction()">Add action</button>
        <ul>
          @for (a of actions; track a.id) {
            <li>{{ a.title }} — {{ a.status }}</li>
          }
        </ul>
        <h2>Follow-ups</h2>
        <input [(ngModel)]="note" placeholder="note" />
        <button type="button" (click)="addFollowUp()">Add follow-up</button>
        <ul>
          @for (f of followUps; track f.id) {
            <li>{{ f.note }}</li>
          }
        </ul>
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
    this.orgId = this.orgCtx.activeOrganization()?.id ?? null;
    this.id = Number(this.route.snapshot.paramMap.get('id'));
    if (this.orgId && this.id) this.reload();
  }

  reload(): void {
    if (!this.orgId) return;
    this.loading = true;
    this.api.getDecision(this.orgId, this.id).subscribe({
      next: (d) => {
        this.decision = d;
        this.loading = false;
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || 'Denied or not found';
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
      error: (e) => (this.error = e?.error?.detail?.message || 'Approve failed'),
    });
  }

  complete(): void {
    if (!this.orgId) return;
    this.api.completeDecision(this.orgId, this.id).subscribe({
      next: (d) => (this.decision = d),
      error: (e) => (this.error = e?.error?.detail?.message || 'Complete failed'),
    });
  }

  addAction(): void {
    if (!this.orgId || !this.actionTitle) return;
    this.api.addAction(this.orgId, this.id, this.actionTitle).subscribe({
      next: () => {
        this.actionTitle = '';
        this.reload();
      },
      error: (e) => (this.error = e?.error?.detail?.message || 'Action failed'),
    });
  }

  addFollowUp(): void {
    if (!this.orgId || !this.note) return;
    this.api.addFollowUp(this.orgId, this.id, this.note).subscribe({
      next: () => {
        this.note = '';
        this.reload();
      },
      error: (e) => (this.error = e?.error?.detail?.message || 'Follow-up failed'),
    });
  }
}
