import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../../shared/services/icon-render.service';
import { I18nService } from '../../../core/services/i18n.service';
import { Component, inject, OnInit, signal, computed, DestroyRef } from '@angular/core';
import { takeUntilDestroyed, toObservable } from '@angular/core/rxjs-interop';
import { skip } from 'rxjs';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { FavoritesStore } from '../../../playback-core/favorites.store';
import { FavoriteTrack } from '../../../shared/models/api.models';
import { TrackRowComponent } from '../../../shared/components/track-row/track-row.component';
import { PlayerController } from '../../../playback-core/player.controller';
import { toPlayableFromFavorite } from '../../../playback-core/adapters/track.adapter';
import { CoverArtService } from '../../../shared/services/cover-art.service';
import { PlayableTrack } from '../../../shared/models/player.models';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { DataSourceBadgeComponent } from '../../../shared/components/data-source-badge/data-source-badge.component';

const COVER = 'linear-gradient(135deg, #1db954 0%, #065f46 50%, #064e3b 100%)';

@Component({
  selector: 'app-liked',
  standalone: true,
  imports: [CommonModule, RouterModule, TrackRowComponent, TranslatePipe, DataSourceBadgeComponent],
  templateUrl: './liked.component.html',
  styleUrls: ['./liked.component.css'],
})
export class LikedComponent implements OnInit {
  readonly lang = inject(I18nService).lang;
  private iconRender = inject(IconRenderService);
  private readonly controller = inject(PlayerController);
  private covers = inject(CoverArtService);

  private favStore = inject(FavoritesStore);
  private destroyRef = inject(DestroyRef);

  tracks = signal<FavoriteTrack[]>([]);
  isLoading = signal(true);
  hasError = signal(false);

  heroCover = COVER;

  ngOnInit() {
    this.loadFavorites();
    toObservable(this.favStore.favoriteIds)
      .pipe(skip(1), takeUntilDestroyed(this.destroyRef))
      .subscribe(() => this.loadFavorites());
  }

  loadFavorites() {
    this.isLoading.set(true);
    this.hasError.set(false);
    this.favStore.loadFavorites().subscribe({
      next: (d) => { this.tracks.set(d ?? []); this.isLoading.set(false); },
      error: () => { this.hasError.set(true); this.isLoading.set(false); },
    });
  }

  formatDuration(ms?: number): string {
    if (!ms) return '—';
    const m = Math.floor(ms / 60000);
    const s = Math.floor((ms % 60000) / 1000);
    return `${m}:${s.toString().padStart(2, '0')}`;
  }

  likedQueue = computed((): PlayableTrack[] =>
    this.tracks().map((t) => toPlayableFromFavorite(this.covers, t)),
  );

  playAll() {
    const q = this.likedQueue();
    if (q.length) this.controller.setQueue(q, 0);
  }

  icon(key: string, size = 18): SafeHtml {
    return this.iconRender.render(key, size);
  }
}
