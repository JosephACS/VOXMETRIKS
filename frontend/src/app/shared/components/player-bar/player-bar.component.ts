import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MusicPlayerService } from '../../services/music-player.service';

@Component({
  selector: 'app-player-bar',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './player-bar.component.html',
  styleUrls: ['./player-bar.component.css'],
})
export class PlayerBarComponent {
  player = inject(MusicPlayerService);

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
}
