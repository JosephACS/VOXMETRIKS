import { SafeHtml } from '@angular/platform-browser';
import { IconRenderService } from '../../../shared/services/icon-render.service';
import { I18nService } from '../../../core/services/i18n.service';
import { Component, DestroyRef, inject, OnInit, signal, computed, viewChild } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, RouterModule } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { ScrollingModule } from '@angular/cdk/scrolling';
import { CoverArtService } from '../../../shared/services/cover-art.service';
import { TracksService } from '../services/tracks.service';
import { ArtistsService } from '../services/artists.service';
import { TrackSearchResult, Artista } from '../../../shared/models/api.models';
import { primaryArtistName } from '../../../shared/utils/artist.util';
import { TrackActionsComponent } from '../../../shared/components/track-actions/track-actions.component';
import { PlayerController } from '../../../playback-core/player.controller';
import { toPlayableFromSearch } from '../../../playback-core/adapters/track.adapter';
import { DataSourceBadgeComponent } from '../../../shared/components/data-source-badge/data-source-badge.component';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { displayTrackTitle } from '../../../shared/utils/track-display.util';
import { SearchHistoryService } from '../services/search-history.service';
import { AIService } from '../../ai/services/ai.service';
import { AiPlaylistDialogComponent } from '../../ai/components/ai-playlist-dialog.component';
import { Subject, combineLatest, of } from 'rxjs';
import { catchError, debounceTime, distinctUntilChanged, map, switchMap, tap } from 'rxjs/operators';

const TRACK_PAGE_SIZE = 20;

@Component({
  selector: 'app-search',
  standalone: true,
  imports: [
    CommonModule, FormsModule, RouterModule, ScrollingModule,
    TrackActionsComponent, DataSourceBadgeComponent, TranslatePipe,
    AiPlaylistDialogComponent,
  ],
  templateUrl: './search.component.html',
  styleUrls: ['./search.component.css'],
})
export class SearchComponent implements OnInit {
  readonly lang = inject(I18nService).lang;
  private iconRender = inject(IconRenderService);
  private covers = inject(CoverArtService);
  private readonly controller = inject(PlayerController);
  private destroyRef = inject(DestroyRef);
  private route = inject(ActivatedRoute);
  private tracksSvc = inject(TracksService);
  private artistsSvc = inject(ArtistsService);
  private searchHistory = inject(SearchHistoryService);
  private aiSvc = inject(AIService);
  private search$ = new Subject<string>();

  readonly aiDialog = viewChild(AiPlaylistDialogComponent);

  query = signal('');
  aiMode = signal(false);
  nlIntent = signal<string | null>(null);
  trackResults = signal<TrackSearchResult[]>([]);
  trackTotal = signal(0);
  trackPage = signal(1);
  artistResults = signal<Artista[]>([]);
  isLoading = signal(false);
  searched = signal(false);
  hasError = signal(false);
  errorMessage = signal('');
  readonly trackPageSize = TRACK_PAGE_SIZE;
  trackTotalPages = computed(() =>
    Math.max(1, Math.ceil(this.trackTotal() / this.trackPageSize)),
  );

  trackQueue = computed(() =>
    this.trackResults().map((r) => toPlayableFromSearch(this.covers, r)),
  );

  ngOnInit() {
    this.search$.pipe(
      debounceTime(350),
      distinctUntilChanged(),
      tap((q) => {
        const term = q.trim();
        if (!term) {
          this.trackResults.set([]);
          this.trackTotal.set(0);
          this.trackPage.set(1);
          this.artistResults.set([]);
          this.searched.set(false);
          this.hasError.set(false);
          this.errorMessage.set('');
          this.nlIntent.set(null);
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
        this.trackPage.set(1);

        if (this.aiMode() || this._looksNatural(term)) {
          return this.aiSvc.naturalSearch(term).pipe(
            map((res) => ({
              term,
              ai: true as const,
              tracks: (res.tracks ?? []).map((t) => ({
                id_track: Number(t['id_track']),
                nombre_track: String(t['nombre_track'] ?? ''),
                nombre_artista: t['nombre_artista'] as string | undefined,
                popularity: t['popularity'] as number | undefined,
              })) as TrackSearchResult[],
              total: res.total ?? 0,
              intent: String((res.intent as Record<string, unknown>)?.['label'] ?? 'ai'),
            })),
            catchError(() => of({
              term,
              ai: true as const,
              tracks: [] as TrackSearchResult[],
              total: 0,
              intent: 'error',
            })),
          );
        }

        return combineLatest([
          this.tracksSvc.searchTracks(term, 1, TRACK_PAGE_SIZE).pipe(
            map((res) => ({ ok: true as const, items: res.items ?? [], total: res.total ?? 0 })),
            catchError(() => of({ ok: false as const, items: [] as TrackSearchResult[], total: 0 })),
          ),
          this.artistsSvc.listArtists(1, 20, term).pipe(
            map((res) => ({ ok: true as const, items: res.items ?? [] })),
            catchError(() => of({ ok: false as const, items: [] as Artista[] })),
          ),
        ]).pipe(map(([tracks, artists]) => ({ term, ai: false as const, tracks, artists })));
      }),
      takeUntilDestroyed(this.destroyRef),
    ).subscribe((result) => {
      if (!result) return;
      if ('ai' in result && result.ai) {
        this.trackResults.set(result.tracks);
        this.trackTotal.set(result.total);
        this.artistResults.set([]);
        this.nlIntent.set(result.intent);
        this.isLoading.set(false);
        if (!result.tracks.length) {
          this.hasError.set(true);
          this.errorMessage.set('No encontramos resultados para esa intención. Prueba otra descripción.');
        }
        return;
      }
      const { term, tracks, artists } = result;
      this.trackResults.set(tracks.items);
      this.trackTotal.set(tracks.total);
      this.artistResults.set(artists.items);
      this.nlIntent.set(null);
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
        this.searchHistory.add(term, tracks.total, artists.items.length);
      }
    });

    this.route.queryParamMap.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((pm) => {
      const q = pm.get('q') ?? '';
      this.query.set(q);
      if (q.trim()) this.search$.next(q);
    });
  }

  private _looksNatural(term: string): boolean {
    const hints = ['para ', 'música', 'musica', 'canciones', 'tranquil', 'energ', 'estudiar', 'entrenar', 'triste', 'parecido'];
    const lower = term.toLowerCase();
    return hints.some((h) => lower.includes(h)) && term.split(/\s+/).length >= 3;
  }

  toggleAiMode(): void {
    this.aiMode.update((v) => !v);
    if (this.query().trim()) this.search$.next(this.query());
  }

  openAiPlaylist(): void {
    this.aiDialog()?.show();
  }

  onInput(val: string) {
    this.query.set(val);
    this.search$.next(val);
  }

  runSearch(q: string) {
    this.query.set(q);
    this.search$.next(q);
  }

  loadTrackPage(page: number) {
    const term = this.query().trim();
    if (!term || page < 1 || page > this.trackTotalPages()) return;
    this.isLoading.set(true);
    this.tracksSvc.searchTracks(term, page, TRACK_PAGE_SIZE).subscribe({
      next: (res) => {
        this.trackResults.set(res.items ?? []);
        this.trackTotal.set(res.total ?? 0);
        this.trackPage.set(page);
        this.isLoading.set(false);
      },
      error: () => this.isLoading.set(false),
    });
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

  trackId = (_: number, r: TrackSearchResult) => r.id_track;

  playable(r: TrackSearchResult) {
    return toPlayableFromSearch(this.covers, r);
  }

  playTrack(r: TrackSearchResult, e?: Event) {
    e?.preventDefault();
    e?.stopPropagation();
    const track = this.playable(r);
    this.controller.playTrack(track, this.trackQueue());
  }
}
