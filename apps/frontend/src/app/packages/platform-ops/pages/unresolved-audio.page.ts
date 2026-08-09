import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { catchError, of } from 'rxjs';
import { PlatformOpsApiService } from '../services/platform-ops-api.service';
import {
  AudioCandidate,
  UnresolvedAudioItem,
} from '../models/platform-ops.models';
import { I18nService } from '../../../core/services/i18n.service';
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
                <th>ID</th>
                <th>{{ 'platformOps.audioUnresolved.colTrack' | t:lang() }}</th>
                <th>{{ 'platformOps.audioUnresolved.colArtist' | t:lang() }}</th>
                <th>{{ 'common.status' | t:lang() }}</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              @for (row of items; track row.track_id) {
                <tr [class.active]="selected?.track_id === row.track_id">
                  <td>{{ row.track_id }}</td>
                  <td>{{ row.track_name || '—' }}</td>
                  <td>{{ row.artist_name || '—' }}</td>
                  <td>
                    <app-enterprise-status-badge [status]="row.status" />
                  </td>
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

      @if (selected) {
        <app-enterprise-section-card
          [title]="
            (selected.track_name || ('#' + selected.track_id)) +
            ' — ' +
            (selected.artist_name || '')
          "
        >
          <div class="manual-row">
            <input
              class="input grow"
              [(ngModel)]="manualUrl"
              [placeholder]="'platformOps.audioUnresolved.pasteUrl' | t:lang()"
            />
            <button type="button" class="btn" [disabled]="busy" (click)="saveManual()">
              {{ 'platformOps.audioUnresolved.validateSave' | t:lang() }}
            </button>
            <button type="button" class="btn" [disabled]="busy" (click)="reresolve()">
              {{ 'platformOps.audioUnresolved.reresolve' | t:lang() }}
            </button>
            <button type="button" class="btn btn-danger" [disabled]="busy" (click)="markUnavailable()">
              {{ 'platformOps.audioUnresolved.markUnavailable' | t:lang() }}
            </button>
          </div>

          @if (actionMsg) {
            <p class="msg">{{ actionMsg }}</p>
          }

          <button type="button" class="btn btn-sm" [disabled]="busy" (click)="loadCandidates()">
            {{ 'platformOps.audioUnresolved.loadCandidates' | t:lang() }}
          </button>

          @if (candidates.length) {
            <ul class="candidates">
              @for (c of candidates; track c.video_id) {
                <li>
                  <div class="cand-meta">
                    <strong>{{ c.title }}</strong>
                    <span class="muted">
                      {{ c.channel_title || '' }} · {{ c.duration_sec || '?' }}s · score
                      {{ c.score ?? '—' }}
                    </span>
                  </div>
                  <div class="cand-actions">
                    <button type="button" class="btn btn-sm" (click)="preview(c)">
                      {{ 'platformOps.audioUnresolved.listen' | t:lang() }}
                    </button>
                    <button
                      type="button"
                      class="btn btn-sm"
                      [disabled]="busy || c.accepted === false"
                      (click)="pickCandidate(c)"
                    >
                      {{ 'platformOps.audioUnresolved.use' | t:lang() }}
                    </button>
                  </div>
                </li>
              }
            </ul>
          }

          @if (previewUrl) {
            <div class="preview">
              <iframe
                [src]="previewUrl"
                title="YouTube preview"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowfullscreen
              ></iframe>
            </div>
          }
        </app-enterprise-section-card>
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
      .input {
        min-width: 16rem;
        padding: 0.45rem 0.65rem;
      }
      .input.grow {
        flex: 1;
        min-width: 12rem;
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
      .candidates {
        list-style: none;
        padding: 0;
        margin: 0.75rem 0 0;
      }
      .candidates li {
        display: flex;
        justify-content: space-between;
        gap: 1rem;
        padding: 0.6rem 0;
        border-bottom: 1px solid rgba(0, 0, 0, 0.08);
      }
      .cand-meta {
        display: flex;
        flex-direction: column;
        gap: 0.15rem;
      }
      .cand-actions {
        display: flex;
        gap: 0.35rem;
        align-items: flex-start;
      }
      .preview iframe {
        width: 100%;
        max-width: 480px;
        aspect-ratio: 16 / 9;
        border: 0;
        margin-top: 0.75rem;
      }
    `,
  ],
})
export class UnresolvedAudioPage implements OnInit {
  private readonly api = inject(PlatformOpsApiService);
  private readonly i18n = inject(I18nService);
  private readonly sanitizer = inject(DomSanitizer);

  lang = () => this.i18n.lang();

  loading = false;
  busy = false;
  error = '';
  actionMsg = '';
  searchQ = '';
  items: UnresolvedAudioItem[] = [];
  total = 0;
  selected: UnresolvedAudioItem | null = null;
  candidates: AudioCandidate[] = [];
  manualUrl = '';
  previewUrl: SafeResourceUrl | null = null;

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
          this.error = err?.error?.detail || err?.message || 'Error';
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
    this.candidates = [];
    this.previewUrl = null;
    this.manualUrl = '';
    this.actionMsg = '';
  }

  loadCandidates(): void {
    if (!this.selected) return;
    this.busy = true;
    this.actionMsg = '';
    this.api
      .searchAudioCandidates(this.selected.track_id)
      .pipe(
        catchError((err) => {
          this.actionMsg = err?.error?.detail || err?.message || 'Error';
          return of(null);
        }),
      )
      .subscribe((res) => {
        this.busy = false;
        this.candidates = res?.candidates || [];
      });
  }

  preview(c: AudioCandidate): void {
    const url = `https://www.youtube.com/embed/${c.video_id}`;
    this.previewUrl = this.sanitizer.bypassSecurityTrustResourceUrl(url);
  }

  pickCandidate(c: AudioCandidate): void {
    this.manualUrl = c.video_id;
    this.saveManual();
  }

  saveManual(): void {
    if (!this.selected || !this.manualUrl.trim()) return;
    this.busy = true;
    this.actionMsg = '';
    this.api
      .saveManualAudio(this.selected.track_id, {
        url: this.manualUrl.trim(),
        validate: true,
      })
      .pipe(
        catchError((err) => {
          this.actionMsg = err?.error?.detail || err?.message || 'Error';
          this.busy = false;
          return of(null);
        }),
      )
      .subscribe((res) => {
        this.busy = false;
        if (!res) return;
        this.actionMsg = this.i18n.t('platformOps.audioUnresolved.saved');
        this.load();
      });
  }

  reresolve(): void {
    if (!this.selected) return;
    this.busy = true;
    this.api
      .reresolveAudio(this.selected.track_id)
      .pipe(
        catchError((err) => {
          this.actionMsg = err?.error?.detail || err?.message || 'Error';
          this.busy = false;
          return of(null);
        }),
      )
      .subscribe((res) => {
        this.busy = false;
        if (!res) return;
        this.actionMsg = `${res.provider}/${res.status}`;
        this.load();
      });
  }

  markUnavailable(): void {
    if (!this.selected) return;
    this.busy = true;
    this.api
      .markAudioUnavailable(this.selected.track_id)
      .pipe(
        catchError((err) => {
          this.actionMsg = err?.error?.detail || err?.message || 'Error';
          this.busy = false;
          return of(null);
        }),
      )
      .subscribe((res) => {
        this.busy = false;
        if (!res) return;
        this.actionMsg = this.i18n.t('platformOps.audioUnresolved.markedUnavailable');
        this.load();
      });
  }
}
