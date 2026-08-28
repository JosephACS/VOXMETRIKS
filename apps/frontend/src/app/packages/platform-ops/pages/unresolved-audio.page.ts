import { Component, ElementRef, OnInit, ViewChild, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { catchError, of } from 'rxjs';
import { PlatformOpsApiService } from '../services/platform-ops-api.service';
import { UnresolvedAudioItem } from '../models/platform-ops.models';
import { I18nService } from '../../../core/services/i18n.service';
import { NotificationService } from '../../../core/services/notification.service';
import { userFacingHttpError } from '../../../core/i18n/user-facing-error';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { ENTERPRISE_UI_IMPORTS } from '../../../shared/components/enterprise';

@Component({
  selector: 'app-unresolved-audio-page',
  standalone: true,
  imports: [CommonModule, FormsModule, TranslatePipe, ...ENTERPRISE_UI_IMPORTS],
  template: `
    <div class="vx-enterprise platform-ops-page unresolved-audio-page">
      <app-enterprise-page-header
        [title]="'platformOps.audioUnresolved.title' | t:lang()"
        [subtitle]="'platformOps.audioUnresolved.subtitle' | t:lang()"
      />

      <div class="filters">
        <input
          class="input"
          type="search"
          [(ngModel)]="searchQ"
          (keyup.enter)="load()"
          [placeholder]="'platformOps.audioUnresolved.searchPlaceholder' | t:lang()"
        />
        <button type="button" class="btn" (click)="load()">
          {{ 'common.search' | t:lang() }}
        </button>
      </div>

      @if (error) {
        <app-enterprise-error-state [message]="error" (retry)="load()" />
      }

      @if (selected) {
        <div #managePanel id="audio-manage-panel" class="manage-panel" tabindex="-1">
          <app-enterprise-section-card
            [title]="
              (selected.track_name || ('#' + selected.track_id)) +
              ' — ' +
              (selected.artist_name || '')
            "
          >
            <p class="manage-hint">
              {{ 'platformOps.audioUnresolved.manageHint' | t:lang() }}
            </p>
            <div class="manual-row">
              <button type="button" class="btn" [disabled]="busy" (click)="reresolve()">
                {{ 'platformOps.audioUnresolved.reresolve' | t:lang() }}
              </button>
              <button
                type="button"
                class="btn btn-danger"
                [disabled]="busy"
                (click)="beginUnavailable()"
                data-testid="audio-mark-unavailable"
              >
                {{ 'platformOps.audioUnresolved.markUnavailable' | t:lang() }}
              </button>
              <button type="button" class="btn btn-sm" (click)="clearSelection()">
                {{ 'common.close' | t:lang() }}
              </button>
            </div>

            @if (confirmUnavailable) {
              <div class="confirm" role="group" [attr.aria-label]="'platformOps.audioUnresolved.unavailableConfirm' | t:lang()">
                <label class="field-label" for="unavailable-reason">
                  {{ 'platformOps.audioUnresolved.reason' | t:lang() }}
                </label>
                <textarea
                  id="unavailable-reason"
                  class="input textarea"
                  [(ngModel)]="unavailableReason"
                  rows="2"
                  data-testid="audio-unavailable-reason"
                ></textarea>
                @if (reasonError) {
                  <p class="err" role="alert">{{ reasonError }}</p>
                }
                <div class="manual-row">
                  <button
                    type="button"
                    class="btn btn-danger"
                    [disabled]="busy"
                    (click)="markUnavailable()"
                    data-testid="audio-unavailable-confirm"
                  >
                    {{ 'platformOps.audioUnresolved.confirmUnavailable' | t:lang() }}
                  </button>
                  <button type="button" class="btn" [disabled]="busy" (click)="cancelUnavailable()">
                    {{ 'common.cancel' | t:lang() }}
                  </button>
                </div>
              </div>
            }

            @if (actionMsg) {
              <p class="msg">{{ actionMsg }}</p>
            }

          </app-enterprise-section-card>
        </div>
      }

      @if (loading) {
        <app-enterprise-loading-skeleton [rows]="6" />
      } @else if (!items.length) {
        <app-enterprise-empty-state
          [title]="'platformOps.audioUnresolved.empty' | t:lang()"
          [description]="'platformOps.audioUnresolved.emptyBody' | t:lang()"
        />
      } @else {
        <app-enterprise-data-table>
          <table class="data-table">
            <thead>
              <tr>
                <th>{{ 'platformOps.audioUnresolved.colTrack' | t:lang() }}</th>
                <th>{{ 'platformOps.audioUnresolved.colArtist' | t:lang() }}</th>
                <th>{{ 'common.status' | t:lang() }}</th>
                <th class="ref-col">{{ 'platformOps.audioUnresolved.colRef' | t:lang() }}</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              @for (row of items; track row.track_id) {
                <tr [class.active]="selected?.track_id === row.track_id">
                  <td>{{ row.track_name || ('platformOps.audioUnresolved.untitled' | t:lang()) }}</td>
                  <td>{{ row.artist_name || ('common.notAvailable' | t:lang()) }}</td>
                  <td>
                    <app-enterprise-status-badge [status]="row.status" />
                  </td>
                  <td class="ref-col">{{ row.track_id }}</td>
                  <td>
                    <button type="button" class="btn btn-sm" (click)="select(row)">
                      {{ 'platformOps.audioUnresolved.manage' | t:lang() }}
                    </button>
                  </td>
                </tr>
              }
            </tbody>
          </table>
        </app-enterprise-data-table>
        <p class="muted">{{ total }} {{ 'platformOps.audioUnresolved.total' | t:lang() }}</p>
      }
    </div>
  `,
  styles: [
    `
      .filters {
        display: flex;
        gap: 0.75rem;
        margin-bottom: 1rem;
        flex-wrap: wrap;
      }
      .manage-panel {
        margin-bottom: 1.25rem;
        scroll-margin-top: 5rem;
      }
      .manage-hint {
        margin: 0 0 0.75rem;
        opacity: 0.8;
        font-size: 0.9rem;
      }
      .input {
        min-width: 16rem;
        padding: 0.45rem 0.65rem;
      }
      .manual-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-bottom: 0.75rem;
      }
      .btn {
        padding: 0.4rem 0.75rem;
        cursor: pointer;
      }
      .btn-sm {
        padding: 0.25rem 0.5rem;
        font-size: 0.85rem;
      }
      .btn-danger {
        color: #b91c1c;
      }
      .muted {
        opacity: 0.7;
        font-size: 0.9rem;
      }
      .msg {
        margin: 0.5rem 0;
      }
      tr.active {
        background: rgba(0, 0, 0, 0.04);
      }
      .ref-col {
        opacity: 0.65;
        font-size: 0.85rem;
      }
      .confirm {
        margin-top: 0.75rem;
        padding: 0.75rem;
        border-radius: 8px;
        border: 1px solid rgba(248, 113, 113, 0.35);
        background: rgba(248, 113, 113, 0.08);
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
        color: #b91c1c;
        margin: 0.35rem 0 0;
      }
    `,
  ],
})
export class UnresolvedAudioPage implements OnInit {
  private readonly api = inject(PlatformOpsApiService);
  private readonly i18n = inject(I18nService);
  private readonly notify = inject(NotificationService);

  @ViewChild('managePanel') managePanel?: ElementRef<HTMLElement>;

  lang = () => this.i18n.lang();

  loading = false;
  busy = false;
  error = '';
  actionMsg = '';
  searchQ = '';
  items: UnresolvedAudioItem[] = [];
  total = 0;
  selected: UnresolvedAudioItem | null = null;
  confirmUnavailable = false;
  unavailableReason = '';
  reasonError = '';

  ngOnInit(): void {
    this.load();
  }

  load(): void {
    this.loading = true;
    this.error = '';
    this.api
      .listUnresolvedAudio({ q: this.searchQ || undefined, limit: 50 })
      .pipe(
        catchError((err) => {
          this.error = userFacingHttpError(this.i18n, err);
          return of({ items: [], total: 0, limit: 50, offset: 0 });
        }),
      )
      .subscribe((res) => {
        this.items = res.items || [];
        this.total = res.total || 0;
        this.loading = false;
      });
  }

  select(row: UnresolvedAudioItem): void {
    this.selected = row;
    this.actionMsg = '';
    this.cancelUnavailable();
    setTimeout(() => {
      this.managePanel?.nativeElement?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      this.managePanel?.nativeElement?.focus({ preventScroll: true });
    }, 0);
  }

  clearSelection(): void {
    this.selected = null;
    this.actionMsg = '';
    this.cancelUnavailable();
  }

  reresolve(): void {
    if (!this.selected) return;
    this.busy = true;
    this.api
      .reresolveAudio(this.selected.track_id)
      .pipe(
        catchError((err) => {
          this.actionMsg = userFacingHttpError(this.i18n, err);
          this.busy = false;
          return of(null);
        }),
      )
      .subscribe((res) => {
        this.busy = false;
        if (!res) return;
        this.actionMsg = this.i18n.t('platformOps.audioUnresolved.reresolved');
        this.notify.success(this.actionMsg);
        this.load();
      });
  }

  beginUnavailable(): void {
    this.confirmUnavailable = true;
    this.unavailableReason = '';
    this.reasonError = '';
  }

  cancelUnavailable(): void {
    this.confirmUnavailable = false;
    this.unavailableReason = '';
    this.reasonError = '';
  }

  markUnavailable(): void {
    if (!this.selected) return;
    const reason = this.unavailableReason.trim();
    if (!reason) {
      this.reasonError = this.i18n.t('platformOps.audioUnresolved.reasonRequired');
      return;
    }
    if (this.busy) return;
    this.busy = true;
    this.api
      .markAudioUnavailable(this.selected.track_id, reason)
      .pipe(
        catchError((err) => {
          this.actionMsg = userFacingHttpError(this.i18n, err);
          this.notify.show(this.i18n.t('common.error'), this.actionMsg, 'error');
          this.busy = false;
          return of(null);
        }),
      )
      .subscribe((res) => {
        this.busy = false;
        if (!res) return;
        this.actionMsg = this.i18n.t('platformOps.audioUnresolved.markedUnavailable');
        this.notify.success(this.actionMsg);
        this.cancelUnavailable();
        this.load();
      });
  }
}
