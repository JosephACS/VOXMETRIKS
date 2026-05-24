import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../../shared/services/icon-render.service';
import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FavoritesService } from '../services/favorites.service';
import { FavoriteTrack } from '../../../shared/models/api.models';
import { TrackRowComponent } from '../../../shared/components/track-row/track-row.component';
import { MusicPlayerService } from '../../../shared/services/music-player.service';
import { CoverArtService } from '../../../shared/services/cover-art.service';
import { PlayableTrack } from '../../../shared/models/player.models';

const COVER = 'linear-gradient(135deg, #1db954 0%, #065f46 50%, #064e3b 100%)';

@Component({
  selector: 'app-liked',
  standalone: true,
  imports: [CommonModule, RouterModule, TrackRowComponent],
  templateUrl: './liked.component.html',
  styleUrls: ['./liked.component.css'],
})
export class LikedComponent implements OnInit {
  private iconRender = inject(IconRenderService);
  private player = inject(MusicPlayerService);
  private covers = inject(CoverArtService);

  tracks = signal<FavoriteTrack[]>([]);
  isLoading = signal(true);

  heroCover = COVER;

  constructor(private favSvc: FavoritesService) {}

  ngOnInit() {
    this.favSvc.loadFavorites().subscribe({
      next: (d) => { this.tracks.set(d ?? []); this.isLoading.set(false); },
      error: () => this.isLoading.set(false),
    });
  }

  formatDuration(ms?: number): string {
    if (!ms) return '—';
    const m = Math.floor(ms / 60000);
    const s = Math.floor((ms % 60000) / 1000);
    return `${m}:${s.toString().padStart(2, '0')}`;
  }

  likedQueue(): PlayableTrack[] {
    return this.tracks().map((t) => ({
      id: t.id_track,
      title: t.nombre_track ?? '—',
      artist: t.nombre_artista ?? '—',
      durationMs: t.duration_ms,
      audioUrl: `/assets/audio/demo-${String((t.id_track % 8) + 1).padStart(2, '0')}.wav`,
      coverGradient: this.covers.gradientFor(t.id_track),
    }));
  }

  playAll() {
    const q = this.likedQueue();
    if (q.length) this.player.setQueue(q, 0);
  }

  icon(key: string, size = 18): SafeHtml {
    return this.iconRender.render(key, size);
  }
}
