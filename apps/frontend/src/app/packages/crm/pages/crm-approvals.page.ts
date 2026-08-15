import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { firstValueFrom } from 'rxjs';
import { CrmApiError, CrmApiService } from '../services/crm-api.service';
import { ApprovalRequest } from '../models/crm.models';
import { I18nService } from '../../../core/services/i18n.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { LocaleDatePipe } from '../../../shared/pipes/locale-format.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-crm-approvals-page',
  standalone: true,
  imports: [CommonModule, FormsModule, TranslatePipe, LocaleDatePipe, ...ENTERPRISE_UI_IMPORTS],
  styleUrls: ['../styles/crm.css'],
  template: `
    <div class="vx-enterprise crm-page" data-testid="crm-approvals-page">
      <app-enterprise-page-header
        [title]="'crm.approvals.title' | t:lang()"
        [subtitle]="'crm.approvals.subtitle' | t:lang()"
      />

      @if (error()) {
        <app-enterprise-error-state [message]="error()!" (retry)="load()" />
      }
      @if (success()) {
        <div class="alert alert--success" role="status">{{ success() }}</div>
      }

      @if (pendingReview()) {
        <app-enterprise-section-card [title]="'common.confirm' | t:lang()">
          <form class="form-grid" (ngSubmit)="confirmReview()">
            <app-enterprise-form-field [label]="'common.notes' | t:lang()">
              <textarea
                class="input"
                rows="2"
                [(ngModel)]="reviewNote"
                name="reviewNote"
                [disabled]="saving()"
              ></textarea>
            </app-enterprise-form-field>
            <app-enterprise-action-bar>
              <button type="button" class="btn btn--ghost" (click)="cancelReview()" [disabled]="saving()">
                {{ 'common.cancel' | t:lang() }}
              </button>
              <button type="submit" class="btn btn--primary" [disabled]="saving()">
                {{ (saving() ? 'common.saving' : 'common.confirm') | t:lang() }}
              </button>
            </app-enterprise-action-bar>
          </form>
        </app-enterprise-section-card>
      }

      @if (loading()) {
        <app-enterprise-loading-skeleton [rows]="4" />
      } @else if (!items().length) {
        <app-enterprise-empty-state [title]="'crm.approvals.empty' | t:lang()" />
      } @else {
        <app-enterprise-data-table>
          <table class="data-table">
            <thead>
              <tr>
                <th>{{ 'common.id' | t:lang() }}</th>
                <th>{{ 'common.type' | t:lang() }}</th>
                <th>{{ 'crm.approvals.object' | t:lang() }}</th>
                <th>{{ 'common.reason' | t:lang() }}</th>
                <th>{{ 'crm.approvals.threshold' | t:lang() }}</th>
                <th>{{ 'common.status' | t:lang() }}</th>
                <th>{{ 'crm.approvals.requested' | t:lang() }}</th>
                <th>{{ 'common.actions' | t:lang() }}</th>
              </tr>
            </thead>
            <tbody>
              @for (a of items(); track a.id) {
                <tr>
                  <td>{{ a.id }}</td>
                  <td>{{ a.object_type }}</td>
                  <td>#{{ a.object_id }}</td>
                  <td>{{ a.reason || ('common.notAvailable' | t:lang()) }}</td>
                  <td>
                    @if (a.threshold_ref != null) {
                      {{ a.threshold_ref | number: '1.0-2' }}%
                    } @else {
                      {{ 'common.notAvailable' | t:lang() }}
                    }
                  </td>
                  <td><app-enterprise-status-badge [status]="a.status" /></td>
                  <td class="muted">{{ a.requested_at | localeDate:true }}</td>
                  <td>
                    @if (a.status === 'pending') {
                      <app-enterprise-action-bar>
                        <button type="button" class="btn btn--sm btn--primary" [disabled]="saving()" (click)="review(a.id, 'approve')">
                          {{ 'common.approve' | t:lang() }}
                        </button>
                        <button type="button" class="btn btn--sm btn--danger" [disabled]="saving()" (click)="review(a.id, 'reject')">
                          {{ 'common.reject' | t:lang() }}
                        </button>
                      </app-enterprise-action-bar>
                    } @else {
                      <span class="muted">{{ a.reviewed_at | localeDate }}</span>
                    }
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </app-enterprise-data-table>
        <p class="muted">{{ 'common.pageTotal' | t:{ page: page, total: total }:lang() }}</p>
        <app-enterprise-action-bar>
          <button type="button" class="btn btn--ghost" [disabled]="page <= 1" (click)="go(page - 1)">
            {{ 'common.prev' | t:lang() }}
          </button>
          <button type="button" class="btn btn--ghost" [disabled]="page * limit >= total" (click)="go(page + 1)">
            {{ 'common.next' | t:lang() }}
          </button>
        </app-enterprise-action-bar>
      }
    </div>
  `,
})
export class CrmApprovalsPageComponent implements OnInit {
  private i18n = inject(I18nService);
  readonly lang = this.i18n.lang;

  private readonly api = inject(CrmApiService);
  private readonly notifications = inject(NotificationService);

  page = 1;
  limit = 25;
  total = 0;
  reviewNote = '';
  private pendingId: number | null = null;
  private pendingAction: 'approve' | 'reject' | null = null;

  readonly items = signal<ApprovalRequest[]>([]);
  readonly loading = signal(true);
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);
  readonly success = signal<string | null>(null);
  readonly pendingReview = signal(false);

  async ngOnInit(): Promise<void> {
    await this.load();
  }

  async go(p: number): Promise<void> {
    this.page = p;
    await this.load();
  }

  async load(): Promise<void> {
    this.loading.set(true);
    this.error.set(null);
    this.success.set(null);
    try {
      const res = await firstValueFrom(this.api.listApprovals(this.page, this.limit));
      this.items.set(res.items);
      this.total = res.total;
      this.page = res.page;
    } catch (e) {
      this.error.set(e instanceof CrmApiError ? e.message : 'Error al cargar aprobaciones');
    } finally {
      this.loading.set(false);
    }
  }

  review(id: number, action: 'approve' | 'reject'): void {
    if (this.saving()) return;
    this.pendingId = id;
    this.pendingAction = action;
    this.reviewNote = '';
    this.pendingReview.set(true);
  }

  cancelReview(): void {
    this.pendingReview.set(false);
    this.pendingId = null;
    this.pendingAction = null;
    this.reviewNote = '';
  }

  async confirmReview(): Promise<void> {
    const id = this.pendingId;
    const action = this.pendingAction;
    if (id == null || !action || this.saving()) return;
    const note = this.reviewNote.trim();
    this.saving.set(true);
    this.error.set(null);
    try {
      if (action === 'approve') {
        await firstValueFrom(this.api.approveRequest(id, note || undefined));
        this.success.set(`Solicitud #${id} aprobada.`);
        this.notifications.success(this.i18n.t('common.approve'));
      } else {
        await firstValueFrom(this.api.rejectRequest(id, note || undefined));
        this.success.set(`Solicitud #${id} rechazada.`);
        this.notifications.success(this.i18n.t('common.reject'));
      }
      this.cancelReview();
      await this.load();
    } catch (e) {
      const msg =
        e instanceof CrmApiError
          ? e.message
          : `Error al ${action === 'approve' ? 'aprobar' : 'rechazar'}`;
      this.error.set(msg);
      this.notifications.error(this.i18n.t('crm.approvals.title'), msg);
    } finally {
      this.saving.set(false);
    }
  }
}
