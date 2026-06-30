import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../../shared/services/icon-render.service';
import { Component, DestroyRef, inject, OnInit, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { CoverArtService } from '../../../shared/services/cover-art.service';
import { TracksService } from '../services/tracks.service';
import { ArtistsService } from '../services/artists.service';
import { TrackSearchResult, Artista } from '../../../shared/models/api.models';
import { primaryArtistName } from '../../../shared/utils/artist.util';
import { FavoriteBtnComponent } from '../../../shared/components/favorite-btn/favorite-btn.component';
import { DataSourceBadgeComponent } from '../../../shared/components/data-source-badge/data-source-badge.component';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { displayTrackTitle } from '../../../shared/utils/track-display.util';
import { SearchHistoryService } from '../services/search-history.service';
import { Subject, combineLatest, of } from 'rxjs';
import { catchError, debounceTime, distinctUntilChanged, map, switchMap, tap } from 'rxjs/operators';

@Component({
  selector: 'app-search',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, FavoriteBtnComponent, DataSourceBadgeComponent, TranslatePipe],
  templateUrl: './search.component.html',
  styleUrls: ['./search.component.css'],
})
export class SearchComponent implements OnInit {
  private iconRender = inject(IconRenderService);
  private covers = inject(CoverArtService);
  private destroyRef = inject(DestroyRef);
  private search$ = new Subject<string>();

  query = signal('');
  trackResults = signal<TrackSearchResult[]>([]);
  artistResults = signal<Artista[]>([]);
  isLoading = signal(false);
  searched = signal(false);
  hasError = signal(false);
  errorMessage = signal('');

  constructor(
    private route: ActivatedRoute,
    private tracksSvc: TracksService,
    private artistsSvc: ArtistsService,
    private searchHistory: SearchHistoryService,
  ) {}

  ngOnInit() {
    this.search$.pipe(
      debounceTime(350),
      distinctUntilChanged(),
      tap((q) => {
        const term = q.trim();
        if (!term) {
          this.trackResults.set([]);
          this.artistResults.set([]);
          this.searched.set(false);
          this.hasError.set(false);
          this.errorMessage.set('');
          this.isLoading.set(false);
        }
      }),
      switchMap((q) => {
        const term = q.trim();
        if (!term) return of(null);
        this.isLoading.set(true);
        this.searched.set(true);
        this.hasError.set(false);
        this.errorMessage.set('');
        return combineLatest([
          this.tracksSvc.searchTracks(term, 100).pipe(
            map((d) => ({ ok: true as const, items: d ?? [] })),
            catchError(() => of({ ok: false as const, items: [] as TrackSearchResult[] })),
          ),
          this.artistsSvc.listArtists(1, 20, term).pipe(
            map((res) => ({ ok: true as const, items: res.items ?? [] })),
            catchError(() => of({ ok: false as const, items: [] as Artista[] })),
          ),
        ]).pipe(map(([tracks, artists]) => ({ term, tracks, artists })));
      }),
      takeUntilDestroyed(this.destroyRef),
    ).subscribe((result) => {
      if (!result) return;
      const { term, tracks, artists } = result;
      this.trackResults.set(tracks.items);
      this.artistResults.set(artists.items);
      this.isLoading.set(false);
      const failed = (tracks.ok ? 0 : 1) + (artists.ok ? 0 : 1);
      if (failed > 0) {
        this.hasError.set(true);
        this.errorMessage.set(
          failed === 2
            ? 'No se pudo consultar el catálogo. Verifica que el backend esté activo.'
            : 'Algunos resultados no se pudieron cargar. Intenta nuevamente.',
        );
      } else {
        this.searchHistory.add(term, tracks.items.length, artists.items.length);
      }
    });

    this.route.queryParamMap.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((pm) => {
      const q = pm.get('q') ?? '';
      this.query.set(q);
      if (q.trim()) this.search$.next(q);
    });
  }

  onInput(val: string) {
    this.query.set(val);
    this.search$.next(val);
  }

  runSearch(q: string) {
    this.query.set(q);
    this.search$.next(q);
  }

  retrySearch() {
    this.runSearch(this.query());
  }

  hasResults(): boolean {
    return this.trackResults().length > 0 || this.artistResults().length > 0;
  }

  cover(trackId: number): string {
    return this.covers.gradientFor(trackId);
  }

  icon(key: string, size = 18): SafeHtml {
    return this.iconRender.render(key, size);
  }

  artistLabel(name?: string): string {
    return primaryArtistName(name);
  }

  displayTitle(name?: string | null): string {
    return displayTrackTitle(name);
  }
}
