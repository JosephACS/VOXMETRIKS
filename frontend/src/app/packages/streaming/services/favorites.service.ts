import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject, tap } from 'rxjs';
import { environment } from '../../../../environments/environment';
import { FavoriteTrack } from '../../../shared/models/api.models';

@Injectable({ providedIn: 'root' })
export class FavoritesService {
  private readonly http = inject(HttpClient);
  private readonly API = `${environment.apiUrl}/favorites`;
  private idsSubject = new BehaviorSubject<Set<number>>(new Set());
  favoriteIds$ = this.idsSubject.asObservable();

  loadFavorites(): Observable<FavoriteTrack[]> {
    return this.http.get<FavoriteTrack[]>(this.API).pipe(
      tap((items) => this.idsSubject.next(new Set(items.map((i) => i.id_track))))
    );
  }

  add(trackId: number): Observable<{ favorited: boolean; track_id: number }> {
    return this.http.post<{ favorited: boolean; track_id: number }>(`${this.API}/${trackId}`, {}).pipe(
      tap(() => {
        const s = new Set(this.idsSubject.value);
        s.add(trackId);
        this.idsSubject.next(s);
      })
    );
  }

  remove(trackId: number): Observable<{ removed: boolean; track_id: number }> {
    return this.http.delete<{ removed: boolean; track_id: number }>(`${this.API}/${trackId}`).pipe(
      tap(() => {
        const s = new Set(this.idsSubject.value);
        s.delete(trackId);
        this.idsSubject.next(s);
      })
    );
  }

  isFavorite(trackId: number): boolean {
    return this.idsSubject.value.has(trackId);
  }

  toggle(trackId: number): Observable<unknown> {
    return this.isFavorite(trackId) ? this.remove(trackId) : this.add(trackId);
  }

  refreshIds(): void {
    this.loadFavorites().subscribe({ error: () => {} });
  }
}
