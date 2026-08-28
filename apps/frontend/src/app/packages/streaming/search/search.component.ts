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
import { TrackCoverService } from '../../../shared/services/track-cover.service';
import { TracksService } from '../services/tracks.service';
import { ArtistsService, ExternalArtistResult } from '../services/artists.service';
import { TrackSearchResult, Artista } from '../../../shared/models/api.models';
import { primaryArtistName } from '../../../shared/utils/artist.util';
import { TrackActionsComponent } from '../../../shared/components/track-actions/track-actions.component';
import { PlayerController } from '../../../playback-core/player.controller';
import { toPlayableFromSearch } from '../../../playback-core/adapters/track.adapter';
import { TranslatePipe } from '../../../shared/pipes/translate.pipe';
import { displayTrackTitle } from '../../../shared/utils/track-display.util';
import { SearchHistoryService } from '../services/search-history.service';
import { AIService } from '../../ai/services/ai.service';
import { AiPlaylistDialogComponent } from '../../ai/components/ai-playlist-dialog.component';
import { Observable, Subject, combineLatest, of } from 'rxjs';
import { catchError, debounceTime, distinctUntilChanged, map, switchMap, tap } from 'rxjs/operators';

const TRACK_PAGE_SIZE = 20;

type SearchPhase =
  | 'idle'
  | 'local'
  | 'local_empty'
  | 'external_loading'
  | 'external'
  | 'external_empty'
  | 'external_unavailable'
  | 'external_error'
  | 'ai';

@Component({
  selector: 'app-search',
  standalone: true,
  imports: [
    CommonModule, FormsModule, RouterModule, ScrollingModule,
    TrackActionsComponent, TranslatePipe,
    AiPlaylistDialogComponent,
  ],
  templateUrl: './search.component.html',
  styleUrls: ['./search.component.css'],
})
export class SearchComponent implements OnInit {
  readonly lang = inject(I18nService).lang;
  private iconRender = inject(IconRenderService);
  private covers = inject(CoverArtService);
  private trackCover = inject(TrackCoverService);
  private readonly controller = inject(PlayerController);
  private destroyRef = inject(DestroyRef);
  private route = inject(ActivatedRoute);
  private tracksSvc = inject(TracksService);
  private artistsSvc = inject(ArtistsService);
  private searchHistory = inject(SearchHistoryService);
  private aiSvc = inject(AIService);
  private search$ = new Subject<{ q: string; allowExternal: boolean }>();

  readonly aiDialog = viewChild(AiPlaylistDialogComponent);

  query = signal('');
  aiMode = signal(false);
  nlIntent = signal<string | null>(null);
  trackResults = signal<TrackSearchResult[]>([]);
  trackTotal = signal(0);
  trackPage = signal(1);
  artistResults = signal<Artista[]>([]);
  externalArtistResults = signal<ExternalArtistResult[]>([]);
  phase = signal<SearchPhase>('idle');
  statusMessage = signal('');
  isLoading = signal(false);
  searched = signal(false);
  hasError = signal(false);
  errorMessage = signal('');
  readonly trackPageSize = TRACK_PAGE_SIZE;
  trackTotalPages = computed(() =>
    Math.max(1, Math.ceil(this.trackTotal() / this.trackPageSize)),
  );

  /** Example queries that only fill/run the existing search pipeline (no fake results). */
  readonly searchExamples = ['Bad Bunny', 'rock', 'pop'] as const;

  uiState = computed(():
    | 'initial'
    | 'searching'
    | 'empty'
    | 'provider_unavailable'
    | 'error'
    | 'results' => {
    if (!this.searched() && !this.isLoading()) return 'initial';
    if (this.isLoading() && !this.hasResults()) return 'searching';
    if (this.phase() === 'external_unavailable') return 'provider_unavailable';
    if (this.hasError() && !this.hasResults()) return 'error';
    if (this.searched() && !this.hasResults() && !this.isLoading()) return 'empty';
    return 'results';
  });

  trackQueue = computed(() =>
    this.trackResults().map((r) => toPlayableFromSearch(this.covers, r)),
  );

  ngOnInit() {
    this.search$.pipe(
      debounceTime(350),
      distinctUntilChanged((a, b) => a.q === b.q && a.allowExternal === b.allowExternal),
      tap(({ q }) => {
        const term = q.trim();
        if (!term) {
          this._resetResults();
        }
      }),
      switchMap(({ q, allowExternal }) => {
        const term = q.trim();
        if (!term) return of(null);
        this.isLoading.set(true);
        this.searched.set(true);
        this.hasError.set(false);
        this.errorMessage.set('');
        this.trackPage.set(1);
        this.statusMessage.set('Buscando en VOXMETRIKS…');
        this.phase.set('local');

        if (this.aiMode()) {
          return this.aiSvc.naturalSearch(term).pipe(
            map((res) => ({
              term,
              kind: 'ai' as const,
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
              kind: 'ai' as const,
              tracks: [] as TrackSearchResult[],
              total: 0,
              intent: 'error',
            })),
          );
        }

        return combineLatest([
          this.tracksSvc.musicSearch(term, 1, TRACK_PAGE_SIZE, false).pipe(
            map((res) => ({ ok: true as const, res })),
            catchError(() => of({
              ok: false as const,
              res: null,
            })),
          ),
          this.artistsSvc.listArtists(1, 20, term).pipe(
            map((res) => ({ ok: true as const, items: res.items ?? [] })),
            catchError(() => of({ ok: false as const, items: [] as Artista[] })),
          ),
        ]).pipe(
          map(([music, artists]) => ({
            term,
            kind: 'music' as const,
            allowExternal,
            music,
            artists,
          })),
        );
      }),
      takeUntilDestroyed(this.destroyRef),
    ).subscribe((result) => {
      if (!result) return;

      if (result.kind === 'ai') {
        this.trackResults.set(result.tracks);
        this.trackTotal.set(result.total);
        this.artistResults.set([]);
        this.externalArtistResults.set([]);
        this.nlIntent.set(result.intent);
        this.phase.set('ai');
        this.statusMessage.set('');
        this.isLoading.set(false);
        if (!result.tracks.length) {
          this.hasError.set(true);
          this.errorMessage.set('No encontramos resultados para esa intención. Prueba otra descripción.');
        }
        return;
      }

      const { term, music, artists } = result;
      this.nlIntent.set(null);
      this.artistResults.set(artists.items);
      this.externalArtistResults.set([]);
      if (!artists.items.length) {
        const externalSearch = (this.artistsSvc as ArtistsService & {
          searchExternal?: (name: string, limit?: number) => Observable<ExternalArtistResult[]>;
        }).searchExternal;
        externalSearch?.call(this.artistsSvc, term, 6).subscribe((items) => this.externalArtistResults.set(items));
      }

      if (!music.ok || !music.res) {
        this.isLoading.set(false);
        this.hasError.set(true);
        this.errorMessage.set('No se pudo consultar el catálogo. Verifica que el backend esté activo.');
        this.phase.set('external_error');
        return;
      }

      const res = music.res;
      this.trackResults.set(res.local?.items ?? []);
      this.trackTotal.set(res.local?.total ?? 0);
      // Playback sources are resolved by Spotify → Deezer; external video
      // search results are intentionally not surfaced in the product UI.
      this.statusMessage.set(res.message || '');
      this.phase.set((res.phase as SearchPhase) || 'local');
      this.isLoading.set(false);

      if (!artists.ok) {
        this.hasError.set(true);
        this.errorMessage.set('Algunos resultados no se pudieron cargar. Intenta nuevamente.');
      } else {
        this.searchHistory.add(term, res.local?.total ?? 0, artists.items.length);
      }
    });

    this.route.queryParamMap.pipe(takeUntilDestroyed(this.destroyRef)).subscribe((pm) => {
      const q = pm.get('q') ?? '';
      this.query.set(q);
      if (q.trim()) this.search$.next({ q, allowExternal: false });
    });
  }

  private _resetResults(): void {
    this.trackResults.set([]);
    this.trackTotal.set(0);
    this.trackPage.set(1);
    this.artistResults.set([]);
    this.externalArtistResults.set([]);
    this.searched.set(false);
    this.hasError.set(false);
    this.errorMessage.set('');
    this.nlIntent.set(null);
    this.statusMessage.set('');
    this.phase.set('idle');
    this.isLoading.set(false);
  }

  private _looksNatural(term: string): boolean {
    const hints = ['para ', 'música', 'musica', 'canciones', 'tranquil', 'energ', 'estudiar', 'entrenar', 'triste', 'parecido'];
    const lower = term.toLowerCase();
    return hints.some((h) => lower.includes(h)) && term.split(/\s+/).length >= 3;
  }

  toggleAiMode(): void {
    this.aiMode.update((v) => !v);
    if (this.query().trim()) this.search$.next({ q: this.query(), allowExternal: false });
  }

  openAiPlaylist(): void {
    this.aiDialog()?.show();
  }

  onInput(val: string) {
    this.query.set(val);
    this.search$.next({ q: val, allowExternal: false });
  }

  onSearchKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter') {
      e.preventDefault();
      this.runSearch(this.query(), true);
    }
  }

  runSearch(q: string, allowExternal = true) {
    this.query.set(q);
    this.search$.next({ q, allowExternal });
  }

  /** Fills the input and executes the same search path as the toolbar submit. */
  applyExample(q: string): void {
    this.runSearch(q, true);
  }

  loadTrackPage(page: number) {
    const term = this.query().trim();
    if (!term || page < 1 || page > this.trackTotalPages()) return;
    this.isLoading.set(true);
    this.tracksSvc.musicSearch(term, page, TRACK_PAGE_SIZE, false).subscribe({
      next: (res) => {
        this.trackResults.set(res.local?.items ?? []);
        this.trackTotal.set(res.local?.total ?? 0);
        this.trackPage.set(page);
        this.isLoading.set(false);
      },
      error: () => this.isLoading.set(false),
    });
  }

  retrySearch() {
    this.runSearch(this.query(), true);
  }

  hasResults(): boolean {
    return (
      this.trackResults().length > 0 ||
      this.artistResults().length > 0 ||
      this.externalArtistResults().length > 0
    );
  }

  cover(trackId: number): string {
    return this.covers.gradientFor(trackId);
  }

  /** Catalog artwork resolved from the app's cover service. */
  coverUrl$(trackId: number): Observable<string | null> {
    return this.trackCover.cover$(trackId);
  }

  artistCoverUrl$(artistId: number): Observable<string | null> {
    return this.trackCover.artistCover$(artistId);
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

  formatDuration(sec?: number): string {
    if (sec == null || !Number.isFinite(sec) || sec <= 0) return '—';
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
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
