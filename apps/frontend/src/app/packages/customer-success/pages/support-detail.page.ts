import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { CustomerSuccessApiService } from '../services/customer-success-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { OrganizationsApiService } from '../../organizations/services/organizations-api.service';
import { Membership } from '../../organizations/models/organization.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ConfirmDialogService } from '../../../shared/services/confirm-dialog.service';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import { userFacingHttpError } from '../../../core/i18n/user-facing-error';

interface SupportCase {
  id: number;
  subject?: string;
  status?: string;
  priority?: string;
  assignee_user_id?: number | null;
}

@Component({
  selector: 'app-support-detail',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise support-detail-page">
      @if (!orgId) {
        <app-enterprise-org-required />
      } @else {
        <a routerLink="/support" class="back-link">{{ 'support.detail.back' | t:lang() }}</a>

        @if (loading) {
          <app-enterprise-loading-skeleton [rows]="4" />
        } @else if (error && !caseData) {
          <app-enterprise-error-state [message]="error" (retry)="reload()" />
        } @else if (!caseData) {
          <app-enterprise-empty-state [title]="'support.detail.notFound' | t:lang()" />
        } @else {
          @if (error) {
            <app-enterprise-error-state [message]="error" />
          }
          @if (success) {
            <div class="alert alert--success" role="status">{{ success }}</div>
          }

          <app-enterprise-page-header [title]="caseData.subject || ('common.notAvailable' | t:lang())">
            <app-enterprise-status-badge [status]="caseData.status || 'unknown'" />
            <span class="muted">/ {{ caseData.priority || ('common.notAvailable' | t:lang()) }}</span>
            @if (caseData.assignee_user_id) {
              <span class="muted">
                · {{ 'support.detail.assignee' | t:lang() }}: {{ memberLabel(caseData.assignee_user_id) }}
              </span>
            }
          </app-enterprise-page-header>

          <app-enterprise-action-bar>
            @if (canTriage) {
              <button type="button" class="btn btn--secondary" (click)="triage()" [disabled]="busy">
                {{ 'support.detail.triage' | t:lang() }}
              </button>
            }
            @if (canEscalate) {
              <button type="button" class="btn btn--secondary" (click)="escalate()" [disabled]="busy">
                {{ 'support.detail.escalate' | t:lang() }}
              </button>
            }
            @if (canResolve) {
              <button type="button" class="btn btn--primary" (click)="resolve()" [disabled]="busy">
                {{ 'support.detail.resolve' | t:lang() }}
              </button>
            }
            @if (canClose) {
              <button type="button" class="btn btn--secondary" (click)="closeCase()" [disabled]="busy">
                {{ 'support.detail.close' | t:lang() }}
              </button>
            }
            @if (canReopen) {
              <button type="button" class="btn btn--primary" (click)="reopen()" [disabled]="busy">
                {{ 'support.detail.reopen' | t:lang() }}
              </button>
            }
          </app-enterprise-action-bar>

          @if (canAssign) {
            <app-enterprise-section-card [title]="'support.detail.assignTitle' | t:lang()">
              <p class="muted">{{ 'support.detail.assignHint' | t:lang() }}</p>
              <div class="form-grid">
                <app-enterprise-form-field [label]="'support.detail.assignee' | t:lang()" [required]="true">
                  <select class="input" [(ngModel)]="assigneeUserId" name="assignee">
                    <option [ngValue]="null">{{ 'support.detail.selectAssignee' | t:lang() }}</option>
                    @for (m of members; track m.user_id) {
                      <option [ngValue]="m.user_id">{{ memberLabel(m.user_id) }}</option>
                    }
                  </select>
                </app-enterprise-form-field>
                <div class="form-grid__actions">
                  <button
                    type="button"
                    class="btn btn--primary"
                    (click)="assign()"
                    [disabled]="busy || assigneeUserId == null"
                  >
                    {{ 'support.detail.assign' | t:lang() }}
                  </button>
                </div>
              </div>
            </app-enterprise-section-card>
          }

          <app-enterprise-section-card [title]="'support.detail.messages' | t:lang()">
            @if (messages.length === 0) {
              <app-enterprise-empty-state [title]="'support.detail.noMessages' | t:lang()" />
            } @else {
              <ul class="ent-list">
                @for (m of messages; track $index) {
                  <li [class.internal]="$any(m).is_internal">
                    @if ($any(m).is_internal) {
                      <app-enterprise-status-badge
                        status="internal"
                        [label]="'support.detail.internalTag' | t:lang()"
                      />
                    }
                    {{ $any(m).body || ('common.notAvailable' | t:lang()) }}
                  </li>
                }
              </ul>
            }
            @if (canRespond || canInternalNote) {
              <div class="form-grid">
                <app-enterprise-form-field [label]="'support.detail.messagePlaceholder' | t:lang()">
                  <input [(ngModel)]="body" class="input" name="body" />
                </app-enterprise-form-field>
                <div class="form-grid__actions">
                  @if (canRespond) {
                    <button
                      type="button"
                      class="btn btn--primary"
                      (click)="send(false)"
                      [disabled]="busy || !body.trim()"
                    >
                      {{ 'support.detail.send' | t:lang() }}
                    </button>
                  }
                  @if (canInternalNote) {
                    <button
                      type="button"
                      class="btn btn--secondary"
                      (click)="send(true)"
                      [disabled]="busy || !body.trim()"
                    >
                      {{ 'support.detail.internalNote' | t:lang() }}
                    </button>
                  }
                </div>
              </div>
            }
          </app-enterprise-section-card>
        }
      }
    </div>
  `,
})
export class SupportDetailPage implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private api = inject(CustomerSuccessApiService);
  private orgCtx = inject(OrganizationContextService);
  private orgApi = inject(OrganizationsApiService);
  private route = inject(ActivatedRoute);
  private confirmDlg = inject(ConfirmDialogService);
  orgId: number | null = null;
  id = 0;
  caseData: SupportCase | null = null;
  messages: unknown[] = [];
  members: Membership[] = [];
  assigneeUserId: number | null = null;
  body = '';
  error = '';
  success = '';
  loading = false;
  busy = false;

  get status(): string {
    return this.caseData?.status || '';
  }

  get canTriage(): boolean {
    return this.orgCtx.hasPermission('support.assign') && ['open', 'reopened'].includes(this.status);
  }

  get canAssign(): boolean {
    return (
      this.orgCtx.hasPermission('support.assign') &&
      !['closed', 'resolved'].includes(this.status) &&
      [
        'open',
        'triaged',
        'reopened',
        'assigned',
        'escalated',
        'in_progress',
        'waiting_customer',
      ].includes(this.status)
    );
  }

  get canEscalate(): boolean {
    return (
      this.orgCtx.hasPermission('support.escalate') &&
      ['triaged', 'assigned', 'in_progress', 'waiting_customer', 'reopened'].includes(this.status)
    );
  }

  get canResolve(): boolean {
    return this.orgCtx.hasPermission('support.resolve') && this.status !== 'closed';
  }

  get canClose(): boolean {
    return (
      this.orgCtx.hasPermission('support.close') &&
      ['resolved', 'escalated', 'in_progress', 'assigned', 'waiting_customer'].includes(this.status)
    );
  }

  get canReopen(): boolean {
    return this.orgCtx.hasPermission('support.close') && ['closed', 'resolved'].includes(this.status);
  }

  get canRespond(): boolean {
    return this.orgCtx.hasPermission('support.respond') && !['closed'].includes(this.status);
  }

  get canInternalNote(): boolean {
    return this.orgCtx.hasPermission('support.internal_note') && !['closed'].includes(this.status);
  }

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    this.id = Number(this.route.snapshot.paramMap.get('id'));
    if (this.orgId && this.id) {
      this.reload();
      this.loadMembers();
    } else {
      this.error = this.i18n.t('common.orgRequiredContext');
    }
  }

  memberLabel(userId: number): string {
    const m = this.members.find((x) => x.user_id === userId);
    const name = m?.user?.display_name?.trim();
    if (name) return name;
    const email = m?.user?.email?.trim();
    if (email) return email;
    return `${this.i18n.t('support.detail.user')} ${userId}`;
  }

  private loadMembers(): void {
    const orgId = this.orgId;
    if (orgId == null) return;
    this.orgApi.listMembers(orgId, 1, 100).subscribe({
      next: (page) => {
        this.members = (page.items || []).filter((m) => m.status === 'active');
      },
      error: () => {
        this.members = [];
      },
    });
  }

  reload(): void {
    const orgId = this.orgId;
    if (orgId == null) return;
    this.loading = true;
    this.error = '';
    this.api.getCase(orgId, this.id).subscribe({
      next: (c) => {
        this.caseData = c as SupportCase;
        this.assigneeUserId = this.caseData.assignee_user_id ?? null;
        this.loading = false;
      },
      error: (e) => {
        this.error = userFacingHttpError(this.i18n, e);
        this.loading = false;
      },
    });
    const includeInternal = this.orgCtx.hasPermission('support.internal_note');
    this.api.listMessages(orgId, this.id, includeInternal).subscribe({
      next: (m) => (this.messages = m || []),
      error: () => {
        /* keep case visible even if messages fail */
      },
    });
  }

  private runAction(fn: () => ReturnType<CustomerSuccessApiService['triage']>, successKey: string): void {
    const orgId = this.orgId;
    if (orgId == null) return;
    this.busy = true;
    this.error = '';
    this.success = '';
    fn().subscribe({
      next: () => {
        this.busy = false;
        this.success = this.i18n.t(successKey);
        this.reload();
      },
      error: (e) => {
        this.error = userFacingHttpError(this.i18n, e);
        this.busy = false;
      },
    });
  }

  triage(): void {
    const orgId = this.orgId;
    if (orgId == null) return;
    this.runAction(() => this.api.triage(orgId, this.id), 'support.detail.triaged');
  }

  assign(): void {
    const orgId = this.orgId;
    if (orgId == null || this.assigneeUserId == null) return;
    const assignee = this.assigneeUserId;
    this.runAction(() => this.api.assign(orgId, this.id, assignee), 'support.detail.assigned');
  }

  escalate(): void {
    const orgId = this.orgId;
    if (orgId == null) return;
    this.runAction(() => this.api.escalate(orgId, this.id), 'support.detail.escalated');
  }

  reopen(): void {
    const orgId = this.orgId;
    if (orgId == null) return;
    this.runAction(() => this.api.reopen(orgId, this.id), 'support.detail.reopened');
  }

  send(internal: boolean): void {
    const orgId = this.orgId;
    if (orgId == null || !this.body.trim()) return;
    this.busy = true;
    this.error = '';
    const req = internal
      ? this.api.addInternalNote(orgId, this.id, this.body)
      : this.api.addMessage(orgId, this.id, this.body);
    req.subscribe({
      next: () => {
        this.body = '';
        this.busy = false;
        this.success = internal
          ? this.i18n.t('support.detail.internalSent')
          : this.i18n.t('support.detail.messageSent');
        this.reload();
      },
      error: (e) => {
        this.error = userFacingHttpError(this.i18n, e);
        this.busy = false;
      },
    });
  }

  resolve(): void {
    const orgId = this.orgId;
    if (orgId == null) return;
    this.runAction(() => this.api.resolve(orgId, this.id), 'support.detail.resolved');
  }

  async closeCase(): Promise<void> {
    const orgId = this.orgId;
    if (orgId == null) return;
    const ok = await this.confirmDlg.open({
      title: this.i18n.t('support.detail.closeTitle'),
      message: this.i18n.t('support.detail.closeConfirm'),
      confirmLabel: this.i18n.t('support.detail.close'),
      cancelLabel: this.i18n.t('common.cancel'),
      danger: true,
    });
    if (!ok) return;
    this.runAction(() => this.api.close(orgId, this.id), 'support.detail.closed');
  }
}
