import { Injectable, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { Observable } from 'rxjs';
import { FavoritesService } from '../packages/streaming/services/favorites.service';
import { FavoriteTrack } from '../shared/models/api.models';

/** Global favorites state — reactive across all track surfaces. */
@Injectable({ providedIn: 'root' })
export class FavoritesStore {
  private readonly favs = inject(FavoritesService);

  readonly favoriteIds = toSignal(this.favs.favoriteIds$, { initialValue: new Set<number>() });

  isFavorite(trackId: number): boolean {
    return this.favoriteIds().has(trackId);
  }

  toggle(trackId: number): Observable<unknown> {
    return this.favs.toggle(trackId);
  }

  add(trackId: number): Observable<{ favorited: boolean; track_id: number }> {
    return this.favs.add(trackId);
  }

  remove(trackId: number): Observable<{ removed: boolean; track_id: number }> {
    return this.favs.remove(trackId);
  }

  loadFavorites(): Observable<FavoriteTrack[]> {
    return this.favs.loadFavorites();
  }

  refreshIds(): void {
    this.favs.refreshIds();
  }
}
