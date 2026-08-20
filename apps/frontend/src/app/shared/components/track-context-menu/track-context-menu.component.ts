import { Component, HostListener, Input, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { PlayerController } from '../../../playback-core/player.controller';
import { PlayableTrack } from '../../models/player.models';
import { AddToPlaylistBtnComponent } from '../add-to-playlist-btn/add-to-playlist-btn.component';
import { TranslatePipe } from '../../pipes/translate.pipe';
import { I18nService } from '../../../core/services/i18n.service';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
  selector: 'app-track-context-menu',
  standalone: true,
  imports: [
    CommonModule,
    RouterModule,
    AddToPlaylistBtnComponent,
    TranslatePipe,
  ],
  template: `
    <div class="tcm-wrap" (click)="$event.stopPropagation()">
      <button
        type="button"
        class="tcm-trigger"
        [class.sm]="size === 'sm'"
        (click)="toggle($event)"
        [title]="'track.moreActions' | t"
        [attr.aria-label]="'track.moreActions' | t"
        [attr.aria-expanded]="open()"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
          <circle cx="5" cy="12" r="2"/><circle cx="12" cy="12" r="2"/><circle cx="19" cy="12" r="2"/>
        </svg>
      </button>
      @if (open()) {
        <div class="tcm-menu" [class.drop-up]="dropUp" role="menu">
          <button type="button" class="tcm-item" role="menuitem" (click)="onPlayNow($event)">
            {{ 'track.playNow' | t:lang() }}
          </button>
          <button type="button" class="tcm-item" role="menuitem" (click)="onPlayNext($event)">
            {{ 'track.playNext' | t:lang() }}
          </button>
          <button type="button" class="tcm-item" role="menuitem" (click)="onAddToQueue($event)">
            {{ 'track.addToQueue' | t:lang() }}
          </button>
          <div class="tcm-divider" role="separator"></div>
          <div class="tcm-row-actions">
            <app-add-to-playlist-btn [trackId]="track.id" size="sm" [dropUp]="true" variant="icon" />
          </div>
          <div class="tcm-divider" role="separator"></div>
          @if (artistRoute; as ar) {
            <a class="tcm-item tcm-link" role="menuitem" [routerLink]="ar" (click)="close()">
              {{ 'track.viewArtist' | t:lang() }}
            </a>
          }
          <a class="tcm-item tcm-link" role="menuitem" [routerLink]="['/tracks', track.id]" (click)="close()">
            {{ 'track.viewDetail' | t:lang() }}
          </a>
        </div>
      }
    </div>
  `,
  styles: [`
    .tcm-wrap { position: relative; display: inline-flex; }
    .tcm-trigger {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 32px;
      height: 32px;
      border: none;
      border-radius: 50%;
      background: transparent;
      color: var(--text-muted, rgba(255,255,255,0.55));
      cursor: pointer;
    }
    .tcm-trigger.sm { width: 28px; height: 28px; }
    .tcm-trigger:hover { color: var(--text); background: var(--shell-hover, rgba(255,255,255,0.06)); }
    .tcm-menu {
      position: absolute;
      top: calc(100% + 4px);
      right: 0;
      min-width: 200px;
      padding: 0.35rem 0;
      border-radius: 8px;
      background: var(--shell-dropdown, var(--shell-panel, #282828));
      border: 1px solid var(--shell-border-strong, rgba(255,255,255,0.1));
      box-shadow: var(--shadow-md, 0 8px 24px rgba(0,0,0,0.45));
      color: var(--shell-fg, var(--text));
      z-index: 120;
    }
    .tcm-menu.drop-up {
      top: auto;
      bottom: calc(100% + 4px);
    }
    .tcm-item {
      display: block;
      width: 100%;
      padding: 0.55rem 1rem;
      border: none;
      background: transparent;
      color: var(--shell-fg, var(--text));
      font-size: 0.8125rem;
      text-align: left;
      cursor: pointer;
      text-decoration: none;
    }
    .tcm-item:hover { background: var(--shell-hover, rgba(255,255,255,0.08)); }
    .tcm-divider {
      height: 1px;
      margin: 0.25rem 0;
      background: var(--shell-border-strong, rgba(255,255,255,0.08));
    }
    .tcm-row-actions {
      display: flex;
      align-items: center;
      gap: 0.35rem;
      padding: 0.35rem 0.75rem;
    }
  `],
})
export class TrackContextMenuComponent {
  readonly lang = inject(I18nService).lang;
  private readonly controller = inject(PlayerController);
  private readonly i18n = inject(I18nService);
  private readonly notify = inject(NotificationService);

  @Input({ required: true }) track!: PlayableTrack;
  @Input() contextQueue: PlayableTrack[] = [];
  @Input() artistId?: number;
  @Input() size: 'sm' | 'md' = 'md';
  @Input() dropUp = false;

  open = signal(false);

  get artistRoute(): string[] | null {
    const id = this.artistId ?? this.track.artistId;
    return id != null && id > 0 ? ['/artists', String(id)] : null;
  }

  toggle(e: Event) {
    e.preventDefault();
    e.stopPropagation();
    this.open.update((v) => !v);
  }

  close() {
    this.open.set(false);
  }

  @HostListener('document:click')
  onDocumentClick() {
    if (this.open()) this.close();
  }

  onPlayNow(e: Event) {
    e.stopPropagation();
    const q = this.contextQueue.length ? this.contextQueue : undefined;
    this.controller.playNow(this.track, q);
    this.notify.success(this.i18n.t('track.playNow'), this.track.title);
    this.close();
  }

  onPlayNext(e: Event) {
    e.stopPropagation();
    this.controller.playNextInQueue(this.track);
    this.notify.info(this.i18n.t('track.playNext'), this.track.title);
    this.close();
  }

  onAddToQueue(e: Event) {
    e.stopPropagation();
    const added = this.controller.addToQueue(this.track);
    if (added) {
      this.notify.success(this.i18n.t('track.addToQueue'), this.track.title);
    } else {
      this.notify.info(this.i18n.t('track.alreadyInQueue'), this.track.title);
    }
    this.close();
  }
}
