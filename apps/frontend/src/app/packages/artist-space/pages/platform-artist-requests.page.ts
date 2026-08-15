import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ArtistSpaceApiService } from '../services/artist-space-api.service';
import { ArtistAccessRequest } from '../models/artist-space.models';
import { I18nService } from '../../../core/services/i18n.service';
import { NotificationService } from '../../../core/services/notification.service';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { userFacingHttpError } from '../../../core/i18n/user-facing-error';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-platform-artist-requests',
  standalone: true,
  imports: [CommonModule, FormsModule, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise" data-testid="platform-artist-requests">
      <app-enterprise-page-header
        [title]="'artistSpace.platform.title' | t: lang()"
        [subtitle]="'artistSpace.platform.subtitle' | t: lang()"
      />
      @if (loading()) {
        <app-enterprise-loading-skeleton [rows]="3" />
      } @else if (error()) {
        <app-enterprise-error-state [message]="error()!" (retry)="load()" />
      } @else if (items().length === 0) {
        <app-enterprise-empty-state
          [title]="'artistSpace.platform.emptyTitle' | t: lang()"
          [description]="'artistSpace.platform.emptyBody' | t: lang()"
        />
      } @else {
        @for (r of items(); track r.id) {
          <app-enterprise-section-card [title]="primaryTitle(r)">
            <p class="meta">
              {{ typeLabel(r.request_type) }}
              <span class="ref"> · {{ 'artistSpace.platform.refId' | t: lang() }} {{ r.id }}</span>
            </p>
            @if (r.evidence_note) {
              <p>{{ r.evidence_note }}</p>
            }
            @if (r.evidence_url) {
              <p class="ref">{{ r.evidence_url }}</p>
            }

            @if (confirmRejectId() === r.id) {
              <div class="confirm" role="group" [attr.aria-label]="'artistSpace.platform.rejectConfirm' | t: lang()">
                <label class="field-label" [attr.for]="'reject-reason-' + r.id">
                  {{ 'artistSpace.platform.rejectReason' | t: lang() }}
                </label>
                <textarea
                  class="input textarea"
                  [id]="'reject-reason-' + r.id"
                  [(ngModel)]="rejectReason"
                  rows="3"
                  [attr.data-testid]="'artist-request-reject-reason-' + r.id"
                ></textarea>
                @if (reasonError()) {
                  <p class="err" role="alert">{{ reasonError() }}</p>
                }
                <div class="actions">
                  <button
                    type="button"
                    class="btn btn--danger"
                    [disabled]="busyId() === r.id"
                    (click)="confirmReject(r)"
                    [attr.data-testid]="'artist-request-reject-confirm-' + r.id"
                  >
                    {{ 'artistSpace.platform.confirmReject' | t: lang() }}
                  </button>
                  <button
                    type="button"
                    class="btn btn--secondary"
                    [disabled]="busyId() === r.id"
                    (click)="cancelReject()"
                  >
                    {{ 'common.cancel' | t: lang() }}
                  </button>
                </div>
              </div>
            } @else {
              <div class="actions">
                <button
                  type="button"
                  class="btn btn--primary"
                  [disabled]="busyId() !== null"
                  (click)="approve(r)"
                  [attr.data-testid]="'artist-request-approve-' + r.id"
                >
                  {{ 'common.approve' | t: lang() }}
                </button>
                <button
                  type="button"
                  class="btn btn--secondary"
                  [disabled]="busyId() !== null"
                  (click)="beginReject(r)"
                  [attr.data-testid]="'artist-request-reject-' + r.id"
                >
                  {{ 'common.reject' | t: lang() }}
                </button>
              </div>
            }
          </app-enterprise-section-card>
        }
      }
    </div>
  `,
  styles: `
    .actions {
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
      margin-top: 0.75rem;
    }
    .meta {
      margin: 0 0 0.5rem;
    }
    .ref {
      opacity: 0.65;
      font-size: 0.85rem;
    }
    .field-label {
      display: block;
      margin-bottom: 0.35rem;
      font-size: 0.85rem;
    }
    .textarea {
      width: 100%;
      resize: vertical;
    }
    .err {
      color: #f87171;
      margin: 0.35rem 0 0;
    }
    .btn--danger {
      background: rgba(248, 113, 113, 0.15);
      border: 1px solid rgba(248, 113, 113, 0.4);
      color: #fecaca;
    }
    .confirm {
      margin-top: 0.75rem;
      padding: 0.75rem;
      border-radius: 8px;
      border: 1px solid rgba(248, 113, 113, 0.35);
      background: rgba(248, 113, 113, 0.08);
    }
  `,
})
export class PlatformArtistRequestsPage implements OnInit {
  private readonly api = inject(ArtistSpaceApiService);
  private readonly i18n = inject(I18nService);
  private readonly notify = inject(NotificationService);

  readonly lang = this.i18n.lang;
  readonly loading = signal(true);
  readonly error = signal<string | null>(null);
  readonly items = signal<ArtistAccessRequest[]>([]);
  readonly busyId = signal<number | null>(null);
  readonly confirmRejectId = signal<number | null>(null);
  readonly reasonError = signal<string | null>(null);
  rejectReason = '';

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.error.set(null);
    this.api.listPlatformRequests('pending').subscribe({
      next: (rows) => {
        this.items.set(rows || []);
        this.loading.set(false);
      },
      error: (e) => {
        this.error.set(userFacingHttpError(this.i18n, e));
        this.loading.set(false);
      },
    });
  }

  primaryTitle(r: ArtistAccessRequest): string {
    return (
      r.proposed_display_name?.trim() ||
      (r.warehouse_artist_id != null
        ? this.i18n.t('artistSpace.platform.warehouseTitle', {
            id: String(r.warehouse_artist_id),
          })
        : this.i18n.t('artistSpace.platform.untitled'))
    );
  }

  typeLabel(type: string): string {
    const key = `artistSpace.platform.type.${type}`;
    const translated = this.i18n.t(key);
    return translated === key ? type : translated;
  }

  approve(r: ArtistAccessRequest): void {
    if (this.busyId() !== null) return;
    this.busyId.set(r.id);
    this.api.approvePlatformRequest(r.id).subscribe({
      next: () => {
        this.notify.success(this.i18n.t('artistSpace.platform.approved'));
        this.busyId.set(null);
        this.load();
      },
      error: (e) => {
        this.notify.show(
          this.i18n.t('common.error'),
          userFacingHttpError(this.i18n, e),
          'error',
        );
        this.busyId.set(null);
      },
    });
  }

  beginReject(r: ArtistAccessRequest): void {
    this.confirmRejectId.set(r.id);
    this.rejectReason = '';
    this.reasonError.set(null);
  }

  cancelReject(): void {
    this.confirmRejectId.set(null);
    this.rejectReason = '';
    this.reasonError.set(null);
  }

  confirmReject(r: ArtistAccessRequest): void {
    const reason = this.rejectReason.trim();
    if (!reason) {
      this.reasonError.set(this.i18n.t('artistSpace.platform.rejectReasonRequired'));
      return;
    }
    if (this.busyId() !== null) return;
    this.busyId.set(r.id);
    this.reasonError.set(null);
    this.api.rejectPlatformRequest(r.id, reason).subscribe({
      next: () => {
        this.notify.success(this.i18n.t('artistSpace.platform.rejected'));
        this.busyId.set(null);
        this.cancelReject();
        this.load();
      },
      error: (e) => {
        this.notify.show(
          this.i18n.t('common.error'),
          userFacingHttpError(this.i18n, e),
          'error',
        );
        this.busyId.set(null);
      },
    });
  }
}
