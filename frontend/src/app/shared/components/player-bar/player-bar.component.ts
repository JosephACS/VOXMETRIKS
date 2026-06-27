import { Component, computed, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MusicPlayerService } from '../../services/music-player.service';
import { TranslatePipe } from '../../pipes/translate.pipe';
import { FavoriteBtnComponent } from '../favorite-btn/favorite-btn.component';
import { AddToPlaylistBtnComponent } from '../add-to-playlist-btn/add-to-playlist-btn.component';

@Component({
  selector: 'app-player-bar',
  standalone: true,
  imports: [CommonModule, TranslatePipe, FavoriteBtnComponent, AddToPlaylistBtnComponent],
  templateUrl: './player-bar.component.html',
  styleUrls: ['./player-bar.component.css'],
})
export class PlayerBarComponent {
  player = inject(MusicPlayerService);

  sourceLabel = computed(() => {
    switch (this.player.audioMode()) {
      case 'youtube': return 'player.sourceYoutube';
      case 'loading': return 'player.sourceLoading';
      default: return 'player.sourceDemo';
    }
  });

  onProgressClick(e: MouseEvent) {
    const el = e.currentTarget as HTMLElement;
    const rect = el.getBoundingClientRect();
    const pct = ((e.clientX - rect.left) / rect.width) * 100;
    this.player.seekPct(pct);
  }

  onVolumeInput(e: Event) {
    const v = parseFloat((e.target as HTMLInputElement).value);
    this.player.setVolume(v);
  }

  toggleExpand(e?: Event) {
    e?.stopPropagation();
    if (!this.player.currentTrack()) return;
    this.player.toggleExpandedView();
  }
}
