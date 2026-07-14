import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { CustomerSuccessApiService } from '../services/customer-success-api.service';
import { OrganizationContextService } from '../../organizations/services/organization-context.service';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ConfirmDialogService } from '../../../shared/services/confirm-dialog.service';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

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

          <app-enterprise-page-header [title]="$any(caseData).subject || ('common.notAvailable' | t:lang())">
            <app-enterprise-status-badge [status]="$any(caseData).status || 'unknown'" />
            <span class="muted">/ {{ $any(caseData).priority || ('common.notAvailable' | t:lang()) }}</span>
          </app-enterprise-page-header>

          <app-enterprise-action-bar>
            <button type="button" class="btn btn--primary" (click)="resolve()" [disabled]="busy">
              {{ 'support.detail.resolve' | t:lang() }}
            </button>
            <button type="button" class="btn btn--secondary" (click)="closeCase()" [disabled]="busy">
              {{ 'support.detail.close' | t:lang() }}
            </button>
          </app-enterprise-action-bar>

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
            <div class="form-grid">
              <app-enterprise-form-field [label]="'support.detail.messagePlaceholder' | t:lang()">
                <input [(ngModel)]="body" class="input" name="body" />
              </app-enterprise-form-field>
              <div class="form-grid__actions">
                <button
                  type="button"
                  class="btn btn--primary"
                  (click)="send(false)"
                  [disabled]="busy || !body.trim()"
                >
                  {{ 'support.detail.send' | t:lang() }}
                </button>
                <button
                  type="button"
                  class="btn btn--secondary"
                  (click)="send(true)"
                  [disabled]="busy || !body.trim()"
                >
                  {{ 'support.detail.internalNote' | t:lang() }}
                </button>
              </div>
            </div>
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
  private route = inject(ActivatedRoute);
  private confirmDlg = inject(ConfirmDialogService);
  orgId: number | null = null;
  id = 0;
  caseData: unknown = null;
  messages: unknown[] = [];
  body = '';
  error = '';
  success = '';
  loading = false;
  busy = false;

  ngOnInit(): void {
    this.orgId = this.orgCtx.organizationId();
    this.id = Number(this.route.snapshot.paramMap.get('id'));
    if (this.orgId && this.id) this.reload();
    else this.error = this.i18n.t('common.orgRequiredContext');
  }

  reload(): void {
    const orgId = this.orgId;
    if (orgId == null) return;
    this.loading = true;
    this.error = '';
    this.api.getCase(orgId, this.id).subscribe({
      next: (c) => {
        this.caseData = c;
        this.loading = false;
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || this.i18n.t('common.loadFailed');
        this.loading = false;
      },
    });
    this.api.listMessages(orgId, this.id, true).subscribe({
      next: (m) => (this.messages = m || []),
      error: () => {
        /* keep case visible even if messages fail */
      },
    });
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
        this.error = e?.error?.detail?.message || this.i18n.t('common.actionFailed');
        this.busy = false;
      },
    });
  }

  resolve(): void {
    const orgId = this.orgId;
    if (orgId == null) return;
    this.busy = true;
    this.error = '';
    this.api.resolve(orgId, this.id).subscribe({
      next: () => {
        this.busy = false;
        this.success = this.i18n.t('support.detail.resolved');
        this.reload();
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || this.i18n.t('common.actionFailed');
        this.busy = false;
      },
    });
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
    this.busy = true;
    this.error = '';
    this.api.close(orgId, this.id).subscribe({
      next: () => {
        this.busy = false;
        this.success = this.i18n.t('support.detail.closed');
        this.reload();
      },
      error: (e) => {
        this.error = e?.error?.detail?.message || this.i18n.t('common.actionFailed');
        this.busy = false;
      },
    });
  }
}
