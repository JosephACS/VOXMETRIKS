import { I18nService } from '../../../core/services/i18n.service';
import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PlayerController } from '../../../playback-core/player.controller';
import { PlaybackStore } from '../../../playback-core/playback.store';
import { TranslatePipe } from '../../pipes/translate.pipe';
import { FavoriteBtnComponent } from '../favorite-btn/favorite-btn.component';
import { AddToPlaylistBtnComponent } from '../add-to-playlist-btn/add-to-playlist-btn.component';

import { RepeatMode } from '../../models/player.models';

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

  onProgressClick(e: MouseEvent) {
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
