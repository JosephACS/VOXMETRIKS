import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../../shared/services/icon-render.service';
import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FavoritesService } from '../services/favorites.service';
import { FavoriteTrack } from '../../../shared/models/api.models';
import { FavoriteBtnComponent } from '../../../shared/components/favorite-btn/favorite-btn.component';

const COVER = 'linear-gradient(135deg, #1db954 0%, #065f46 50%, #064e3b 100%)';

@Component({
  selector: 'app-liked',
  standalone: true,
  imports: [CommonModule, RouterModule, FavoriteBtnComponent],
  templateUrl: './liked.component.html',
  styleUrls: ['./liked.component.css'],
})
export class LikedComponent implements OnInit {
  private iconRender = inject(IconRenderService);

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

  icon(key: string, size = 18): SafeHtml {
    return this.iconRender.render(key, size);
  }
}
