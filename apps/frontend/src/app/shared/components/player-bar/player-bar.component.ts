import { I18nService } from '../../../core/services/i18n.service';
import { Component, computed, effect, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { toSignal } from '@angular/core/rxjs-interop';
import { NavigationEnd, Router } from '@angular/router';
import { filter, map, startWith } from 'rxjs/operators';
import { PlayerController } from '../../../playback-core/player.controller';
import { PlaybackStore } from '../../../playback-core/playback.store';
import { TranslatePipe } from '../../pipes/translate.pipe';
import { FavoriteBtnComponent } from '../favorite-btn/favorite-btn.component';
import { AddToPlaylistBtnComponent } from '../add-to-playlist-btn/add-to-playlist-btn.component';

import { RepeatMode } from '../../models/player.models';

function isStaffReportsPath(url: string): boolean {
  const path = (url || '').split('?')[0];
  return (
    path === '/reports' ||
    path.startsWith('/reports/') ||
    path === '/simple-reports' ||
    path.startsWith('/simple-reports') ||
    path === '/complex-reports' ||
    path.startsWith('/complex-reports')
  );
}

@Component({
  selector: 'app-player-bar',
  standalone: true,
  imports: [CommonModule, TranslatePipe, FavoriteBtnComponent, AddToPlaylistBtnComponent],
  templateUrl: './player-bar.component.html',
  styleUrls: ['./player-bar.component.css'],
})
export class PlayerBarComponent {
  readonly lang = inject(I18nService).lang;
  readonly controller = inject(PlayerController);
  readonly playback = inject(PlaybackStore);
  private readonly router = inject(Router);

  private readonly url = toSignal(
    this.router.events.pipe(
      filter((e): e is NavigationEnd => e instanceof NavigationEnd),
      map((e) => e.urlAfterRedirects || e.url),
      startWith(this.router.url),
    ),
    { initialValue: this.router.url },
  );

  /** Compact staff mini-player on report routes (listener keeps full bar elsewhere). */
  readonly staffReportsSurface = computed(() => isStaffReportsPath(this.url() || ''));
  readonly staffIdle = computed(() => this.staffReportsSurface() && !this.playback.currentTrack());
  readonly staffCompact = computed(() => this.staffReportsSurface() && !!this.playback.currentTrack());

  constructor() {
    effect(() => {
      if (typeof document === 'undefined') return;
      const root = document.documentElement;
      if (this.staffIdle()) {
        // Dock pill only — do not reserve a full-width strip that covers charts.
        root.style.setProperty('--player-height', '0px');
      } else if (this.staffCompact()) {
        root.style.setProperty('--player-height', '52px');
      } else if (this.staffReportsSurface()) {
        root.style.setProperty('--player-height', '52px');
      } else {
        root.style.removeProperty('--player-height');
      }
    });
  }

  onProgressClick(e: MouseEvent) {
    if (this.staffIdle()) return;
    const el = e.currentTarget as HTMLElement;
    const rect = el.getBoundingClientRect();
    const pct = ((e.clientX - rect.left) / rect.width) * 100;
    this.controller.seekPct(pct);
  }

  onVolumeInput(e: Event) {
    const v = parseFloat((e.target as HTMLInputElement).value);
    this.controller.setVolume(v);
  }

  toggleExpand(e?: Event) {
    e?.stopPropagation();
    if (!this.playback.currentTrack()) return;
    this.controller.toggleExpandedView();
  }

  repeatTitle(mode: RepeatMode): string {
    if (mode === 'one') return 'player.repeatOne';
    if (mode === 'all') return 'player.repeatAll';
    return 'player.repeatOff';
  }
}
